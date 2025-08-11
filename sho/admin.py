from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.urls import reverse
from django.contrib.auth.models import Group
from django.db import models
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
    
    fieldsets = (
        ('Category Information', {
            'fields': ('name', 'image', 'image_preview')
        }),
    )
    
    def image_thumbnail(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 8px; object-fit: cover; border: 2px solid #ddd;" />',
                obj.image.url
            )
        return format_html('<div style="width: 50px; height: 50px; background: #f0f0f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 10px;">No Image</div>')
    image_thumbnail.short_description = "Image"
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 200px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.image.url
            )
        return "No image uploaded yet"
    image_preview.short_description = "Image Preview"
    
    def product_count(self, obj):
        count = obj.products.count()
        if count == 0:
            return format_html('<span style="color: #999;">0 products</span>')
        return format_html('<span style="color: #28a745; font-weight: bold;">{} product{}</span>', 
                          count, 's' if count != 1 else '')
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
                '<img src="{}" width="80" height="80" style="border-radius: 8px; object-fit: cover; border: 2px solid #ddd;" />',
                obj.image.url
            )
        return format_html('<div style="width: 80px; height: 80px; background: #f0f0f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 10px;">Preview</div>')
    image_preview.short_description = "Preview"


class ProductColorNestedInline(nested_admin.NestedStackedInline):
    model = ProductColor
    extra = 1
    inlines = [ProductImageNestedInline]
    readonly_fields = ('color_summary',)
    
    fieldsets = (
        ('Color Details', {
            'fields': (('color', 'qty'), 'color_summary'),
            'classes': ('wide',)
        }),
    )
    
    def color_summary(self, obj):
        if not obj.pk:
            return "Save to see image summary"
        
        image_count = obj.images.count()
        if image_count == 0:
            return format_html('<span style="color: #dc3545;">⚠️ No images uploaded for this color</span>')
        elif image_count < 3:
            return format_html('<span style="color: #ffc107;">📷 {} image{} (consider adding more)</span>', 
                              image_count, 's' if image_count != 1 else '')
        else:
            return format_html('<span style="color: #28a745;">✅ {} images uploaded</span>', image_count)
    color_summary.short_description = "Image Status"


class ProductReviewInline(admin.TabularInline):
    model = ProductReview
    extra = 0
    readonly_fields = ('reviewer', 'review_preview', 'created_at', 'review_image_thumb')
    fields = ('reviewer', 'review_preview', 'review_image_thumb', 'created_at')
    can_delete = True
    show_change_link = False
    
    def review_preview(self, obj):
        if obj.review:
            preview = obj.review[:100] + "..." if len(obj.review) > 100 else obj.review
            return format_html('<div style="max-width: 300px;">{}</div>', preview)
        return ""
    review_preview.short_description = "Review Text"
    
    def review_image_thumb(self, obj):
        if obj.review_image:
            return format_html(
                '<img src="{}" width="40" height="40" style="border-radius: 5px; object-fit: cover;" />',
                obj.review_image.url
            )
        return "No Image"
    review_image_thumb.short_description = "Image"

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Product)
class ProductAdmin(nested_admin.NestedModelAdmin):
    list_display = (
        'name', 'category', 'formatted_price', 'discount_badge', 
        'color_count', 'image_count', 'review_count', 'status_indicator'
    )
    list_filter = ('category', 'discount')
    search_fields = ('name', 'category__name')
    list_editable = ('category',)
    inlines = [ProductColorNestedInline, ProductReviewInline]
    readonly_fields = ('price_calculation', 'product_gallery')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category'),
            'classes': ('wide',)
        }),
        ('Pricing Information', {
            'fields': (('price', 'after_discount_price'), 'discount', 'price_calculation'),
            'description': 'Enter after_discount_price to automatically calculate discount percentage',
            'classes': ('wide',)
        }),
        ('Product Gallery', {
            'fields': ('product_gallery',),
            'classes': ('collapse', 'wide')
        })
    )
    
    def formatted_price(self, obj):
        original = obj.original_price()
        current = obj.price
        if obj.discount > 0:
            return format_html(
                '<div><span style="text-decoration: line-through; color: #999;">₹{}</span></div>'
                '<div style="color: #28a745; font-weight: bold;">₹{}</div>',
                original, current
            )
        return format_html('<div style="font-weight: bold;">₹{}</div>', current)
    formatted_price.short_description = "Price"
    
    def discount_badge(self, obj):
        if obj.discount > 0:
            return format_html(
                '<span style="background: linear-gradient(135deg, #28a745, #20c997); color: white; '
                'padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: bold; '
                'box-shadow: 0 2px 4px rgba(40,167,69,0.3);">{} % OFF</span>',
                obj.discount
            )
        return format_html(
            '<span style="background: #6c757d; color: white; padding: 4px 8px; '
            'border-radius: 12px; font-size: 11px;">No Discount</span>'
        )
    discount_badge.short_description = "Discount"
    
    def color_count(self, obj):
        count = obj.colors.count()
        if count == 0:
            return format_html('<span style="color: #dc3545;">⚠️ 0</span>')
        elif count < 2:
            return format_html('<span style="color: #ffc107;">⚠️ {}</span>', count)
        else:
            return format_html('<span style="color: #28a745;">✅ {}</span>', count)
    color_count.short_description = "Colors"
    
    def image_count(self, obj):
        count = sum(color.images.count() for color in obj.colors.all())
        if count == 0:
            return format_html('<span style="color: #dc3545;">❌ 0</span>')
        elif count < 5:
            return format_html('<span style="color: #ffc107;">⚠️ {}</span>', count)
        else:
            return format_html('<span style="color: #28a745;">✅ {}</span>', count)
    image_count.short_description = "Images"
    
    def review_count(self, obj):
        count = obj.reviews.count()
        return format_html('<span style="color: #007bff;">{}</span>', count)
    review_count.short_description = "Reviews"
    
    def status_indicator(self, obj):
        colors = obj.colors.count()
        images = sum(color.images.count() for color in obj.colors.all())
        
        if colors == 0:
            return format_html('<span style="color: #dc3545;">❌ No Colors</span>')
        elif images == 0:
            return format_html('<span style="color: #ffc107;">⚠️ No Images</span>')
        elif images < 3:
            return format_html('<span style="color: #ffc107;">⚠️ Few Images</span>')
        else:
            return format_html('<span style="color: #28a745;">✅ Ready</span>')
    status_indicator.short_description = "Status"
    
    def price_calculation(self, obj):
        if obj.discount > 0:
            original = obj.original_price()
            return format_html(
                '<div style="padding: 10px; background: #f8f9fa; border-radius: 5px; border-left: 4px solid #28a745;">'
                '<strong>Original Price:</strong> ₹{}<br>'
                '<strong>After {}% Discount:</strong> ₹{}<br>'
                '<strong>You Save:</strong> ₹{}</div>',
                original, obj.discount, obj.price, original - obj.price
            )
        return format_html(
            '<div style="padding: 10px; background: #f8f9fa; border-radius: 5px;">'
            '<strong>Current Price:</strong> ₹{}<br>'
            '<em>No discount applied</em></div>',
            obj.price
        )
    price_calculation.short_description = "Price Details"
    
    def product_gallery(self, obj):
        if not obj.pk:
            return "Save product first to see gallery"
        
        colors = obj.colors.prefetch_related('images').all()
        if not colors:
            return "No colors added yet"
        
        gallery_html = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 10px;">'
        
        for color in colors:
            images = color.images.all()
            color_name = color.color or 'Unnamed Color'
            
            gallery_html += '<div style="border: 1px solid #ddd; border-radius: 8px; padding: 10px; background: #fff;">'
            gallery_html += '<h4 style="margin: 0 0 10px 0; color: #495057; font-size: 14px;">{} ({} in stock)</h4>'.format(color_name, color.qty)
            
            if images:
                gallery_html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(60px, 1fr)); gap: 5px;">'
                for img in images[:6]:
                    if img.image:
                        gallery_html += '<img src="{}" style="width: 100%; height: 60px; object-fit: cover; border-radius: 4px; border: 1px solid #ddd;" title="Click to view full size" />'.format(img.image.url)
                if len(images) > 6:
                    gallery_html += '<div style="background: #f8f9fa; border-radius: 4px; display: flex; align-items: center; justify-content: center; font-size: 12px; color: #666;">+{} more</div>'.format(len(images) - 6)
                gallery_html += '</div>'
            else:
                gallery_html += '<div style="text-align: center; color: #999; padding: 20px; background: #f8f9fa; border-radius: 4px;">No images</div>'
            
            gallery_html += '</div>'
        
        gallery_html += '</div>'
        return mark_safe(gallery_html)
    product_gallery.short_description = "Product Gallery"


# ================================
# SEPARATE COLOR ADMIN
# ================================
@admin.register(ProductColor)
class ProductColorAdmin(nested_admin.NestedModelAdmin):
    list_display = ('product', 'color', 'qty', 'image_count', 'first_image_preview')
    list_filter = ('product__category',)
    search_fields = ('product__name', 'color')
    list_editable = ('qty', 'color')
    inlines = [ProductImageNestedInline]
    
    def image_count(self, obj):
        count = obj.images.count()
        if count == 0:
            return format_html('<span style="color: #dc3545;">No images</span>')
        elif count < 3:
            return format_html('<span style="color: #ffc107;">{} image{}</span>', 
                              count, 's' if count != 1 else '')
        else:
            return format_html('<span style="color: #28a745;">{} images</span>', count)
    image_count.short_description = "Images"
    
    def first_image_preview(self, obj):
        first_image = obj.images.first()
        if first_image and first_image.image:
            return format_html(
                '<img src="{}" width="60" height="60" style="border-radius: 8px; object-fit: cover; border: 2px solid #ddd;" />',
                first_image.image.url
            )
        return format_html('<div style="width: 60px; height: 60px; background: #f0f0f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: #999; font-size: 10px;">No Image</div>')
    first_image_preview.short_description = "Preview"


# ================================
# REVIEW ADMIN
# ================================
@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'reviewer', 'created_at', 'review_preview', 'image_status')
    list_filter = ('created_at', 'product__category')
    search_fields = ('product__name', 'reviewer__username', 'review')
    readonly_fields = ('image_preview',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Review Information', {
            'fields': ('product', 'reviewer', 'review')
        }),
        ('Review Image', {
            'fields': ('review_image', 'image_preview'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def review_preview(self, obj):
        preview = obj.review[:80] + "..." if len(obj.review) > 80 else obj.review
        return format_html('<div style="max-width: 300px;">{}</div>', preview)
    review_preview.short_description = "Review"
    
    def image_status(self, obj):
        if obj.review_image:
            return format_html(
                '<img src="{}" width="40" height="40" style="border-radius: 5px; object-fit: cover;" />',
                obj.review_image.url
            )
        return format_html('<span style="color: #999;">No Image</span>')
    image_status.short_description = "Image"
    
    def image_preview(self, obj):
        if obj.review_image:
            return format_html(
                '<img src="{}" style="max-width: 400px; max-height: 300px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />',
                obj.review_image.url
            )
        return "No image uploaded"
    image_preview.short_description = "Full Image Preview"


# ================================
# ORDER ADMIN
# ================================
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'color', 'price', 'quantity', 'subtotal', 'product_image')
    can_delete = False
    
    def subtotal(self, obj):
        return format_html('<strong>₹{}</strong>', obj.price * obj.quantity)
    subtotal.short_description = "Subtotal"
    
    def product_image(self, obj):
        if obj.color and obj.color.images.exists():
            first_image = obj.color.images.first()
            return format_html(
                '<img src="{}" width="40" height="40" style="border-radius: 4px; object-fit: cover;" />',
                first_image.image.url
            )
        return "No Image"
    product_image.short_description = "Image"


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_id_display', 'user_info', 'created_at', 'total_display', 
        'status_badge', 'items_summary', 'location_info'
    )
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__email', 'phone', 'razorpay_order_id')
    list_editable = ('status',)
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline]
    readonly_fields = ('order_summary', 'user_details')
    
    fieldsets = (
        ('Order Details', {
            'fields': ('user', 'razorpay_order_id', 'status', 'order_summary')
        }),
        ('Customer Information', {
            'fields': ('user_details',),
            'classes': ('collapse',)
        }),
        ('Delivery Information', {
            'fields': ('shipping_address', 'phone', 'pincode', 'deliverycharge')
        }),
        ('Payment & Discounts', {
            'fields': ('total', 'redeemed_points')
        })
    )
    
    def order_id_display(self, obj):
        return f"#{obj.id}"
    order_id_display.short_description = "Order ID"
    
    def user_info(self, obj):
        return format_html(
            '<div><strong>{}</strong></div><small>{}</small>',
            obj.user.get_full_name() or obj.user.username,
            obj.user.email
        )
    user_info.short_description = "Customer"
    
    def total_display(self, obj):
        return format_html('<strong>₹{}</strong>', obj.total)
    total_display.short_description = "Total"
    
    def status_badge(self, obj):
        colors = {
            'Confirmed': '#28a745', 'Pending': '#ffc107', 'Shipped': '#17a2b8',
            'Delivered': '#28a745', 'Cancelled': '#dc3545', 'Returned': '#6c757d',
            'Return Requested': '#fd7e14', 'Processing': '#007bff', 'On the way': '#20c997'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 6px 12px; '
            'border-radius: 20px; font-size: 12px; font-weight: bold; '
            'text-transform: uppercase; letter-spacing: 0.5px;">{}</span>',
            color, obj.status
        )
    status_badge.short_description = "Status"
    
    def items_summary(self, obj):
        count = obj.items.count()
        return format_html('<span style="color: #007bff;">{} item{}</span>', 
                          count, 's' if count != 1 else '')
    items_summary.short_description = "Items"
    
    def location_info(self, obj):
        return format_html('📍 {} | 📞 {}', obj.pincode, obj.phone[-4:])
    location_info.short_description = "Location"
    
    def order_summary(self, obj):
        items_total = sum(item.price * item.quantity for item in obj.items.all())
        return format_html(
            '<div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #007bff;">'
            '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">'
            '<div><strong>Items Total:</strong> ₹{}</div>'
            '<div><strong>Delivery:</strong> ₹{}</div>'
            '<div><strong>Points Used:</strong> ₹{}</div>'
            '<div><strong>Final Total:</strong> ₹{}</div>'
            '</div></div>',
            items_total, obj.deliverycharge, obj.redeemed_points, obj.total
        )
    order_summary.short_description = "Order Summary"
    
    def user_details(self, obj):
        profile = getattr(obj.user, 'profile', None)
        loyalty_points = profile.loyaltypoints if profile else 0
        return format_html(
            '<div style="background: #f8f9fa; padding: 15px; border-radius: 8px;">'
            '<div><strong>Full Name:</strong> {}</div>'
            '<div><strong>Email:</strong> {}</div>'
            '<div><strong>Usern