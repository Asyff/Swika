
from django.urls import path
from . import views

urlpatterns = [
    # ==================== PUBLIC CORE VIEWS ====================
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('blog/', views.blog, name='blog'),
    path('shop/', views.shop, name='shop'),
    path('contact/', views.contact, name='contact'),
    path('product/<int:pk>/', views.product, name='product'), # Added trailing slash for consistency
    path('category/<str:food>/', views.category, name='category'),
    path('category_summary/', views.category_summary, name='category_summary'), # FIX 1: Added missing trailing slash
    
    # ==================== VISITOR AUTHENTICATION ====================
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('profile/edit/', views.update_profile, name='update_profile'),
    
    # ==================== LOCAL NEPALESE PAYMENT UTILITIES ====================
    path('checkout/', views.checkout, name='checkout'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('orders/', views.order_history, name='order_history'), # FIX 2: Removed duplicate lower copy entry
    
    path('generate-esewa-signature/', views.generate_esewa_signature, name='generate_esewa_signature'),
    path('esewa-success/', views.esewa_success, name='esewa_success'),
    path('khalti-success/', views.khalti_success, name='khalti_success'),
    path('fonepay-success/', views.fonepay_success, name='fonepay_success'),
    path('cod-success/', views.cod_success, name='cod_success'),
    
    # ==================== ADMINISTRATIVE FULFILLMENT INTERFACE ====================
    path('store-admin/orders/', views.admin_order_dashboard, name='admin_order_dashboard'),
    path('store-admin/orders/update/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('orders/invoice/<int:order_id>/', views.print_invoice, name='print_invoice'),
    
    # OPTIONAL FIX 3: Added the missing admin categories endpoints we built earlier
    path('store-admin/categories/', views.manage_categories, name='manage_categories'),
    path('store-admin/categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
]