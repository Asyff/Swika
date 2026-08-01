from django.contrib import admin
from .models import *

# Register your models here.



class OrderAdmin(admin.ModelAdmin):
    # Explicitly display these specific parameters inside your administrator management panel dashboard grid
    list_display = ('id', 'user', 'product', 'quantity', 'phone', 'address', 'status', 'date')
    list_filter = ('status', 'date')
    search_fields = ('user__username', 'product__name', 'phone')
    
admin.site.register(Order,OrderAdmin)

# 1. Create an Inline Model form for the secondary images
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3  # Dynamically displays 3 blank upload field slots by default

# 2. Attach the Inline model straight into your primary Product management block
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    list_display = ('id', 'name', 'price', 'stock_quantity', 'is_sale')
    search_fields = ('name', 'category__name')

admin.site.register(Product, ProductAdmin)
admin.site.register(Category)

admin.site.register(Profile)


