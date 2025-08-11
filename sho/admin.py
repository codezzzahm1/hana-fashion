from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from django.contrib.auth.models import Group
import nested_admin
from .models import (
    Category, Product, ProductColor, ProductImage, ProductReview, 
    Order, OrderItem, Profile, Wishlist, WishlistItem
)

# Unregister unnecessary models
try:
    admin.site.unregister(Group)
except admin.sites.NotRegistered:
    pass

# Custom admin site configuration
admin.site.site_header = "The Hana Fashion Admin Panel"
admin.site.site_title = "Hana Fashion Admin"
admin.site.index_title = "Welcome to Hana Fashion Administration"


# ================================
# CATEGORY ADMIN
# ================================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'image_thumbnail', 'product_count')
    search_fields = ('name',)
    readonly_fields = ('image_preview',)
    
    def image_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 8px; object-fit: cover;" />',
                obj.image.url
            )
        return format_html('<div style="width: 50px; height: 50px; background: #f0f0f0; border-radius: 8px;"></div>')
    image_thumbnail.short_description = "Image"
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 300px; border-radius: 8px;" />',
                obj.image.url
            )
        return "No image uploaded yet"
    image_preview.short_description = "Image Preview"
    
    def product_count(self, obj):
        count = obj.products.count()
        return format_html('<span>{} products</span>', count)
    product_count.short_description = "Products"


# ================================
# NESTED PRODUCT ADMIN
# ================================
class ProductImageNestedInline(nested_admin.NestedTabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ('image_preview',)
    fields = ('image', 'image_preview')
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="80" height="80" style="border-radius: 8px; object-fit: cover;" />',
                obj.image.url
            )
        return format_html('<div style="width: 80px; height: 80px; background: #f0f0f0;"></div>')
    image_preview.short_description = "Preview"


class ProductColorNestedInline(nested_admin.NestedStackedInline):
    model = ProductColor
    extra = 1
    inlines = [ProductImageNestedInline]
    readonly_fields = ('color_summary',)
    
    def color_summary(self, obj):
        if not obj.pk:
            return "Save to see image summary"
        
        image_count = obj.images.count()
        if image_count == 0:
            return format_html('<span style="color: red;">No images uploaded</span>')
        else:
            return format_html('<span style="color: green;">{} images uploaded</span>', image_count)
    color_summary.short_description = "Image Status"


class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    readonly_fields = ('reviewer', 'review_preview', 'created_at')
    fields = ('reviewer', 'review_preview', 'created_at')
    can_delete = True
    
    def review_preview(self, obj):
        if obj.review:
            preview = obj.review[:50] + "..." if len(obj.review) > 50 else obj.review
            return preview
        return ""
    review_preview.short_description = "Review Text"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Product)
class ProductAdmin(nested_admin.NestedModelAdmin):
    list_display = ('name', 'category', 'price', 'discount', 'color_count')
    list_filter = ('category', 'discount')
    search_fields = ('name', 'category__name')
    inlines = [ProductColorNestedInline, ProductReviewInline]
    readonly_fields = ('price_calculation',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category')
        }),
        ('Pricing Information', {
            'fields': ('price', 'after_discount_price', 'discount', 'price_calculation')
        }),
    )
    
    def color_count(self, obj):
        return obj.colors.count()
    color_count.short_description = "Colors"
    
    def price_calculation(self, obj):
        if obj.discount > 0:
            original = obj.original_price()
            savings = original - obj.price
            return format_html(
                '<div>Original: Rs.{}<br>Current: Rs.{}<br>Savings: Rs.{}</div>',
                original, obj.price, savings
            )
        return format_html('<div>Current Price: Rs.{}</div>', obj.price)
    price_calculation.short_description = "Price Details"


# ================================
# COLOR ADMIN
# ================================
@admin.register(ProductColor)
class ProductColorAdmin(nested_admin.NestedModelAdmin):
    list_display = ('product', 'color', 'qty', 'image_count')
    list_filter = ('product__category',)
    search_fields = ('product__name', 'color')
    inlines = [ProductImageNestedInline]
    
    def image_count(self, obj):
        return obj.images.count()
    image_count.short_description = "Images"


# ================================
# REVIEW ADMIN
# ================================
@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'reviewer', 'created_at', 'review_short')
    list_filter = ('created_at', 'product__category')
    search_fields = ('product__name', 'reviewer__username', 'review')
    readonly_fields = ('image_preview',)
    
    def review_short(self, obj):
        return obj.review[:50] + "..." if len(obj.review) > 50 else obj.review
    review_short.short_description = "Review"
    
    def image_preview(self, obj):
        if obj.review_image:
            return format_html(
                '<img src="{}" style="max-width: 300px;" />',
                obj.review_image.url
            )
        return "No image"
    image_preview.short_description = "Image Preview"


# ================================
# ORDER ADMIN
# ================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'color', 'price', 'quantity', 'subtotal')
    can_delete = False
    
    def subtotal(self, obj):
        return obj.price * obj.quantity
    subtotal.short_description = "Subtotal"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'total', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone')
    list_editable = ('status',)
    inlines = [OrderItemInline]
    
    actions = ['mark_confirmed', 'mark_shipped', 'mark_delivered']
    
    def mark_confirmed(self, request, queryset):
        updated = queryset.update(status='Confirmed')
        self.message_user(request, f'{updated} orders marked as confirmed.')
    mark_confirmed.short_description = "Mark as Confirmed"
    
    def mark_shipped(self, request, queryset):
        updated = queryset.update(status='Shipped')
        self.message_user(request, f'{updated} orders marked as shipped.')
    mark_shipped.short_description = "Mark as Shipped"
    
    def mark_delivered(self, request, queryset):
        updated = queryset.update(status='Delivered')
        self.message_user(request, f'{updated} orders marked as delivered.')
    mark_delivered.short_description = "Mark as Delivered"


# ================================
# PROFILE ADMIN
# ================================
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'user_email', 'loyaltypoints', 'first_order_offer_used')
    search_fields = ('user__username', 'user__email')
    list_editable = ('loyaltypoints',)
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = "Email"


# ================================
# WISHLIST ADMIN
# ================================
class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'items_count')
    search_fields = ('user__username',)
    inlines = [WishlistItemInline]
    
    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = "Items"
