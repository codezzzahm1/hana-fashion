
import razorpay
import math
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .forms import SignUpForm
from .models import *
from .cart import Cart



# Create your views here.

def home(request):
    categories = Category.objects.all()
    return render(request, 'sho/home.html', {"categories": categories})


def register(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data['username']
            password = form.cleaned_data['password1']
            user = authenticate(username, password)
            login(request, user)
            return redirect('home')
    else:
        form = SignUpForm()
    return render(request, 'sho/register.html', {"form": form})


def category_products(request, pk):
    category = get_object_or_404(Category, pk=pk)
    products = Product.objects.filter(category=category) 
    return render(request, 'sho/category_products.html', {
        'products': products,
        'category': category
    })


def view_product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'sho/view_product_detail.html', {
        'product': product
    })


@login_required(login_url='/login/')
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    color_id = int(request.POST.get('color_id'))
    try:
        qty = int(request.POST.get('qty'))
    except ValueError:
        qty = 1
    cart = Cart(request)
    cart.add(product, color_id, qty)
    return redirect('cart_detail')


@login_required(login_url='/login/')
def cart_detail(request):
    cart = Cart(request)
    total_sum = sum([item['total'] for k, item in cart.cart.items()])
    if not request.user.profile.first_order_offer_used:
        discount = int(total_sum * 0.05)
        total_sum -= discount
    else:
        discount = int(total_sum * 0.10)
        total_sum -= discount
    
    if has_ordered_ten_times(request.user):
        vip_user = True
    else:
        vip_user = False

    return render(request, 'sho/cart_detail.html', {'cart_items': cart.get_items(), 'total_sum': total_sum, 'discount': discount, 'vip_user': vip_user})


@login_required(login_url='/login/')
def remove_from_cart(request, key):
    cart = Cart(request)
    cart.remove(key)
    return redirect('cart_detail')


@login_required(login_url='/login/')
@require_POST
@csrf_exempt  
def ajax_update_cart_quantity(request):
    key = request.POST.get('key')
    quantity = request.POST.get('quantity')
    try:
        quantity = int(quantity)
        if quantity < 1:
            return JsonResponse({'success': False, 'error': 'Quantity must be >= 1'})
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid quantity'})

    cart = Cart(request)
    if key not in cart.cart:
        return JsonResponse({'success': False, 'error': 'Invalid cart item'})
    
    item = cart.cart[key]
    available_qty = get_object_or_404(ProductColor, id=item['color_id']).qty
  
    if quantity >= available_qty:
        quantity = available_qty
        
    cart.update_quantity(key, quantity)
    
    total_price = item['price'] * item['quantity']
    total_sum = sum([item['total'] for k, item in cart.cart.items()])

    if not request.user.profile.first_order_offer_used:
        discount = int(total_sum * 0.05)
        total_sum -= discount
    else:
        discount = int(total_sum * 0.10)
        total_sum -= discount


    return JsonResponse({
        'success': True,
        'key': key,
        'quantity': quantity,
        'total_price': "%.2f" % total_price,
        'total_sum': total_sum,
        'ajax_discount': discount,
    })


def ajax_get_stock_quantity_of_product(request, product_id, color_id):
     item = get_object_or_404(ProductColor, id=int(color_id))
     return JsonResponse({
        'success': True,
        'stock_qty': item.qty,  
    })



def has_ordered_ten_times(user: User) -> bool:
    count = Order.objects.filter(user=user, status='Confirmed').count()
    return count >= 10


@login_required(login_url='/login/')
def place_order_and_redirect_to_razorpay(request):
    if request.method != 'POST':
        return redirect('cart_detail')


    cart = Cart(request)
    items = []
    total = 0
    for key, item in cart.cart.items():
        quantity = item['quantity']
        price = item['price']
        total += item['total']
        items.append(item)

    address = request.POST.get('address')
    phone = request.POST.get('phone')
    pincode = request.POST.get('pincode')

    if not request.user.profile.first_order_offer_used:
        discount = total * (5/100)
        total -= discount
    else:
        discount = total * (10/100)
        total -= discount        

    redeem_points = int(request.POST.get('redeem_points_in_modal', '0'))
    redeem_points = min(redeem_points, request.user.profile.loyaltypoints, total)

    total -= redeem_points

    if not address or not phone:
        return redirect('cart_detail')

    deliverycharge = 60 if int(pincode) > 600000 and int(pincode) < 699999 else 90

    total += deliverycharge

    if has_ordered_ten_times(request.user):
        vip_user = True
        total -= deliverycharge
    else:
        vip_user = False
    
    
    total = math.ceil(total)
   
    # 1. Create your local pending Order
    order = Order.objects.create(
        user=request.user,
        total=total,
        shipping_address=address,
        phone=phone,
        pincode=pincode,
        deliverycharge=deliverycharge,
        status='Pending',
        redeemed_points=redeem_points
    )

    amount_paise = int(total * 100)  # Razorpay expects amounts in paise

    # 2. Create order in Razorpay
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    razorpay_order = client.order.create({
        'amount': amount_paise,
        'currency': 'INR',
        'payment_capture': 1,  # auto-capture payment
        'notes': {
            'django_order_id': str(order.id),
            'customer_email': request.user.email or '',
        }
    })

    order.razorpay_order_id = razorpay_order['id']  # Save to Order model (add this field)
    order.save()

    # 3. Render payment page with Razorpay key/order details
    return render(request, 'sho/razorpay_checkout.html', {
        'order': order,
        'razorpay_order_id': razorpay_order['id'],
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'amount': amount_paise,
        'user': request.user,
        'phone': phone,
        'address': address,
        'vip_user': vip_user
    })


@csrf_exempt
def razorpay_payment_success(request):
    import json
    from django.utils import timezone

    if request.method == 'POST':
        data = json.loads(request.body)
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')
        order_id = data.get('order_id')

        # Verify signature
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        try:
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            client.utility.verify_payment_signature(params_dict)

            order = Order.objects.get(pk=order_id, razorpay_order_id=razorpay_order_id)
            order.status = 'Confirmed'
            order.save()

            if not request.user.profile.first_order_offer_used:
                request.user.profile.first_order_offer_used = True
                request.user.profile.save()

            # Move items from Cart to OrderItem
            cart = Cart(request)
            points_earned = 0
            for key, item in cart.cart.items():
                product = Product.objects.get(id=item['product_id'])
                color = ProductColor.objects.get(id=item['color_id'])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    color=color,
                    price=item['price'],
                    quantity=item['quantity']
                )
                color.qty -= item['quantity']
                points_earned += (item['quantity'] * item['price']) * 0.01
                color.save()
            cart.clear()

            if order.redeemed_points > 0:
                request.user.profile.loyaltypoints -= order.redeemed_points 

            request.user.profile.loyaltypoints += points_earned
            request.user.profile.save()
            
            print("it is success", points_earned)
            return JsonResponse({'success': True, 'points_earned': float(points_earned)})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


@login_required(login_url='/login/')
def my_orders(request):
    # Get all orders of the logged-in user, newest first
    orders = Order.objects.filter(user=request.user).order_by('-created_at').prefetch_related('items__product', 'items__color')
    
    return render(request, 'sho/my_orders.html', {'orders': orders})


def about_us(request):
    return render(request, 'sho/about_us.html')


def faq(request):
    return render(request, 'sho/faq.html')


@login_required(login_url='/login/')
def wishlist_view(request):
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    items = wishlist.items.select_related('product').all()
    return render(request, 'sho/wishlist.html', {'wishlist_items': items})


@login_required(login_url='/login/')
def ajax_add_to_wishlist(request, product_id_duplicate, product_id):
    product = get_object_or_404(Product, pk=product_id)
    wishlist, _ = Wishlist.objects.get_or_create(user=request.user)
    WishlistItem.objects.get_or_create(wishlist=wishlist, product=product)
    return JsonResponse({ 'success': True })


@login_required(login_url='/login/')
def remove_from_wishlist(request, product_id):
    wishlist = get_object_or_404(Wishlist, user=request.user)
    WishlistItem.objects.filter(wishlist=wishlist, product_id=product_id).delete()
    return redirect('wishlist')