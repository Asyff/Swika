from home.models import Product
from .models import PersistentCartItem, Product

class Cart():
    def __init__(self, request):
        self.session = request.session
        self.request = request # Save the request object reference for user check access
        
        cart = self.session.get('session_key')
        if 'session_key' not in request.session:
            cart = self.session['session_key'] = {}
            
        self.cart = cart

        # SYNC LOGIC: If user is authenticated, sync DB items into the current session structure
        if request.user.is_authenticated:
            db_items = PersistentCartItem.objects.filter(user=request.user)
            for item in db_items:
                product_id_str = str(item.product.id)
                # Keep the highest quantity if there is a conflict between session and DB
                if product_id_str in self.cart:
                    self.cart[product_id_str] = max(int(self.cart[product_id_str]), item.quantity)
                else:
                    self.cart[product_id_str] = item.quantity
            
            # Save the synced layout state back down to the session tracking storage
            self.session.modified = True
    
    def add(self, product, quantity):
        product_id = str(product.id)
        product_qty = int(quantity)
        
        if product_id in self.cart:
            self.cart[product_id] += product_qty
        else:
            self.cart[product_id] = product_qty
            
        self.session.modified = True

        # DATABASE SAVE: Mirror modifications to DB if user is logged in
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
        
    
    def __len__(self):
        return sum(self.cart.values())
    
    def get_prods(self):
        product_ids=self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)
        
        return products
    
    
    def get_quants(self):
        quantities = self.cart
        return quantities
    
    def update(self, product, quantity):
        product_id = str(product)
        product_qty = int(quantity)
        
        self.cart[product_id] = product_qty
        self.session.modified = True

        # DATABASE UPDATE
        if self.request.user.is_authenticated:
            try:
                item = PersistentCartItem.objects.get(user=self.request.user, product_id=int(product_id))
                item.quantity = product_qty
                item.save()
            except PersistentCartItem.DoesNotExist:
                pass
    
    def delete(self, product):
        product_id = str(product)
        
        if product_id in self.cart:
            del self.cart[product_id]
        self.session.modified = True
        
        # DATABASE REMOVAL
        if self.request.user.is_authenticated:
            PersistentCartItem.objects.filter(user=self.request.user, product_id=int(product_id)).delete()
        
    def cart_total(self):
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)    
        quantities = self.cart
        total = 0
        for key, value in quantities.items():
            key = int(key)
            for product in products:
                if product.id == key:
                    if product.is_sale: 
                       total = total + (product.sale_price * value)
                    else:
                        total = total + (product.price * value)
                        
        
        return total 
                    
        