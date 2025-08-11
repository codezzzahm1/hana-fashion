from django.contrib import admin
from django.utils.html import format_html, mark_safe
import nested_admin
from .models import (
    Category, Product, ProductColor, ProductImage, ProductReview,
    Order, OrderItem, Profile, Wishlist, WishlistItem
)

# --- CATEGORY ADMIN ---
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name']

# --- NESTED INLINES ---
class ProductImageNestedInline(nested_admin.NestedTabularInline):
    model = ProductImage
    extra = 1

class ProductColorNestedInline(nested_admin.NestedStackedInline):
    model = ProductColor
    extra = 1
    inlines = [ProductImageNestedInline]

class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    fields = ['reviewer', 'review', 'created_at']
    readonly_fields = ['reviewer', 'review', 'created_at']
    can_delete = False
    show_change_link = False
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Product)
class ProductAdmin(nested_admin.NestedModelAdmin):
    inlines = [ProductColorNestedInline, ProductReviewInline]
    list_display = ['name', 'category', 'price', 'discount']

# --- PLAIN ADMIN FOR COLOR, IMAGE, REVIEW ---
@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['product', 'color', 'qty']

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['color']

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'reviewer', 'created_at']

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'loyaltypoints', 'first_order_offer_used']

# --- ORDER ADMIN ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'color', 'price', 'quantity']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'created_at', 'total', 'status']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'shipping_address', 'phone']
    inlines = [OrderItemInline]

# --- WISHLIST ---
class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user']
    inlines = [WishlistItemInline]
