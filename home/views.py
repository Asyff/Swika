from django.shortcuts import render, redirect
from .models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django import forms


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
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request,username = username, password = password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return redirect('login')
    
    else:
        
        return render(request, 'login.html', {})

def logout_user(request):
    logout(request)
    messages.success(request, ("You have been logged out."))
    return redirect('login')



def register_user(request):
   if request.method == "POST":
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        password2 = request.POST['password2']
        
        if password == password2:
            if User.objects.filter(username = username).exists():
                messages.error(request, "The username is already taken")
                return redirect('register')
        
   
            elif User.objects.filter(email = email).exists():
                messages.error(request, "The email is already used")
                return redirect('register')
            
            else:
                user=User.objects.create_user(
                    first_name = first_name,
                    last_name = last_name,
                    email = email,
                    username = username,
                    password= password
                )
                
                user.save()
                return redirect('login')
        else:
            messages.error(request, "The password doesn't match")
            return redirect(request, 'register')
   else:
        return render(request, 'register.html')
    
def update_user(request):
    if request.user.is_authenticated:
        current_user = User.objects.get(id = request.user.id)
        
        
        
    return render(request, 'update_user.html', {})
    


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
   

