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
            first_name=first_name, last_name=last_name,
            email=email, username=username, password=password
        )
        user.save()
        auth_login(request, user)
        messages.success(request, f"Welcome, {first_name}!")
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
    
    for product_obj in cart.get_prods():
        product_id_str = str(product_obj.id)
        if product_id_str in quantities:
            qty = quantities[product_id_str]
            price = product_obj.sale_price if product_obj.sale_price > 0 else product_obj.price
            product_obj.qty = qty
            product_obj.total_price = round(float(price) * qty, 2)
            products_with_data.append(product_obj)
            
    if not products_with_data:
        messages.error(request, "Your cart is empty.")
        return redirect('home')

    profile_form = ProfileForm(instance=request.user.profile)
    user_full_name = f"{request.user.first_name} {request.user.last_name}".strip()
    if not user_full_name:
        user_full_name = request.user.username

    return render(request, "checkout.html", {
        "cart_products": products_with_data,
        "cart_subtotal": cart.cart_total(),
        "form": profile_form,
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

    # Dynamic status fallback logic: check if 'initial_status' was passed into kwargs, otherwise default to 'Paid'
    order_status = kwargs.get('initial_status', 'Paid')

    purchased_items_snapshot = []

    for product in cart.get_prods():
        product_id_str = str(product.id)
        if product_id_str in quantities:
            qty = quantities[product_id_str]
            purchase_price = product.sale_price if product.sale_price > 0 else product.price
            line_cost = round(float(purchase_price) * qty, 2)
            
            # Save the new row transaction records into your Database model layout
            Order.objects.create(
                user=request.user,
                product=product,
                quantity=qty,
                address=final_address,
                phone=final_phone,
                status=order_status,  # Dynamic evaluation (eSewa/Khalti -> 'Paid', COD -> 'Pending')
                price_at_purchase=purchase_price
            )
            
            purchased_items_snapshot.append({
                'name': product.name,
                'qty': qty,
                'price': purchase_price,
                'line_total': line_cost
            })
            
            # Deduct inventory stock levels
            if hasattr(product, 'stock_quantity'):
                product.stock_quantity = max(0, product.stock_quantity - qty)
                product.save()
            
    # Trigger outbound notifications straight to swikahandmade@gmail.com
    if purchased_items_snapshot:
        send_admin_order_notification(
            user=request.user,
            checkout_phone=final_phone,
            checkout_address=final_address,
            order_items=purchased_items_snapshot
        )

    # Wipe user active session cart cookies parameters configurations
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
        method_used = request.POST.get('payment_method', 'fonepay').strip()

        cart = Cart(request)
        quantities = cart.get_quants()
        profile = request.user.profile

        final_address = typed_address if typed_address else (profile.shipping_address if profile.shipping_address else "Provided on Checkout Summary")
        final_phone = typed_phone if typed_phone else (profile.phone if profile.phone else "N/A")

        # 1. PROCESS GATEWAY PARAMETERS CONDITIONALS
        if method_used == 'cod':
            txn_id = "CASH-ON-DELIVERY"
            screenshot_file = None
            fallback_label = "Cash on Delivery Route"
        else:
            txn_id = request.POST.get('fonepay_txn_id', '').strip()
            screenshot_file = request.FILES.get('payment_screenshot')
            fallback_label = "Paid via Fonepay Mobile QR Scan"

        # 2. COMMIT TRANSACTION ROW ENTRIES ITEM-BY-ITEM
        for product in cart.get_prods():
            product_id_str = str(product.id)
            if product_id_str in quantities:
                qty = quantities[product_id_str]
                purchase_price = product.sale_price if product.sale_price > 0 else product.price
                
                Order.objects.create(
                    user=request.user,
                    product=product,
                    quantity=qty,
                    address=final_address,
                    phone=final_phone,
                    status='Pending',  # Both methods stay Pending until admin clears fulfillment actions
                    price_at_purchase=purchase_price,
                    fonepay_txn_id=txn_id,
                    payment_screenshot=screenshot_file
                )
                
                # Automatic Inventory deduction block tracking sync links
                if hasattr(product, 'stock_quantity') and product.stock_quantity is not None:
                    product.stock_quantity = max(0, product.stock_quantity - qty)
                    product.save()

        # Clear session shopping baskets
        request.session['session_key'] = {}
        request.session.modified = True
        
        PersistentCartItem.objects.filter(user=request.user).delete()

        return JsonResponse({'status': 'submitted'})
        
@login_required
def cod_success(request):
    if request.method == 'POST' or request.method == 'GET':
        profile = request.user.profile
        
        # Call helper, flagging initial_status as 'Pending' since money isn't collected yet
        create_database_orders(
            request, 
            fallback_address_gateway="Cash on Delivery (COD)",
            checkout_phone=profile.phone,
            checkout_address=profile.shipping_address,
            initial_status='Pending' # Matches your model's choices tuple
        )
        
        messages.success(request, "Order placed successfully via Cash on Delivery!")
        return redirect('payment_success')


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
    """
    Compiles a comprehensive summary of successful orders and fires 
    a dispatch alert notification email straight to management fulfillment teams.
    """
    admin_recipient = "swikahandmade@gmail.com"
    
    subject = f"🚨 ALERT: New Order Received - Swika Estore"
    
    # Compile a scannable text breakdown ledger loop string for items
    items_breakdown_text = ""
    grand_total = 0
    
    for item in order_items:
        items_breakdown_text += f"- {item['name']} (Quantity: x{item['qty']}) @ Rs.{item['price']} each\n"
        grand_total += item['line_total']

    email_body = f"""
Hello Swika Handmade Team,

A new successful payment checkout has been verified on your marketplace platform. Please find the customer fulfillment parameters below:

========================================
CUSTOMER & DELIVERY DETAILS
========================================
Customer Account: {user.username}
Client Full Name: {user.first_name} {user.last_name}
Email Address: {user.email}
Contact Telephone: {checkout_phone}
Shipping Destination: {checkout_address}

========================================
PURCHASED LINE ITEMS BREAKDOWN
========================================
{items_breakdown_text}
----------------------------------------
GRAND TOTAL REMITTED: Rs.{grand_total}
========================================

Fulfillment Next Steps:
Log into your order management panel dashboard (http://localhost:8000/store-admin/orders/) to print out packing slips, generate PDF invoices, or advance the logistical status to 'Shipped'.

Best regards,
Swika Estore Automation Engine
"""

    try:
        send_mail(
            subject=subject,
            message=email_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin_recipient],
            fail_silently=False, # Set to False during staging development to catch configuration faults
        )
    except Exception as e:
        print(f"Outbound dispatch automation email system logged an exception error fault: {e}")