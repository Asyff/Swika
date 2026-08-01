# home/models.py
from django.db import models
import datetime
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver # FIX 1: Explicitly imported receiver module

# ==================== E-STORE CORE LISTING MODELS ====================

class Category(models.Model):
    name = models.CharField(max_length=50)
    image = models.ImageField(upload_to='uploads/product/', blank=True, null=True, default='uploads/product/bag1.PNG')
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'categories'


class Product(models.Model):
    name = models.CharField(max_length=50)
    price = models.DecimalField(default=0, decimal_places=2, max_digits=7)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)
    description = models.CharField(max_length=250, default='', blank=True, null=True)
    image = models.ImageField(upload_to='uploads/product/')
    stock_quantity = models.IntegerField(default=10, help_text="Available stock items count")
    
    # Active inventory/sale pricing controls
    is_sale = models.BooleanField(default=False)
    sale_price = models.DecimalField(default=0, decimal_places=2, max_digits=7)
    
    def __str__(self):
        return self.name


# ==================== TRANSACTION ORDER MODEL ====================

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    address = models.CharField(max_length=255, default='', blank=True)
    phone = models.CharField(max_length=20, default='', blank=True)
    date = models.DateTimeField(auto_now_add=True)
    
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # FIX 2: Added safety checks to prevent crashes if an order user is empty/null
    def __str__(self):
        username = self.user.username if self.user else "Anonymous/Guest"
        return f"Order #{self.id} - {username} - {self.product.name} (x{self.quantity})"

    @property
    def total_cost(self):
        return round(float(self.price_at_purchase) * self.quantity, 2)


# ==================== USER PROFILE EXTENSION LAYER ====================

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    shipping_address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=50, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    def __str__(self):
        first = self.user.first_name if self.user.first_name else ""
        last = self.user.last_name if self.user.last_name else ""
        name_string = f"{first} {last}".strip()
        return f"{name_string if name_string else self.user.username} (@{self.user.username})"


# FIX 3: Registered signal receiver link via decorator hook
@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        user_profile = Profile(user=instance)
        user_profile.save()
        
class ProductImage(models.Model):
    # Links each extra image directly to a single Product record
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='uploads/product/carousels/')

    def __str__(self):
        return f"Gallery Image for {self.product.name} (ID: #{self.id})"