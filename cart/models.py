from django.db import models

# Create your models here.

from django.db import models
from django.contrib.auth.models import User
from home.models import Product

class PersistentCartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='db_cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product') # One row per unique item per user

    def __str__(self):
        return f"{self.user.username} - {self.product.name} (x{self.quantity})"