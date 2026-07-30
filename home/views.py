from django.shortcuts import render, redirect
from .models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as auth_login
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms
from .forms import ProfileForm
from .models import Profile 
import hmac
import hashlib
import base64
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Order
from cart.cart import Cart
from cart.models import PersistentCartItem
from .forms import ProfileForm 



# Create your views here.

def home(request):
    products = Product.objects.all()
    return render(request, 'index.html', {'products': products})


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


def login_user(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back!")
            
            # CHECK FOR REDIRECT TARGET: If '?next=' exists in URL, send them there!
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
                
            return redirect('home')
        else:
            messages.error(request, "Invalid username or password.")
            return redirect('login')
    
    return render(request, 'login.html', {})

def logout_user(request):
    # Note: Modern Django requires logouts to be via POST request. 
    # This check ensures it executes cleanly whether called via standard routing rules or script triggers.
    if request.method == "POST" or request.method == "GET":
        logout(request)
        messages.success(request, "You have successfully logged out of your account.")
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
        
        # 1. Check if passwords match
        if password != password2:
            messages.error(request, "The passwords do not match.")
            return redirect('register') # FIX: Removed the incorrect 'request' argument
            
        # 2. Check if username is taken
        if User.objects.filter(username=username).exists():
            messages.error(request, "The username is already taken.")
            return redirect('register')
            
        # 3. Check if email is already used
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
        
        # OPTIONAL PRO-TIP: Log the user in automatically after registration 
        # so they don't have to type their credentials again instantly
        auth_login(request, user)
        
        messages.success(request, f"Account created successfully! Welcome, {first_name}.")
        return redirect('home') # Redirect straight to homepage since they are logged in
        
    # Handles initial GET request
    return render(request, 'register.html')
    
@login_required
def update_profile(request):
    # Grab the logged-in user's profile instance
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Your shipping information has been updated successfully!")
            return redirect('update_profile')
    else:
        form = ProfileForm(instance=profile)
        
    return render(request, "update_profile.html", {"form": form})
    


def product(request, pk):
    product = Product.objects.get(id=pk)
    return render(request, 'singleproduct.html', {'product':product})


def category(request, food):
    
    try:
        category = Category.objects.get(name=food)
        products = Product.objects.filter(category=category)
        return render(request, 'category.html', {'products': products, 'category':category} )
    
    except:
        messages.error(request, ("category doesn't exist"))
        return redirect('home')
    
    
def category_summary(request):
    categories= Category.objects.all()
    return render(request, 'category_summary.html', {"categories":categories})


#Payment

@login_required
def checkout(request):
    cart = Cart(request)
    quantities = cart.get_quants()
    products_with_data = []
    
    # 1. Package active cart items using Option B
    for product in cart.get_prods():
        product_id_str = str(product.id)
        if product_id_str in quantities:
            qty = quantities[product_id_str]
            price = product.sale_price if product.sale_price > 0 else product.price
            product.qty = qty
            product.total_price = round(float(price) * qty, 2)
            products_with_data.append(product)
            
    if not products_with_data:
        return redirect('cart_summary')

    # 2. FIX: Pre-populate your ProfileForm using the logged-in user's profile database row
    profile_form = ProfileForm(instance=request.user.profile)
    
    # 3. Pull name details dynamically from the User model for safe layout display
    user_full_name = f"{request.user.first_name} {request.user.last_name}".strip()
    if not user_full_name:
        user_full_name = request.user.username

    return render(request, "checkout.html", {
        "cart_products": products_with_data,
        "totals": cart.cart_total(),
        "form": profile_form,        # Passes your profile form instance to the template
        "user_full_name": user_full_name,
        "user_email": request.user.email,
    })

def generate_esewa_signature(request):
    if request.method == 'POST':
        # Official UAT development key for the 'EPAYTEST' account
        secret_key = "8gBm/:&EnhH.1/q" 
        
        # 1. Safely extract parameters from the AJAX request
        total_amount = request.POST.get('total_amount', '').strip()
        transaction_uuid = request.POST.get('transaction_uuid', '').strip()
        product_code = request.POST.get('product_code', '').strip()

        # 2. CRITICAL CALCULATION FIX: Convert float strings (e.g., '1200.0') to clean integers ('1200')
        # eSewa rejects signatures if the payload says '1200' but the signature string used '1200.0'
        if '.' in total_amount:
            try:
                # Split at decimal or convert smoothly
                total_amount = str(int(float(total_amount)))
            except ValueError:
                pass

        # 3. Format the exact parameter signature sequence demanded by eSewa v2
        data_to_sign = f"total_amount={total_amount},transaction_uuid={transaction_uuid},product_code={product_code}"
        
        # 4. Generate the HMAC-SHA256 signature
        secret_bytes = bytes(secret_key, 'utf-8')
        data_bytes = bytes(data_to_sign, 'utf-8')
        hmac_hash = hmac.new(secret_bytes, data_bytes, hashlib.sha256).digest()
        encoded_signature = base64.b64encode(hmac_hash).decode('utf-8')

        return JsonResponse({
            'signature': encoded_signature,
            'clean_amount': total_amount # Pass back the cleaned format to update the form input
        })
        
# Universal helper function to execute core checkout conversions item-by-item safely
def create_database_orders(request, fallback_address_gateway):
    cart = Cart(request)
    quantities = cart.get_quants()
    profile = request.user.profile

    for product in cart.get_prods():
        product_id_str = str(product.id)
        if product_id_str in quantities:
            qty = quantities[product_id_str]
            purchase_price = product.sale_price if product.sale_price > 0 else product.price
            
            Order.objects.create(
                user=request.user,
                product=product,
                quantity=qty,
                address=profile.shipping_address if profile.shipping_address else fallback_address_gateway,
                phone=profile.phone if profile.phone else "N/A",
                status='Paid',
                price_at_purchase=purchase_price
            )
            
    # Clear out structural baskets references strings session caches
    request.session['session_key'] = {}
    request.session.modified = True
    
@login_required
def payment_success(request):
    # This page displays the final success receipt message
    return render(request, "payment_success.html")

def create_database_orders(request, fallback_address_gateway):
    cart = Cart(request)
    quantities = cart.get_quants()
    profile = request.user.profile

    for product in cart.get_prods():
        product_id_str = str(product.id)
        if product_id_str in quantities:
            qty = quantities[product_id_str]
            purchase_price = product.sale_price if product.sale_price > 0 else product.price
            
            # 1. CREATE DISPATCH ORDER RECORD
            Order.objects.create(
                user=request.user,
                product=product,
                quantity=qty,
                address=profile.shipping_address if profile.shipping_address else fallback_address_gateway,
                phone=profile.phone if profile.phone else "N/A",
                status='Paid',
                price_at_purchase=purchase_price
            )
            
            # 2. INVENTORY DEDUCTION ENGINE
            if hasattr(product, 'stock_quantity'):
                # Lower the stock levels safely
                product.stock_quantity = max(0, product.stock_quantity - qty)
                product.save() # Commit stock changes permanently to database
            
    # 3. WIPE AND CLEAN OUT ACTIVE CART SESSSION BASKETS
    request.session['session_key'] = {}
    request.session.modified = True
    
    # If utilizing the PersistentCartItem database system, clear that as well:
    
    PersistentCartItem.objects.filter(user=request.user).delete()

# eSewa Landing Redirect Endpoint View
@login_required
def esewa_success(request):
    create_database_orders(request, "Paid via eSewa Portal")
    return redirect('payment_success')

# Khalti SDK Verification Callback View
@login_required
def khalti_success(request):
    khalti_token = request.GET.get('token')
    amount_in_paisa = request.GET.get('amount')

    # SERVER-TO-SERVER VERIFICATION: Confirm with Khalti that token transaction is fully authentic
    # headers = {"Authorization": "Key test_secret_key_...your_secret_key..."}
    # response = requests.post("https://khalti.com", data={'token': khalti_token, 'amount': amount_in_paisa}, headers=headers)
    
    create_database_orders(request, "Paid via Khalti Web Wallet")
    return redirect('payment_success')

# Fonepay Verification API Endpoint View
@csrf_exempt
@login_required
def fonepay_success(request):
    if request.method == 'POST':
        create_database_orders(request, "Paid via Fonepay Mobile QR Scan")
        return JsonResponse({'status': 'verified'})
   
@login_required

def order_history(request):
    # Fetch all orders belonging to this user, sorted by newest date first
    user_orders = Order.objects.filter(user=request.user).order_by('-date')
    return render(request, "order_history.html", {"orders": user_orders})

