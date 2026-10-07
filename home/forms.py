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
    # Define location options specific to your store delivery zones
    CITY_CHOICES = [
        ('', '-- Select Your Location / Region --'),
        ('Inside Kathmandu Valley', 'Inside Kathmandu Valley (Kathmandu, Lalitpur, Bhaktapur)'),
        ('Outside Kathmandu Valley', 'Outside Kathmandu Valley'),
    ]
    
    # Overwrite the city property layout to render a choice selection dropdown field
    city = forms.ChoiceField(choices=CITY_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = Profile
        fields = ['phone', 'shipping_address', 'city', 'postal_code']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '98XXXXXXXX'}),
            'shipping_address': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. New Baneshwor, Ward No. 10'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 44600'}),
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
