# cart/cart.py
from home.models import Product  # FIX 1: Explicitly import Product from your home models app
from .models import PersistentCartItem  # Import your active DB cart database tracking model row

class Cart():
    def __init__(self, request):
        self.session = request.session
        self.request = request 
        
        cart = self.session.get('session_key')
        if 'session_key' not in request.session:
            cart = self.session['session_key'] = {}
            
        self.cart = cart

        # Sync items from database to session cache for logged-in users
        if request.user.is_authenticated:
            db_items = PersistentCartItem.objects.filter(user=request.user)
            for item in db_items:
                product_id_str = str(item.product.id)
                if product_id_str in self.cart:
                    self.cart[product_id_str] = max(int(self.cart[product_id_str]), item.quantity)
                else:
                    self.cart[product_id_str] = item.quantity
            self.session.modified = True

    def add(self, product, quantity):
        product_id = str(product.id)
        product_qty = int(quantity)
        
        if product_id in self.cart:
            self.cart[product_id] += product_qty
        else:
            self.cart[product_id] = product_qty
            
        self.session.modified = True

        if self.request.user.is_authenticated:
            item, created = PersistentCartItem.objects.get_or_create(
                user=self.request.user, 
                product=product
            )
            if created:
                item.quantity = product_qty
            else:
                item.quantity += product_qty
            item.save()

    def update(self, product, quantity):
        product_id = str(product)
        product_qty = int(quantity)
        
        self.cart[product_id] = product_qty
        self.session.modified = True

        if self.request.user.is_authenticated:
            PersistentCartItem.objects.filter(
                user=self.request.user, 
                product_id=int(product_id)
            ).update(quantity=product_qty)
    
    def delete(self, product):
        product_id = str(product)
        if product_id in self.cart:
            del self.cart[product_id]
        self.session.modified = True
        
        if self.request.user.is_authenticated:
            PersistentCartItem.objects.filter(
                user=self.request.user, 
                product_id=int(product_id)
            ).delete()

    def __len__(self):
        return sum(int(val) for val in self.cart.values())

    def get_prods(self):
        product_ids = self.cart.keys()
        return Product.objects.filter(id__in=product_ids)

    def get_quants(self):
        return self.cart

    # CRITICAL FIX: The exact calculation engine required to output the 'totals' context variable
    def cart_total(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)    
        total = 0
        
        for key, value in self.cart.items():
            for product in products:
                if product.id == int(key):
                    # Check for sale price overrides natively
                    if hasattr(product, 'sale_price') and product.sale_price > 0:
                        total += (product.sale_price * int(value))
                    else:
                        total += (product.price * int(value))
        return round(float(total), 2)