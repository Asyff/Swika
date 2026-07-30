from django.db import models
import datetime
from django.contrib.auth.models import User
from django.db.models.signals import post_save

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length= 50)
    image = models.ImageField(upload_to='uploads/product/', blank=True,  null=True, default='uploads/product/bag1.PNG')
    
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'categories'
    
    

class Product(models.Model):
    
    name = models.CharField(max_length= 50)
    price = models.DecimalField(default=0, decimal_places=2, max_digits=7)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)
    description = models.CharField(max_length=250, default= '', blank=True, null=True)
    image = models.ImageField(upload_to='uploads/product/')
    
    is_sale = models.BooleanField(default=False)
    sale_price = models.DecimalField(default=0, decimal_places=2, max_digits=7)
    
    def __str__(self):
        return self.name

class Order(models.Model):
    # 1. FIX: Point directly to Django's built-in secure User model
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders', null=True, blank=True)
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1) # Safer field type for inventory numbers
    address = models.CharField(max_length=255, default='', blank=True) # Increased max_length for long addresses
    phone = models.CharField(max_length=20, default='', blank=True)
    
    # 2. IMPROVEMENT: Use auto_now_add=True for precise time tracking automatically
    date = models.DateTimeField(auto_now_add=True)
    
    # 3. OPTION: Instead of a simple True/False, a string choice field tracks logistics better
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Paid', 'Paid'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    
    # 4. NEW: Store the historical price of the item at the exact moment of purchase
   # Change max_value=10 to max_digits=10
    price_at_purchase = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)


    # 5. FIX: Must return a formatting string representation to avoid model object crashes
    def __str__(self):
        return f"Order #{self.id} - {self.user.username} - {self.product.name} (x{self.quantity})"

    # Handy helper property to compute line subtotals inside order loops easily
    @property
    def total_cost(self):
        return round(float(self.price_at_purchase) * self.quantity, 2)


class Profile(models.Model):
    # This securely links back to Django's built-in User (handles first_name, last_name, email, encrypted password)
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    # Custom customer fields that Django's base User model doesn't have
    phone = models.CharField(max_length=15, blank=True)
    shipping_address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=50, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} ({self.user.username})"

# This signal automatically builds a profile whenever a new secure user registers
def create_profile(sender, instance, created, **kwargs):
    if created:
        user_profile = Profile(user=instance)
        user_profile.save()