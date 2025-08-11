from django.contrib import admin
from django.utils.html import format_html, mark_safe
import nested_admin
from .models import Category, Product, ProductColor, ProductImage, ProductReview, Order, OrderItem, Profile

admin.site.register(Category)

# --- NESTED INLINES FOR PRODUCT ---
class ProductImageNestedInline(nested_admin.NestedTabularInline):
    model = ProductImage
    extra = 1
    readonly_fields = ['thumbnail']

    def thumbnail(self, instance):
        if instance.image:
            return format_html('<img src="{}" width="64" style="margin:1px; border-radius:8px;" />', instance.image.url)
        return ""
    thumbnail.short_description = "Thumbnail"

class ProductColorNestedInline(nested_admin.NestedStackedInline):
    model = ProductColor
    extra = 1
    inlines = [ProductImageNestedInline]  # Only here!
    readonly_fields = ['all_images_for_color']

    def all_images_for_color(self, instance):
        if not instance.pk:  # Inline not yet saved
            return ""
        images = instance.images.all()
        if not images:
            return "No images"
        html = ""
        for img in images:
            if img.image:
                html += f'<img src="{img.image.url}" width="64" style="margin:1px; border-radius:8px;" />'
        return mark_safe(html)
    all_images_for_color.short_description = 'Images'

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
    list_display = ('name', 'category')

# --- PLAIN ADMIN FOR COLOR/IMAGE (NO INLINES) ---
@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    list_display = ['color', 'product']

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['color', 'image']

admin.site.register(ProductReview)
admin.site.register(Profile)

# --- ORDER/ORDERITEM ADMIN ---
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'color', 'price', 'quantity')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'total', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'shipping_address', 'phone')
    inlines = [OrderItemInline]


# --- UNREGISTER UNNEEDED MODELS (if desired) ---
try:
    admin.site.unregister(ProductImage)
except admin.sites.NotRegistered:
    pass
try:
    admin.site.unregister(ProductColor)
except admin.sites.NotRegistered:
    pass
