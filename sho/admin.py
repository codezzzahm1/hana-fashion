from django.contrib import admin
import nested_admin
from .models import (
    Category, Product, ProductColor, ProductImage, ProductReview,
    Order, OrderItem, Profile, Wishlist, WishlistItem
)

# --- CATEGORY ---
admin.site.register(Category)

# --- MINIMAL NESTED INLINES (NO CUSTOM METHODS) ---
class ProductImageNestedInline(nested_admin.NestedTabularInline):
    model = ProductImage
    extra = 0

class ProductColorNestedInline(nested_admin.NestedTabularInline):  # Changed to TabularInline
    model = ProductColor
    extra = 0
    inlines = [ProductImageNestedInline]

@admin.register(Product)
class ProductAdmin(nested_admin.NestedModelAdmin):
    inlines = [ProductColorNestedInline]
    list_display = ['name', 'category', 'price']

# --- SIMPLE ADMIN FOR OTHER MODELS ---
@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['product', 'color', 'qty']

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['color']

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'reviewer']

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'loyaltypoints']

# --- ORDER ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total', 'status']
    inlines = [OrderItemInline]

# --- WISHLIST ---
class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user']
    inlines = [WishlistItemInline]
