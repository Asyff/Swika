from django.db import models
from django.contrib.auth.models import User
from home.models import Product  # Assumes Product model lives in home app

class PersistentCartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='db_cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    date_added = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Ensures one unique row per user per product in the database
        unique_together = ('user', 'product') 

    def __str__(self):
        return f"{self.user.username} - {self.product.name} (x{self.quantity})"