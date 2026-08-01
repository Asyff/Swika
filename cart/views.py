from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .cart import Cart
from home.models import Product

def cart_summary(request):
    cart = Cart(request)
    quantities = cart.get_quants() 
    totals = cart.cart_total()
    
    products_with_data = []
    for product in cart.get_prods():
        product_id_str = str(product.id)
        
        if product_id_str in quantities:
            qty = quantities[product_id_str]
            # FIX 1: Aligned with your core billing strategy checking sale_price value
            price = product.sale_price if product.sale_price > 0 else product.price
            
            # Attach temporary custom attributes onto the object context
            product.qty = qty
            product.total_price = round(float(price) * qty, 2)
            
            products_with_data.append(product)

    return render(request, "cart_summary.html", {
        "cart_products": products_with_data,
        "totals": totals
    })
    
def cart_add(request):
    cart = Cart(request)
    if request.POST.get('action') == 'post':
        try:
            product_id = int(request.POST.get('product_id'))
            product_qty = int(request.POST.get('product_qty'))
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid product ID or quantity format.'}, status=400)

        product = get_object_or_404(Product, id=product_id)
        current_in_cart = int(cart.cart.get(str(product_id), 0))
        total_requested = current_in_cart + product_qty

        if total_requested > product.stock_quantity:
            return JsonResponse({'error': f"Cannot add. Only {product.stock_quantity} total items available."}, status=400)

        cart.add(product=product, quantity=product_qty)
        
        message_html = f'''
            <div class="alert alert-success alert-dismissible fade show text-center py-2 mb-3 mx-auto" role="alert" style="max-width:600px; font-size:14px; border-radius:6px; z-index:1050;">
                Successfully added <strong>{product.name}</strong> to your cart!
                <button type="button" class="btn btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        '''

        return JsonResponse({
            'qty': cart.__len__(),
            'message_html': message_html
        })
    return JsonResponse({'error': 'Invalid request method.'}, status=400)


def cart_delete(request):
    cart = Cart(request)
    if request.POST.get('action') == 'post':
        product_id = int(request.POST.get('product_id'))
        
        cart.delete(product=product_id)
        
        global_cart_total = cart.__len__()
        new_grand_total = cart.cart_total()

        response_data = {
            'product_id': product_id,
            'global_qty': global_cart_total,
            'grand_total': round(new_grand_total, 2)
        }
        return JsonResponse(response_data)
    return JsonResponse({'error': 'Invalid request method.'}, status=400)
    

def cart_update(request):
    cart = Cart(request)
    if request.POST.get('action') == 'post':
        try:
            product_id = int(request.POST.get('product_id'))
            product_qty = int(request.POST.get('product_qty'))
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid format.'}, status=400)
            
        product = get_object_or_404(Product, id=product_id)
        
        # FIX 2: HARD VALIDATION—Block quantity modifiers from sneaking past stock thresholds
        if product_qty > product.stock_quantity:
            return JsonResponse({
                'error': f"Only {product.stock_quantity} units available. Reverting quantity.",
                'max_stock': product.stock_quantity
            }, status=400)
            
        # Call your Cart class update method
        cart.update(product=product_id, quantity=product_qty)
       
        # Calculate fresh subtotal math details for your live AJAX script
        price = product.sale_price if product.sale_price > 0 else product.price
        item_subtotal = round(float(price) * product_qty, 2)
        new_grand_total = cart.cart_total()

        # FIX 3: Fully populated response dictionary with line subtotals and grand total data
        return JsonResponse({
            'qty': product_qty,
            'subtotal': item_subtotal,
            'global_qty': cart.__len__(),
            'grand_total': round(new_grand_total, 2)
        })
    return JsonResponse({'error': 'Invalid request method.'}, status=400)