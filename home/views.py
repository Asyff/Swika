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
def create_database_orders(request, fallback_address_gateway, checkout_phone=None, checkout_address=None, receipt_file=None, initial_status='Paid'):
    cart = Cart(request)
    quantities = cart.get_quants()
    profile = request.user.profile

    final_address = checkout_address if checkout_address else (profile.shipping_address if profile.shipping_address else fallback_address_gateway)
    final_phone = checkout_phone if checkout_phone else (profile.phone if profile.phone else "N/A")

    for product in cart.get_prods():
        product_id_str = str(product.id)
        if product_id_str in quantities:
            qty = quantities[product_id_str]
            purchase_price = product.sale_price if product.sale_price > 0 else product.price
            
            # 1. Create long-term order fulfillment row
            Order.objects.create(
                user=request.user,
                product=product,
                quantity=qty,
                address=final_address,
                phone=final_phone,
                price_at_purchase=purchase_price,
                payment_receipt=receipt_file,
                status=initial_status
            )
            
            # 2. Deduct inventory stock numbers
            if hasattr(product, 'stock_quantity'):
                product.stock_quantity = max(0, product.stock_quantity - qty)
                product.save()
            
    # 3. FIX: CLEAR PERMANENT DATABASE CART ITEMS FIRST
    # This prevents the Cart.__init__ constructor from pulling old items back on page load
    PersistentCartItem.objects.filter(user=request.user).delete()

    # 4. CLEAR ACTIVE SESSION CART
    request.session['session_key'] = {}
    request.session.modified = True
    
    
@login_required
def payment_success(request):
    return render(request, "payment_success.html")

def generate_esewa_signature(request):
    if request.method == 'POST':
        # Use the standard Sandbox Secret Key for EPAYTEST
        secret_key = "8gBm/:&EnhH" 
        
        # Ensure values are read cleanly without removing valid float/decimal places
        total_amount = request.POST.get('total_amount', '').strip()
        transaction_uuid = request.POST.get('transaction_uuid', '').strip()
        product_code = request.POST.get('product_code', '').strip()

        # Build the exact message string string as mandated by eSewa v2 rules
        data_to_sign = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
        
        # Hashing process
        secret_bytes = bytes(secret_key, 'utf-8')
        data_bytes = bytes(data_to_sign, 'utf-8')
        
        hmac_hash = hmac.new(secret_bytes, data_bytes, hashlib.sha256).digest()
        encoded_signature = base64.b64encode(hmac_hash).decode('utf-8')

        return JsonResponse({
            'signature': encoded_signature,
            'clean_amount': total_amount
        })
        
@login_required
def esewa_success(request):
    create_database_orders(request, "Paid via eSewa Portal", initial_status='Paid')
    return redirect('payment_success')

@login_required
def khalti_success(request):
    create_database_orders(request, "Paid via Khalti Web Wallet", initial_status='Paid')
    return redirect('payment_success')

@csrf_exempt
@login_required
def fonepay_success(request):
    if request.method == 'POST':
        typed_phone = request.POST.get('phone', '').strip()
        typed_address = request.POST.get('shipping_address', '').strip()
        
        # EXTRACT FILE: Pull the uploaded file from request.FILES dictionary safely
        uploaded_receipt = request.FILES.get('payment_receipt')

        create_database_orders(
            request, 
            fallback_address_gateway="Paid via Fonepay Mobile QR Scan",
            checkout_phone=typed_phone,
            checkout_address=typed_address,
            receipt_file=uploaded_receipt # Pass the image variable
        )
        return JsonResponse({'status': 'verified'})
        
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
    search_query = request.GET.get('search', '').strip()
    status_filter = request.GET.get('status_filter', '').strip()
    
    if search_query:
        from django.db.models import Q
        orders = orders.filter(
            Q(user__username__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(address__icontains=search_query) |
            Q(product__name__icontains=search_query)
        )
        
    if status_filter:
        orders = orders.filter(status=status_filter)
        
    all_orders = Order.objects.all()
    metrics = {
        'total': all_orders.count(),
        'pending': all_orders.filter(status='Pending').count(),
        'paid': all_orders.filter(status='Paid').count(),
        'shipped': all_orders.filter(status='Shipped').count(),
        'delivered': all_orders.filter(status='Delivered').count(),
    }
    return render(request, "admin_order_dashboard.html", {"orders": orders, "metrics": metrics})


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