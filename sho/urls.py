from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import BootstrapAuthenticationForm

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='sho/login.html', authentication_form=BootstrapAuthenticationForm), name='login'),
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('logout/', auth_views.LogoutView.as_view(template_name='sho/home.html'), name='logout'),
    path('categories/<int:pk>/', views.category_products, name='category_products'),
    path('product_detail/<int:pk>/', views.view_product_detail, name='product_detail'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<str:key>/', views.remove_from_cart, name='remove_from_cart'), 
    path('ajax/update-cart-quantity/', views.ajax_update_cart_quantity, name='ajax_update_cart_quantity'),
    path('product_detail/<int:product_id>/get-stock-quantity/<int:color_id>/',views.ajax_get_stock_quantity_of_product, name='get_stock_quantity_of_product' ),
    path('place-order/', views.place_order_and_redirect_to_razorpay, name='place_order'),
    path('razorpay-success/', views.razorpay_payment_success, name='razorpay_payment_success'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('about-us/', views.about_us, name='about_us'),
    path('faq/', views.faq, name='faq'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('product_detail/<int:product_id_duplicate>/wishlist/add/<int:product_id>/', views.ajax_add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),


]