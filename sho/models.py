from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal, ROUND_HALF_UP

class Category(models.Model):
    name = models.CharField(max_length=30)
    image = models.ImageField(upload_to='category_images/')

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(to=Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=30)
    price = models.DecimalField(max_digits=10, decimal_places=0)
    discount = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        price_decimal = Decimal(self.price)
        # Calculate discount amount exactly
        discount_amount = (price_decimal * Decimal(self.discount) / Decimal("100"))
        # Subtract and round to 2 decimal places using HALF_UP (bankers rounding)
        final_price = (price_decimal - discount_amount).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )
        self.price = final_price
        # super().save(*args, **kwargs)
        # self.price = self.price - ((self.price/100) * self.discount)
        return super().save(*args, **kwargs)
    
    def original_price(self):
        if self.discount:
            return (self.price / (Decimal("1") - (Decimal(self.discount) / Decimal("100")))).quantize(
                Decimal("0.01"),
                rounding=ROUND_HALF_UP,
            )
        return self.price
        # return self.price + ((self.price/100) * self.discount)


    def __str__(self):
        return self.name
    

class ProductColor(models.Model):
    product = models.ForeignKey(to=Product, related_name='colors', on_delete=models.CASCADE)
    color = models.CharField(max_length=30, blank=True, null=True)
    qty = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.name}: {self.color}"


class ProductImage(models.Model):
    color = models.ForeignKey(to=ProductColor, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='product_images/')


class ProductReview(models.Model):
    product = models.ForeignKey(to=Product, related_name='reviews', on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)
    reviewer = models.ForeignKey(to=User, related_name='reviews', on_delete=models.CASCADE)
    review = models.TextField(max_length=256)
    review_image = models.ImageField(upload_to='review_images')

    def __str__(self):
        return f"{self.product}-{self.review}-{self.reviewer}"


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(choices=(
        ("Confirmed", "Confirmed"),
        ("Pending", "Pending"),
        ("Shipped", "Shipped"),
        ("Delivered", "Delivered"),
        ("Cancelled", "Cancelled"),
        ("Returned", "Returned"),
        ("Return Requested", "Return Requested"),
        ("Processing", "Processing"),
        ("On the way", "On the way"),
    ), default="Confirmed")
    shipping_address = models.TextField(max_length=256)
    phone = models.CharField(max_length=15)
    pincode = models.PositiveIntegerField()
    deliverycharge = models.PositiveIntegerField()
    redeemed_points = models.PositiveIntegerField()

    def __str__(self):
        return f"Order {self.id} by {self.user.username} - Status: {self.status}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('Product', on_delete=models.PROTECT)
    color = models.ForeignKey('ProductColor', on_delete=models.PROTECT)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f"Order ID: {self.order.id} - {self.product.name} {self.color.color} - {self.quantity} by {self.order.user.username} at {self.order.created_at.strftime('%d-%b-%y')}"
    

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    first_order_offer_used = models.BooleanField(default=False)
    loyaltypoints = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.user.username}'s profile"



class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')

    def __str__(self):
        return f"{self.user.username}'s Wishlist"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('Product', on_delete=models.CASCADE)

    class Meta:
        unique_together = ('wishlist', 'product')  # prevent duplicates

    def __str__(self):

        return f"{self.product.name} in {self.wishlist.user.username}'s wishlist"

