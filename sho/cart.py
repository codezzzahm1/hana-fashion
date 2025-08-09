
class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product, color_id, quantity):
        key = color_id
        if key in self.cart:
            self.cart[key]['quantity'] += quantity
        else:
            self.cart[key] = {
                'product_id': product.id,
                'color_id': color_id,
                'name': product.name,
                'color_name': product.colors.get(id=color_id).color,
                'price': int(product.price),  # Use discounted price if any
                'quantity': quantity,
                'image': product.colors.get(id=color_id).images.first().image.url if product.colors.get(id=color_id).images.exists() else '',
                'total': float(product.price) * quantity
            }
        self.save()

    def remove(self, key):
        if key in self.cart:
            del self.cart[key]
            self.save()

    def clear(self):
        self.session['cart'] = {}
        self.save()

    def save(self):
        self.session.modified = True

    def get_items(self):
        return self.cart.values()
    
    def update_quantity(self, key, quantity):
        if key in self.cart:
            self.cart[key]['quantity'] = max(1, quantity)  # Prevent quantity < 1
            self.cart[key]['total'] = self.cart[key]['quantity'] * self.cart[key]['price']
            self.save()
