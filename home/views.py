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
    # If a user is already authenticated, don't show the login screen again
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == "POST":
        # 1. Cleanly pull inputs safely using .get() to prevent hard crashes
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        # 2. Authenticate the entry keys against database hash rows
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name if user.first_name else user.username}!")
            return redirect('home')
        else:
            # 3. Inform the user why validation fell flat instead of failing silently
            messages.error(request, "Invalid username or password. Please try again.")
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
   

