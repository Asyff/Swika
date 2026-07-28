from django.shortcuts import render, get_object_or_404
from .cart import Cart
from home.models import Product
from django.http import JsonResponse
from django.contrib import messages

# Create your views here.

def cart_summary(request):
    cart = Cart(request)
    quantities = cart.get_quants() # Make sure to add parentheses () to call your method
    totals = cart.cart_total()
    
    # We will attach quantities and subtotals directly onto the product objects dynamically
    products_with_data = []
    for product in cart.get_prods():
        product_id_str = str(product.id)
        
        if product_id_str in quantities:
            qty = quantities[product_id_str]
            price = product.sale_price if product.is_sale else product.price
            
            # Attach temporary custom attributes onto the object
            product.qty = qty
            product.total_price = round(float(price) * qty, 2)
            
            products_with_data.append(product)

    return render(request, "cart_summary.html", {
        "cart_products": products_with_data,
        "totals": totals
    })
def cart_add(request):
    cart= Cart(request)
    if request.POST.get('action')=='post':
        product_id = int(request.POST.get('product_id'))
        product_qty = int(request.POST.get('product_qty'))
        product = get_object_or_404(Product, id=product_id)
        
        cart.add(product=product, quantity = product_qty)
        global_cart_total = cart.__len__()
        
        # Get the specific quantity for just THIS product to update its table row
        specific_product_qty = cart.cart.get(str(product_id), 0)

        response_data = {
            'product_id': product_id,
            'qty': specific_product_qty,        # For the specific product input box
            'global_qty': global_cart_total   # For a nav bar cart counter badge (if you have one)
        }
        
        messages.success(request,("Added to Cart!"))
        return JsonResponse(response_data)


def cart_delete(request):
    cart = Cart(request)
    if request.POST.get('action') == 'post':
        product_id = int(request.POST.get('product_id'))
        
        # 1. Delete the product from the session state
        cart.delete(product=product_id)
        
        # 2. Grab the newly updated totals for the response payload
        global_cart_total = cart.__len__()
        new_grand_total = cart.cart_total()

        # 3. Pass all the information your AJAX success handler needs
        response_data = {
            'product_id': product_id,
            'global_qty': global_cart_total,
            'grand_total': round(new_grand_total, 2)
        }
        
        return JsonResponse(response_data)
    

def cart_update(request):
    cart = Cart(request)
    if request.POST.get('action') == 'post':
        product_id = int(request.POST.get('product_id'))
        product_qty = int(request.POST.get('product_qty'))
        
        # This calls your Cart class update method
        cart.update(product=product_id, quantity=product_qty)
       
        # Get the global cart badge total (sum of all items combined)
        global_cart_total = cart.__len__()

        response = JsonResponse({
            'qty': product_qty,
            'global_qty': global_cart_total
        })
        return response
    
