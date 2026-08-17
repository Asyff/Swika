from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.exceptions import PermissionDenied
import hmac
import hashlib
import base64
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.auth import update_session_auth_hash # Crucial: stops logout on password change
from django.contrib.auth.forms import PasswordChangeForm
from .forms import UserUpdateForm, ProfileForm

# Unified App Imports
from .models import Order, Product, Profile, Category
from cart.cart import Cart
from cart.models import PersistentCartItem# Active DB cart model tracking row
from .forms import CategoryForm
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.db.models import Q
# ==================== PUBLIC PAGE VIEW CONTROLLERS ====================

def home(request):
    available_products = Product.objects.filter(stock_quantity__gt=0)
    return render(request, 'index.html', {'products': available_products})

def about(request):
    return render(request, 'about.html', {})

def blog(request):
    return render(request, 'blog.html', {})

def shop(request):
    return render(request, 'shop.html', {})

def cart(request):
    return render(request, 'cart.html', {})

def contact(request):
    return render(request, 'contact.html', {})

def product(request, pk):
    product_obj = get_object_or_404(Product, id=pk)
    
    extra_carousel_images = product_obj.images.all() 
    return render(request, 'singleproduct.html', {'product': product_obj, 'carousel_images': extra_carousel_images})

def category(request, food):
    try:
        category_obj = Category.objects.get(name__iexact=food)
        visible_products = Product.objects.filter(category=category_obj, stock_quantity__gt=0)
        return render(request, 'category.html', {
            'products': visible_products, 
            'category': category_obj
        })
    except Category.DoesNotExist:
        messages.error(request, "The requested category does not exist.")
        return redirect('home')
    
def category_summary(request):
    categories = Category.objects.all()
    return render(request, 'category_summary.html', {"categories": categories})


# ==================== ACCOUNT ROUTING PORTS ====================

def login_user(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, "Welcome back!")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('login')
    return render(request, 'login.html', {})

def logout_user(request):
    if request.method == "POST" or request.method == "GET":
        logout(request)
        messages.success(request, "You have successfully logged out.")
        return redirect('login')
    return redirect('home')

def register_user(request):
    if request.method == "POST":
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        
        if password != password2:
            messages.error(request, "The passwords do not match.")
            return redirect('register')
            
        if User.objects.filter(username=username).exists():
            messages.error(request, "The username is already taken.")
            return redirect('register')
            
        if User.objects.filter(email=email).exists():
            messages.error(request, "The email is already in use.")
            return redirect('register')
        
        user = User.objects.create_user(
            first_name=first_name,
            last_name=last_name,
            email=email,
            username=username,
            password=password
        )
        user.save()
        
        # FIX: Pass the explicit string name of your custom auth backend right here!
        auth_login(request, user, backend='home.backends.EmailOrUsernameBackend')
        
        messages.success(request, f"Account created successfully! Welcome, {first_name}.")
        return redirect('home')
    
    return render(request, 'register.html')
    
@login_required
def update_profile(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        # 1. Check if the user is submitting a Password Change Action
        if 'change_password' in request.POST:
            pass_form = PasswordChangeForm(request.user, request.POST)
            user_form = UserUpdateForm(instance=request.user)
            profile_form = ProfileForm(instance=profile)
            
            if pass_form.is_valid():
                user = pass_form.save()
                # Keeps the current browser logged in after security credential changes
                update_session_auth_hash(request, user)
                messages.success(request, "Your security password has been changed successfully!")
                return redirect('update_profile')
            else:
                messages.error(request, "Password update failed. Please check the requirements below.")

        # 2. Else user is updating standard profile detail fields
        else:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            profile_form = ProfileForm(request.POST, instance=profile)
            pass_form = PasswordChangeForm(request.user)

            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, "Your personal information has been updated successfully!")
                return redirect('update_profile')
    else:
        # Standard load instance mappings
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)
        pass_form = PasswordChangeForm(request.user)
        
    return render(request, "update_profile.html", {
        "user_form": user_form,
        "profile_form": profile_form,
        "pass_form": pass_form
    })

# ==================== CONSOLIDATED CART AND PAYMENT CONTROLLER ====================

@login_required
def checkout(request):
    cart = Cart(request)
    quantities = cart.get_quants()
    products_with_data = []
    
    inventory_error_triggered = False

    for product in cart.get_prods():
        product_id_str = str(product.id)
        if product_id_str in quantities:
            qty = quantities[product_id_str]
            
            # Inventory validation guard
            if hasattr(product, 'stock_quantity') and product.stock_quantity is not None:
                if product.stock_quantity < qty:
                    messages.error(request, f"Sorry, '{product.name}' only has {product.stock_quantity} items remaining in stock.")
                    inventory_error_triggered = True
                    continue

            price = product.sale_price if product.sale_price > 0 else product.price
            product.qty = qty
            product.total_price = round(float(price) * qty, 2)
            products_with_data.append(product)
            
    if inventory_error_triggered or not products_with_data:
        return redirect('cart_summary')

    # Prep name configurations
    user_full_name = f"{request.user.first_name} {request.user.last_name}".strip()
    if not user_full_name:
        user_full_name = request.user.username

    # Pass the form instance loop definitions
    form = ProfileForm(instance=request.user.profile)
    
    return render(request, "checkout.html", {
        "cart_products": products_with_data,
        "totals": cart.cart_total(),  # <-- CRITICAL: This fills your template's {{ totals }} tag!
        "form": form,
        "user_full_name": user_full_name,
        "user_email": request.user.email,
    })

# UNIFIED CHECKOUT ORDER WRITER CONSOLE ENGINE

def create_database_orders(request, fallback_address_gateway, checkout_phone=None, checkout_address=None, **kwargs):
    cart = Cart(request)
    quantities = cart.get_quants() 
    profile = request.user.profile

    final_address = checkout_address if checkout_address else (profile.shipping_address if profile.shipping_address else fallback_address_gateway)
    final_phone = checkout_phone if checkout_phone else (profile.phone if profile.phone else "N/A")
    order_status = kwargs.get('initial_status', 'Paid')
    uploaded_receipt = kwargs.get('receipt_file', None)
    
    # 1. EXTRACT THE TRANSACTION ID FROM KWARGS
    trace_txn_id = kwargs.get('txn_id', '') 

    purchased_items_snapshot = []
    last_saved_order_id = 1 

    for product in cart.get_prods():
        product_id_str = str(product.id)
        if product_id_str in quantities:
            qty = int(quantities[product_id_str])
            purchase_price = product.sale_price if product.sale_price > 0 else product.price
            line_cost = round(float(purchase_price) * qty, 2)
            
            # Save the new row record to your Database model layout
            new_order = Order.objects.create(
                user=request.user,
                product=product,
                quantity=qty,
                address=final_address,
                phone=final_phone,
                status=order_status,  
                price_at_purchase=purchase_price,
                payment_screenshot=uploaded_receipt,
                
                # 2. SAVE TRACE ID DIRECTLY INTO THE DATABASE ROW
                fonepay_txn_id=trace_txn_id  
            )
            
            last_saved_order_id = new_order.id 
            purchased_items_snapshot.append({
                'name': product.name, 'qty': qty, 'price': purchase_price, 'line_total': line_cost
            })
            
            if hasattr(product, 'stock_quantity'):
                product.stock_quantity = max(0, product.stock_quantity - qty)
                product.save()
            
            
    if purchased_items_snapshot:
        print("--- [TRACE] Snapshot verified! Triggering email dispatches... ---")
        send_admin_order_notification(request.user, final_phone, final_address, purchased_items_snapshot)
        
        payment_route_label = "Fonepay Screenshot Uploaded (Awaiting Verification)" if uploaded_receipt else "Cash on Delivery (COD)"
        send_customer_order_confirmation(request.user, final_phone, final_address, purchased_items_snapshot, payment_route_label, last_saved_order_id)

    # Wipe transaction cache ONLY after everything builds successfully
    request.session['session_key'] = {}
    request.session.modified = True
    PersistentCartItem.objects.filter(user=request.user).delete()
    
@login_required
def payment_success(request):
    return render(request, "payment_success.html")


@csrf_exempt
@login_required
def fonepay_success(request):
    if request.method == 'POST':
        typed_phone = request.POST.get('phone', '').strip()
        typed_address = request.POST.get('shipping_address', '').strip()
        screenshot_file = request.FILES.get('payment_screenshot', None)
        
        # 1. ADD THIS LINE: Capture the trace ID typed inside your HTML input box
        captured_txn_id = request.POST.get('fonepay_txn_id', '').strip()

        print("\n================== FONEPAY BACKEND ENTRY TRIGGERED ==================")
        print(f"Captured Transaction ID: {captured_txn_id}")
        print(f"Screenshot File Binary Discovered: {screenshot_file is not None}")
        print("====================================================================\n")

        # 2. Pass captured_txn_id into your universal order loop execution block via kwargs
        create_database_orders(
            request, 
            fallback_address_gateway="Paid via Fonepay Mobile QR Scan",
            checkout_phone=typed_phone,
            checkout_address=typed_address,
            receipt_file=screenshot_file, 
            txn_id=captured_txn_id,       # <-- ADD THIS ARGUMENT
            initial_status='Pending'      
        )
        
        return JsonResponse({'status': 'verified'})
        
@csrf_exempt
@login_required
def cod_success(request):
    """
    Explicit doorstep processing endpoint layout view.
    """
    if request.method == 'POST':
        typed_phone = request.POST.get('phone', '').strip()
        typed_address = request.POST.get('shipping_address', '').strip()

        print("\n==================== COD BACKEND ENTRY TRIGGERED ====================")
        print(f"Captured Telephone Input: {typed_phone}")
        print(f"Captured Target Address: {typed_address}")
        print("====================================================================\n")

        create_database_orders(
            request, 
            fallback_address_gateway="Pay on Delivery (COD)",
            checkout_phone=typed_phone,
            checkout_address=typed_address,
            initial_status='Pending' 
        )
        return JsonResponse({'status': 'verified'})
        
    return JsonResponse({'error': 'Method Not Allowed'}, status=405)


# ==================== ADMINISTRATIVE FULFILLMENT INTERFACE ====================

def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@user_passes_test(is_admin_user, login_url='login')
def admin_order_dashboard(request):
    orders = Order.objects.all().order_by('-date')
    
    # SEARCH FILTER ENGINE LINK
    search_query = request.GET.get('search_query', '').strip()
    if search_query:
        # Searches across user model fields, products names, phone inputs, or fonepay transaction tracking strings
        orders = orders.filter(
            Q(user__username__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(fonepay_txn_id__icontains=search_query) |
            Q(product__name__icontains=search_query)
        )
    
    metrics = {
        'total': Order.objects.count(), # Baseline totals calculated from root table to preserve metrics accuracy
        'pending': Order.objects.filter(status='Pending').count(),
        'paid': Order.objects.filter(status='Paid').count(),
        'shipped': Order.objects.filter(status='Shipped').count(),
        'delivered': Order.objects.filter(status='Delivered').count(),
    }
    
    return render(request, "admin_order_dashboard.html", {
        "orders": orders,
        "metrics": metrics,
        "search_query": search_query # Return query to keep text locked in input box layout during filtering
    })


@user_passes_test(is_admin_user, login_url='login')
def update_order_status(request, order_id):
    if request.method == 'POST':
        order_obj = get_object_or_404(Order, id=order_id)
        new_status = request.POST.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order_obj.status = new_status
            order_obj.save()
            messages.success(request, f"Order #{order_obj.id} updated to {new_status}!")
    return redirect('admin_order_dashboard')


@login_required
def print_invoice(request, order_id):
    order_obj = get_object_or_404(Order, id=order_id)
    if order_obj.user != request.user and not (request.user.is_staff or request.user.is_superuser):
        raise PermissionDenied
    return render(request, "print_invoice.html", {"order": order_obj})


@login_required
def order_history(request):
    user_orders = Order.objects.filter(user=request.user).order_by('-date')
    return render(request, "order_history.html", {"orders": user_orders})


# Reuse our previously built administrative checkpoint logic gate
def is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@user_passes_test(is_admin_user, login_url='login')
def manage_categories(request):
    categories = Category.objects.all()
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "New category created successfully!")
            return redirect('manage_categories')
    else:
        form = CategoryForm()
            
    return render(request, "admin_manage_categories.html", {
        "categories": categories,
        "form": form
    })

@user_passes_test(is_admin_user, login_url='login')
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category_name = category.name
    category.delete()
    messages.success(request, f"Category '{category_name}' removed successfully.")
    return redirect('manage_categories')

def send_admin_order_notification(user, checkout_phone, checkout_address, order_items):
    # --- ADD THIS LOG RUN ON ENTRY ---
    print("--- [TRACE] Entering send_admin_order_notification view trigger now... ---")
    
    admin_recipient = "swikahandmade@gmail.com"
    subject = f"🚨 ALERT: New Order Received - Swika Estore"
    
    items_breakdown_text = ""
    grand_total = 0
    for item in order_items:
        items_breakdown_text += f"- {item['name']} (Quantity: x{item['qty']}) @ Rs.{item['price']} each\n"
        grand_total += item['line_total']

    email_body = f"Customer Account: {user.username}\nItems:\n{items_breakdown_text}\nTotal: Rs.{grand_total}"

    try:
        # Force a print log right before the django email wrapper method triggers
        print(f"--- [TRACE] Attempting to dispatch email to admin recipient: {admin_recipient} ---")
        
        send_mail(
            subject=subject,
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_recipient],
            fail_silently=False, # Set to False to catch system crashes
        )
        print("--- [TRACE] Admin email sent loop completed successfully! ---")
    except Exception as e:
        print(f"!!! [CRITICAL] Admin mail failed execution block error: {e} !!!")


def send_customer_order_confirmation(user, checkout_phone, checkout_address, order_items, payment_route, order_id):
    # --- ADD THIS LOG RUN ON ENTRY ---
    print(f"--- [TRACE] Entering send_customer_order_confirmation for order #{order_id}... ---")
    
    if not user.email:
        print("--- [TRACE] Skipping customer email: User profile contains an empty email field ---")
        return
        
    subject = f"🛍️ Order Confirmed! #ORD-00{order_id} - Swika Estore"
    grand_total = sum(item['line_total'] for item in order_items)
    
    context = {
        'user': user, 'phone': checkout_phone, 'address': checkout_address,
        'order_items': order_items, 'grand_total': grand_total,
        'payment_route': payment_route, 'order_id': order_id
    }
    
    try:
        html_content = render_to_string('order_confirmation.html', context)
        text_content = strip_tags(html_content)
        
        print(f"--- [TRACE] Compiling message bodies. Destination target mail: {user.email} ---")
        
        msg = EmailMultiAlternatives(
            subject=subject, body=text_content, from_email=settings.DEFAULT_FROM_EMAIL, to=[user.email]
        )
        msg.attach_alternative(html_content, "text/html")
        
        # Set to False to catch token conversion issues
        msg.send(fail_silently=False) 
        print("--- [TRACE] Customer invoice sent loop completed successfully! ---")
    except Exception as e:
        print(f"!!! [CRITICAL] Customer invoice failed execution block error: {e} !!!")