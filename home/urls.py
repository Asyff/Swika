
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('blog/', views.blog, name='blog'),
    path('shop/', views.shop, name='shop'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.register_user, name='register'),
    path('profile/edit/', views.update_profile, name='update_profile'),
    path('product/<int:pk>', views.product, name='product'),
    path('category/<str:food>', views.category, name='category'),
    path('category_summary', views.category_summary, name='category_summary'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('orders/', views.order_history, name='order_history'),
    
    # NEW Local Nepalese Payment Endpoints
    path('generate-esewa-signature/', views.generate_esewa_signature, name='generate_esewa_signature'),
    path('esewa-success/', views.esewa_success, name='esewa_success'),
    path('khalti-success/', views.khalti_success, name='khalti_success'),
    path('fonepay-success/', views.fonepay_success, name='fonepay_success'),
    path('orders/', views.order_history, name='order_history'),
    
]