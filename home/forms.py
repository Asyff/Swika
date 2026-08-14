from django import forms
from .models import Profile,  Category
from django import forms
from django.contrib.auth.models import User


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        }

# Updated form for custom profile metadata
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone', 'shipping_address', 'city', 'postal_code']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone Number'}),
            'shipping_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Itapukhu'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kathmandu'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Postal Code'}),
        }

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Enter category name (e.g., Bags, Shoes, Clothes)'
            }),
        }
