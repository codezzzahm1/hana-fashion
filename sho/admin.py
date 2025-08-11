from django.contrib import admin
from django.utils.html import format_html
import nested_admin
from .models import (
    Category, Product, ProductColor, ProductImage, ProductReview,
    Order, OrderItem, Profile, Wishlist, WishlistItem
)

# --- CATEGORY ---
admin.site.register(Category)

# --- NESTED INLINES WITH THUMBNAILS ---
class ProductImageNestedInline(nested_admin.NestedTabularInline):
    model = ProductImage
    extra = 0
    readonly_fields = ['thumbnail']
    
    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="64" style="border-radius:5px;" />', obj.image.url)
        return ""
    thumbnail.short_description = "Preview"

class ProductColorNestedInline(nested_admin.NestedTabularInline):
    model = ProductColor
    extra = 0
    inlines = [ProductImageNestedInline]

@admin.register(Product)
class ProductAdmin(nested_admin.NestedModelAdmin):
    inlines = [ProductColorNestedInline]
    list_display = ['name', 'category', 'price', 'discount']

# --- SIMPLE ADMIN FOR OTHER MODELS ---
@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['product', 'color', 'qty']

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['color', 'image_preview']
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" style="border-radius:5px;" />', obj.image.url)
        return ""
    image_preview.short_description = "Preview"

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'reviewer', 'created_at']

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'loyaltypoints', 'first_order_offer_used']

# --- ORDER ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'total', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    inlines = [OrderItemInline]

# --- WISHLIST ---
class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user']
    inlines = [WishlistItemInline]
