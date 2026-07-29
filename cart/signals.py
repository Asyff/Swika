from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .cart import Cart

@receiver(user_logged_in)
def sync_cart_on_login(sender, request, user, **kwargs):
    # Instantiating the cart fires our constructor logic, which instantly handles 
    # merging anonymous session items directly up into the user's permanent model records!
    cart = Cart(request)