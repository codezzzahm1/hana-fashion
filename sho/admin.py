from django.contrib import admin
from django.utils.html import format_html, mark_safe
from .models import Category, Product, ProductColor, ProductImage, ProductReview, Order, OrderItem, Profile


admin.site.register(Category)


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0
    readonly_fields = ['thumbnail']

    def thumbnail(self, instance):
        if instance.image:
            return format_html('<img src="{}" width="64" style="margin:1px; border-radius:8px;" />', instance.image.url)
        return ""
    thumbnail.short_description = "Thumbnail"


class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1
    show_change_link = True  # Allow going to color edit page

    readonly_fields = ['all_images_for_color']

    def all_images_for_color(self, instance):
        if not instance.pk:  # Inline not yet saved
            return ""
        images = instance.images.all()  # Access ProductImage instances
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
    show_change_link = False  # Reviews can be viewed only, not changed here

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductColorInline, ProductReviewInline]
    list_display = ('name', 'category')

# Existing registrations...
@admin.register(ProductColor)
class ProductColorAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    list_display = ['color', 'product']

@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['color', 'thumbnail']
    readonly_fields = ['thumbnail']

    def thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="80" />', obj.image.url)
        return ""
    thumbnail.short_description = "Thumbnail"

admin.site.register(ProductReview)  # optionally keep review editable separately
admin.site.register(Profile)

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0  # no extra blank rows
    readonly_fields = ('product', 'color', 'price', 'quantity')  # optional, make fields read-only if you don't want editing

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'total', 'status')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'shipping_address', 'phone')
    inlines = [OrderItemInline]