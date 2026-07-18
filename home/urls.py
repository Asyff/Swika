
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
    path('update_user/', views.update_user, name='update_user'),
    path('product/<int:pk>', views.product, name='product'),
    path('category/<str:food>', views.category, name='category'),
    path('category_summary', views.category_summary, name='category_summary'),
    
]