from datetime import timedelta, datetime
import io
import re
import json
import os

from django.conf import settings
from django.db.models import Sum, Q
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator


from .models import (
    User, Snack, Cart, CartItem, Order, OrderItem, Payment, Feedback
)


# --------- helpers / constants --------- #

OWNER_EMAIL = getattr(settings, 'OWNER_EMAIL', 'owner@gmail.com')
OWNER_PASSWORD = getattr(settings, 'OWNER_PASSWORD', 'owner123')
FEEDBACK_MAX_LENGTH = getattr(settings, 'FEEDBACK_MAX_LENGTH', 350)

# Snack seed data: name, price, image file name (in static/images/)
SNACKS_SEED = [
    ("Vada Pav", 20, "vada-pav.jpg"),
    ("Medu Vada", 30, "medu-vada.jpg"),
    ("Sabudana Vada", 30, "sabudana-vada.jpg"),
    ("Sabudana Khichadi", 40, "sabudana-khichadi.jpg"),
    ("Samosa", 20, "samosa.jpg"),
    ("Pohe", 20, "pohe.jpg"),
    ("Sheera", 20, "sheera.jpg"),
    ("Misal Pav", 70, "misal-pav.jpg"),
    ("Bhel", 50, "bhel.jpg"),
    ("Pav Bhaji", 60, "pav-bhaji.jpg"),
    ("Kanda Bhaji", 30, "kanda-bhaji.jpg"),
    ("Alu Vadi", 40, "alu-vadi.jpg"),
    ("Batata Bhaji", 30, "batata-bhaji.jpg"),
    ("Panipuri", 20, "panipuri.jpg"),
    ("Bharli Vangi", 70, "bharli-vangi.jpg"),
    ("Puran Poli", 30, "puran-poli.jpg"),
    ("Shrikhand Puri", 80, "shrikhand-puri.jpg"),
    ("Thalipeeth", 30, "thalipeeth.jpg"),
    ("Upma", 20, "upma.jpg"),
    ("Dosa", 30, "dosa.jpg"),
    ("Idli", 30, "idli.jpg"),
    ("Uttapa", 30, "uttapa.jpg"),
    ("Chaha", 10, "chaha.jpg"),
    ("Coffee", 10, "coffee.jpg"),
]


def is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def valid_full_name(name: str) -> bool:
    if not name:
        return False
    return bool(re.fullmatch(r"[A-Za-z\s]{2,100}", name.strip()))


def valid_email(email: str) -> bool:
    if not email:
        return False
    email = email.strip()
    pattern = r"^[A-Za-z0-9._%+-]+@gmail\.com$"
    return bool(re.fullmatch(pattern, email))


def get_current_user(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    try:
        return User.objects.get(user_id=user_id)
    except User.DoesNotExist:
        return None


def get_logged_in_user(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return None


def get_or_create_cart_for_user(user):
    """
    Always return a single Cart for this user.
    If multiple carts exist (old data), merge their items into the first one
    and delete the extras.
    """
    from .models import Cart, CartItem

    carts = Cart.objects.filter(user=user).order_by('cart_id')

    if carts.exists():
        main = carts.first()
        extras = list(carts[1:])  # any extra carts (bad old data)

        if extras:
            # Move all items from extra carts to the main cart
            extra_ids = [c.pk for c in extras]
            CartItem.objects.filter(cart__in=extra_ids).update(cart=main)
            # Delete the extra carts
            Cart.objects.filter(pk__in=extra_ids).delete()

        return main

    # No cart yet -> create fresh
    return Cart.objects.create(user=user)


def get_cart_count(user):
    if not user:
        return 0
    cart = Cart.objects.filter(user=user).first()
    if not cart:
        return 0
    total = cart.items.aggregate(total=Sum('quantity'))['total'] or 0
    return int(total)


def owner_required(request):
    return request.session.get('user') == 'owner'


def seed_snacks_if_empty():
    """
    Seed some default snacks once, if DB is empty.
    Also store image file name so we can use it from DB.
    We expect all corresponding files in static/images/.
    """
    if Snack.objects.exists():
        return

    for name, price, image_file in SNACKS_SEED:
        Snack.objects.create(
            snack_name=name,
            price=price,
            available_quantity=100,
            image=image_file,   # just "vada-pav.jpg", etc.
        )


# -------------- user views -------------- #

def home(request):
    """Home page, snack grid; default landing."""
    seed_snacks_if_empty()
    user = get_current_user(request)
    snacks = Snack.objects.order_by('snack_id')
    cart_count = get_cart_count(user)

    return render(
        request,
        'home.html',
        {
            'user': user,
            'snacks': snacks,
            'cart_count': cart_count,
        }
    )


def register(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        mobile = request.POST.get('mobile', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not valid_full_name(name):
            messages.error(request, "Name must contain only letters and spaces (2–100 characters).")
            return redirect('register')

        if not mobile.isdigit() or len(mobile) != 10:
            messages.error(request, "Mobile number must be exactly 10 digits.")
            return redirect('register')

        if not valid_email(email):
            messages.error(request, "Please enter a valid Gmail address.")
            return redirect('register')

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect('register')

        existing = User.objects.filter(Q(email=email) | Q(mobile=mobile)).first()
        if existing:
            if existing.email == email:
                messages.warning(request, "This email is already registered.")
            else:
                messages.warning(request, "This mobile number is already registered.")
            return redirect('register')

        User.objects.create(
            user_name=name,
            email=email,
            mobile=mobile,
            password=password
        )
        messages.success(request, "Registration successful. Please log in.")
        return redirect('login')
    
    return render(request, 'register.html')


def login_view(request):
    if request.method == 'POST':
        identifier = request.POST.get('identifier', '').strip()
        password = request.POST.get('password', '')

        # Owner login from same page
        if identifier == OWNER_EMAIL and password == OWNER_PASSWORD:
            request.session['user'] = 'owner'
            request.session.pop('user_id', None)
            return redirect('owner_dashboard')

        # Normal customer login
        user = User.objects.filter(
            Q(email=identifier) | Q(mobile=identifier),
            password=password
        ).first()

        if user:
            request.session['user_id'] = user.user_id
            request.session['user'] = user.user_name
            return redirect('home')

        messages.error(request, "Invalid email/mobile or password.")

    return render(request, 'login.html')


def logout_view(request):
    request.session.flush()
    messages.info(request, "Logged out successfully.")
    return redirect('login')


def profile(request):
    user = get_current_user(request)
    if not user:
        messages.warning(request, "Please log in to view profile.")
        return redirect('login')
    return render(request, 'profile.html', {'user': user})


@require_POST
def delete_profile(request):
    """
    Delete the currently logged-in user's account, but keep all orders/payments.
    Carts are removed, orders remain with user=NULL.
    """
    # don't allow owner account deletion through this
    if request.session.get('user') == 'owner':
        messages.error(request, "Owner account cannot be deleted from here.")
        return redirect('profile')

    user = get_current_user(request)
    if not user:
        messages.warning(request, "Please log in first.")
        return redirect('login')

    # Delete user's cart (cart + cart items) – safe to remove
    from .models import Cart
    Cart.objects.filter(user=user).delete()

    # Orders are NOT deleted because Order.user uses SET_NULL now

    # Delete the user account
    user.delete()

    # Clear session
    request.session.flush()
    messages.success(request, "Your account has been deleted. Your previous orders and payments history are still stored for records.")
    return redirect('register')


def orders(request):
    user = get_current_user(request)
    if not user:
        messages.warning(request, "Please log in to view orders.")
        return redirect('login')

    orders_qs = user.orders.order_by('-order_time')
    return render(
        request,
        'orders.html',
        {
            'user': user,
            'orders': orders_qs,
            'cart_count': get_cart_count(user),
        }
    )


def cart_view(request):
    user = get_logged_in_user(request)
    if not user or request.session.get('user') == 'owner':
        messages.warning(request, "Please log in as customer to view cart.")
        return redirect('login')

    cart = get_or_create_cart_for_user(user)
    cart_items = CartItem.objects.filter(cart=cart).select_related('snack')

    items = []
    total = 0
    for ci in cart_items:
        snack = ci.snack
        price = snack.price if snack else 0
        qty = ci.quantity or 0
        subtotal = price * qty
        total += subtotal
        items.append({
            'id': ci.pk,
            'snack_name': snack.snack_name if snack else 'Item',
            'price': price,
            'qty': qty,
            'subtotal': subtotal,
        })

    cart_count = cart_items.aggregate(total_qty=Sum('quantity'))['total_qty'] or 0

    context = {
        'items': items,
        'total': total,
        'cart_count': cart_count,
    }
    return render(request, 'cart.html', context)


@require_POST
def add_to_cart(request):
    # Block not-logged-in or owner from this user action
    if not request.session.get('user_id') or request.session.get('user') == 'owner':
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'login required'})
        return redirect('login')

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        data = request.POST

    snack_id = data.get('snack_id')
    quantity = data.get('quantity', 1)

    try:
        quantity = int(quantity)
    except (TypeError, ValueError):
        quantity = 1

    if quantity < 1:
        quantity = 1

    user_id = request.session['user_id']
    user = User.objects.get(pk=user_id)
    snack = get_object_or_404(Snack, pk=snack_id)

    # 🔑 USE HELPER HERE (handles duplicates)
    cart = get_or_create_cart_for_user(user)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        snack=snack,
        defaults={'quantity': 0}
    )

    cart_item.quantity = (cart_item.quantity or 0) + quantity
    cart_item.save()

    cart_count = CartItem.objects.filter(cart=cart).aggregate(
        total=Sum('quantity')
    )['total'] or 0

    return JsonResponse({
        'success': True,
        'cart_count': int(cart_count)
    })


@require_POST
def update_cart_item(request):
    user = get_logged_in_user(request)
    if not user or request.session.get('user') == 'owner':
        return redirect('login')

    cart = get_or_create_cart_for_user(user)

    cart_item_id = request.POST.get('cart_item_id')
    action = request.POST.get('action')

    if not cart_item_id or not action:
        return redirect('cart')

    try:
        cart_item = CartItem.objects.select_related('snack', 'cart').get(
            pk=int(cart_item_id),
            cart=cart
        )
    except (ValueError, CartItem.DoesNotExist):
        return redirect('cart')

    snack = cart_item.snack
    available = snack.available_quantity if snack and snack.available_quantity is not None else 0

    if action == 'increase':
        new_qty = (cart_item.quantity or 0) + 1
        # if available is 0, treat as infinite
        if available == 0 or new_qty <= available:
            cart_item.quantity = new_qty
            cart_item.save()

    elif action == 'decrease':
        new_qty = (cart_item.quantity or 0) - 1
        if new_qty <= 0:
            cart_item.delete()
        else:
            cart_item.quantity = new_qty
            cart_item.save()

    elif action == 'remove':
        cart_item.delete()

    return redirect('cart')


def checkout(request):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    cart = get_or_create_cart_for_user(user)
    items = cart.items.select_related('snack')
    if not items.exists():
        return redirect('cart')

    total = 0
    details = []
    for it in items:
        snack = it.snack
        if not snack:
            continue
        price = snack.price or 0
        qty = it.quantity or 0
        subtotal = price * qty
        total += subtotal
        details.append({
            'cart_item_id': it.cart_item_id,
            'snack_id': snack.snack_id,
            'snack_name': snack.snack_name,
            'price': price,
            'qty': qty,
            'subtotal': subtotal,
            'available': snack.available_quantity or 0,
        })

    return render(
        request,
        'checkout.html',
        {
            'user': user,
            'items': details,
            'total': total,
            'cart_count': get_cart_count(user),
        }
    )


def view_order(request, order_id):
    order = get_object_or_404(Order, order_id=order_id)
    items = order.items.select_related('snack')
    return render(
        request,
        'view_order.html',
        {
            'order': order,
            'items': items,
        }
    )


def payment(request, method):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    if method not in ('cash', 'cashless'):
        return redirect('checkout')

    cart = get_or_create_cart_for_user(user)
    items = cart.items.select_related('snack')
    if not items.exists():
        return redirect('cart')

    total = 0
    details = []
    for it in items:
        snack = it.snack
        price = snack.price or 0 if snack else 0
        qty = it.quantity or 0
        subtotal = price * qty
        total += subtotal
        details.append({
            'snack_name': snack.snack_name if snack else 'Item',
            'qty': qty,
            'price': price,
            'subtotal': subtotal,
        })

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'cancel':
            return redirect('cart')
        if action == 'done':
            return redirect('feedback')  # method passed via hidden field in form

    return render(
        request,
        'payment.html',
        {
            'user': user,
            'method': method,
            'items': details,
            'total': total,
            'cart_count': get_cart_count(user),
        }
    )


def feedback(request):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    method = request.GET.get('method') or request.POST.get('method') or 'cash'

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'skip':
            return redirect('confirm_payment', method=method)

        try:
            rating = int(request.POST.get('rating') or 0)
        except (TypeError, ValueError):
            rating = 0

        content = (request.POST.get('feedback_content') or '').strip()
        if len(content) > FEEDBACK_MAX_LENGTH:
            content = content[:FEEDBACK_MAX_LENGTH]

        Feedback.objects.create(
            user=user,
            rating=rating or None,
            feedback_content=content,
            feedback_time=timezone.now(),
        )
        return redirect('confirm_payment', method=method)

    return render(
        request,
        'feedback.html',
        {
            'user': user,
            'method': method,
            'cart_count': get_cart_count(user),
        }
    )


def confirm_payment(request, method):
    user = get_current_user(request)
    if not user:
        return redirect('login')

    if method not in ('cash', 'cashless'):
        return redirect('checkout')

    cart = get_or_create_cart_for_user(user)
    items = cart.items.select_related('snack')
    if not items.exists():
        return redirect('cart')

    total = 0
    insufficient = []

    for it in items:
        snack = it.snack
        if not snack:
            insufficient.append(f"Item {it.cart_item_id} not found.")
            continue

        available = snack.available_quantity or 0
        if available < (it.quantity or 0):
            insufficient.append(f"Only {available} left for {snack.snack_name}.")
        total += (snack.price or 0) * (it.quantity or 0)

    if insufficient:
        messages.warning(request, "Some items are out of stock, please update your cart.")
        return redirect('cart')

    status = 'Paid' if method == 'cashless' else 'Pending'
    order = Order.objects.create(
        user=user,
        order_time=timezone.now(),
        status=status,
        price=int(total),
    )

    for it in items:
        if not it.snack:
            continue
        OrderItem.objects.create(
            order=order,
            snack=it.snack,
            quantity=it.quantity or 0
        )
        if it.snack.available_quantity is not None:
            new_qty = max(0, (it.snack.available_quantity or 0) - (it.quantity or 0))
            it.snack.available_quantity = new_qty
            it.snack.save(update_fields=['available_quantity'])

    Payment.objects.create(
        order=order,
        mode='Cash' if method == 'cash' else 'Cashless',
        payment_time=timezone.now(),
        status='Pending',
    )

    items.delete()
    return redirect('orders')


def live_orders(request):
    """
    Live status page: user sees today's orders only.
    JS will poll API so no full page refresh.
    """
    user = get_current_user(request)
    if not user:
        messages.warning(request, "Please log in to see your live orders.")
        return redirect('login')

    today = timezone.localdate()  # today's date in server timezone

    orders_qs = (
        user.orders
        .filter(order_time__date=today)  
        .order_by('-order_time')    
    )

    return render(
        request,
        'live_orders.html',
        {
            'user': user,
            'orders': orders_qs,
            'cart_count': get_cart_count(user),
        }
    )


# ---------- AJAX / JSON API ---------- #

def api_cart_count(request):
    user = get_current_user(request)
    return JsonResponse({'cart_count': get_cart_count(user)})


def api_order_status(request, order_id):
    user = get_current_user(request)
    if not user:
        return JsonResponse({'error': 'login required'}, status=401)

    order = get_object_or_404(Order, pk=order_id, user=user)
    payment = order.payments.order_by('-payment_time').first()
    return JsonResponse({
        'order_id': order.order_id,
        'status': order.status,
        'price': order.price,
        'order_time': order.order_time.isoformat(),
        'payment_status': payment.status if payment else None,
        'payment_mode': payment.mode if payment else None,
    })


def api_user_latest_orders(request):
    user = get_current_user(request)
    if not user:
        return JsonResponse({'error': 'login required'}, status=401)

    today = timezone.localdate()

    orders_qs = (
        user.orders
        .filter(order_time__date=today)    
        .order_by('-order_time')[:10]
    )

    data = []
    for o in orders_qs:
        payment = o.payments.order_by('-payment_time').first()
        data.append({
            'order_id': o.order_id,
            'status': o.status,
            'price': o.price,
            'order_time': o.order_time.isoformat(),
            'payment_status': payment.status if payment else None,
            'payment_mode': payment.mode if payment else None,
        })
    return JsonResponse({'orders': data})


# -------------- owner views -------------- #

def owner_dashboard(request):
    if not owner_required(request):
        return redirect('login')

    # Today (local date)
    today = timezone.localdate()

    total_users = User.objects.count()

    # ✅ only completed orders for today
    total_orders = Order.objects.filter(
        status='Completed',
        order_time__date=today
    ).count()

    # ✅ only completed payments for today
    total_payments = Payment.objects.filter(
        status='Completed',
        payment_time__date=today
    ).count()

    total_snacks = Snack.objects.count()

    # ✅ recent orders for today only
    recent_orders = Order.objects.filter(
        order_time__date=today
    ).order_by('-order_time')[:6]

    return render(
        request,
        'owner/dashboard.html',
        {
            'total_users': total_users,
            'total_orders': total_orders,
            'total_payments': total_payments,
            'total_snacks': total_snacks,
            'recent_orders': recent_orders,
            'today': today,
        }
    )


def owner_customers(request):
    if not owner_required(request):
        return redirect('login')

    # Owner CAN ONLY VIEW – no POST actions here

    q_name = request.GET.get('q_name', '').strip()
    q_email = request.GET.get('q_email', '').strip()
    q_mobile = request.GET.get('q_mobile', '').strip()

    users_qs = User.objects.all()
    if q_name:
        users_qs = users_qs.filter(user_name__icontains=q_name)
    if q_email:
        users_qs = users_qs.filter(email__icontains=q_email)
    if q_mobile:
        users_qs = users_qs.filter(mobile__icontains=q_mobile)

    users_qs = users_qs.order_by('user_id')

    return render(
        request,
        'owner/customers.html',
        {
            'users': users_qs,
            'q_name': q_name,
            'q_email': q_email,
            'q_mobile': q_mobile,
        }
    )


def owner_feedbacks_list(request):
    if not owner_required(request):
        return redirect('login')

    feedbacks = Feedback.objects.select_related('user').order_by('-feedback_time')
    return render(
        request,
        'owner/feedbacks.html',
        {
            'feedbacks': feedbacks,
        }
    )


@require_POST
def owner_delete_feedback(request, feedback_id):
    if not owner_required(request):
        return redirect('login')
    Feedback.objects.filter(feedback_id=feedback_id).delete()
    return redirect('owner_feedbacks_list')


def owner_orders_list(request):
    if not owner_required(request):
        return redirect('login')

    today = timezone.localdate()

    q_user = request.GET.get('q_user', '').strip()
    q_status = request.GET.get('q_status', '').strip()

    # ✅ ONLY today’s orders
    orders_qs = Order.objects.filter(order_time__date=today)

    if q_user:
        orders_qs = orders_qs.filter(
            Q(user__user_name__icontains=q_user) |
            Q(user__email__icontains=q_user)
        )
    if q_status:
        orders_qs = orders_qs.filter(status=q_status)

    orders_qs = orders_qs.order_by('-order_time')

    return render(
        request,
        'owner/orders.html',
        {
            'orders': orders_qs,
            'q_user': q_user,
            'q_status': q_status,
            'today': today,
        }
    )


@require_POST
def owner_change_order_status(request, order_id):
    if not owner_required(request):
        return redirect('login')

    new_status = request.POST.get('status')
    if new_status:
        Order.objects.filter(order_id=order_id).update(status=new_status)
    return redirect('owner_orders_list')


def owner_view_order(request, order_id):
    if not owner_required(request):
        return redirect('login')

    order = get_object_or_404(Order, order_id=order_id)
    items = order.items.select_related('snack')
    return render(
        request,
        'owner/order_view.html',
        {
            'order': order,
            'items': items,
        }
    )


def owner_payments_list(request):
    if not owner_required(request):
        return redirect('login')

    today = timezone.localdate()

    q_order = request.GET.get('q_order', '').strip()
    q_mode = request.GET.get('q_mode', '').strip()
    q_status = request.GET.get('q_status', '').strip()

    # ✅ ONLY today’s payments
    payments_qs = Payment.objects.select_related('order').filter(
        payment_time__date=today
    )

    if q_order:
        try:
            order_id = int(q_order)
            payments_qs = payments_qs.filter(order__order_id=order_id)
        except ValueError:
            pass
    if q_mode:
        payments_qs = payments_qs.filter(mode__icontains=q_mode)
    if q_status:
        payments_qs = payments_qs.filter(status=q_status)

    payments_qs = payments_qs.order_by('-payment_time')

    return render(
        request,
        'owner/payments.html',
        {
            'payments': payments_qs,
            'q_order': q_order,
            'q_mode': q_mode,
            'q_status': q_status,
            'today': today,
        }
    )


@require_POST
def owner_change_payment_status(request, payment_id):
    if not owner_required(request):
        return redirect('login')

    new_status = request.POST.get('status')
    if new_status:
        Payment.objects.filter(payment_id=payment_id).update(status=new_status)
    return redirect('owner_payments_list')


def owner_inventory(request):
    if not owner_required(request):
        return redirect('login')

    snacks = Snack.objects.order_by('snack_id')
    return render(request, 'owner/inventory.html', {'snacks': snacks})


@require_POST
def owner_update_inventory(request, snack_id):
    if not owner_required(request):
        return redirect('login')

    snack = get_object_or_404(Snack, snack_id=snack_id)

    name = request.POST.get('snack_name') or snack.snack_name
    price_raw = request.POST.get('price', '').strip()
    qty_raw = request.POST.get('available_quantity', '').strip()

    snack.snack_name = name

    if price_raw:
        try:
            price_val = int(price_raw)
            if price_val < 0:
                price_val = 0
            snack.price = price_val
        except ValueError:
            pass

    if qty_raw:
        try:
            qty_val = int(qty_raw)
            if qty_val < 0:
                qty_val = 0
            snack.available_quantity = qty_val
        except ValueError:
            pass

    snack.save()
    return redirect('owner_inventory')


def owner_add_snack(request):
    if not owner_required(request):
        return redirect('login')

    if request.method == 'POST':
        name = (request.POST.get('snack_name') or '').strip()
        price_raw = request.POST.get('price', '').strip()
        qty_raw = request.POST.get('available_quantity', '').strip()
        uploaded = request.FILES.get('image')  # upload image from owner panel

        if not name:
            messages.error(request, "Snack name is required.")
            return redirect('owner_add_snack')

        try:
            price_val = int(price_raw or 0)
        except ValueError:
            price_val = 0
        if price_val < 0:
            price_val = 0

        try:
            qty_val = int(qty_raw or 0)
        except ValueError:
            qty_val = 0
        if qty_val < 0:
            qty_val = 0

        image_name = None
        if uploaded:
            images_dir = os.path.join(settings.BASE_DIR, 'static', 'images')
            os.makedirs(images_dir, exist_ok=True)
            image_name = uploaded.name
            image_path = os.path.join(images_dir, image_name)
            with open(image_path, 'wb+') as dest:
                for chunk in uploaded.chunks():
                    dest.write(chunk)

        Snack.objects.create(
            snack_name=name,
            price=price_val,
            available_quantity=qty_val,
            image=image_name,
        )
        messages.success(request, "Snack added successfully.")
        return redirect('owner_inventory')

    return render(request, 'owner/add_snack.html')


@require_POST
def owner_delete_snack(request, snack_id):
    if not owner_required(request):
        return redirect('login')

    Snack.objects.filter(snack_id=snack_id).delete()
    return redirect('owner_inventory')


def owner_reports(request):
    if not owner_required(request):
        return redirect('login')

    today = timezone.localdate()

    # ---- TODAY REVENUE: completed payments only ----
    rev_agg = Payment.objects.filter(
        status='Completed',
        payment_time__date=today
    ).aggregate(total=Sum('order__price'))
    today_revenue = int(rev_agg['total'] or 0)

    # ---- TODAY ORDERS: completed orders only ----
    today_orders_completed = Order.objects.filter(
        status='Completed',
        order_time__date=today
    ).count()

    # ----- Graph date range (default last 7 days) -----
    date_from_str = (request.GET.get('from') or '').strip()
    date_to_str = (request.GET.get('to') or '').strip()

    if date_from_str and date_to_str:
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
        except ValueError:
            date_from = today - timedelta(days=6)
        try:
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except ValueError:
            date_to = today
    else:
        # default: last 7 days including today
        date_to = today
        date_from = today - timedelta(days=6)

    if date_from > date_to:
        date_from, date_to = date_to, date_from

    labels = []
    values = []

    current = date_from
    tz = timezone.get_current_timezone()
    while current <= date_to:
        day_start = datetime.combine(current, datetime.min.time(), tzinfo=tz)
        day_end = datetime.combine(current, datetime.max.time(), tzinfo=tz)

        day_revenue = (
            Payment.objects
            .filter(status='Completed', payment_time__gte=day_start, payment_time__lte=day_end)
            .aggregate(total=Sum('order__price'))['total'] or 0
        )

        labels.append(current.strftime('%Y-%m-%d'))
        values.append(int(day_revenue))
        current += timedelta(days=1)

    # Popular snacks (all time)
    popular = (
        Snack.objects
        .filter(order_items__isnull=False)
        .annotate(total_sold=Sum('order_items__quantity'))
        .order_by('-total_sold')[:10]
    )

    return render(
        request,
        'owner/reports.html',
        {
            'today': today,
            'today_revenue': today_revenue,

            # expose under both names, so any template works
            'today_orders': today_orders_completed,
            'today_orders_count': today_orders_completed,

            'date_from': date_from.strftime('%Y-%m-%d'),
            'date_to': date_to.strftime('%Y-%m-%d'),
            'chart_labels': labels,
            'chart_values': values,
            'popular': popular,
        }
    )


def owner_reports_orders(request):
    if not owner_required(request):
        return redirect('login')

    date_from_str = request.GET.get('from', '').strip()
    date_to_str = request.GET.get('to', '').strip()
    status_filter = request.GET.get('status', '').strip()

    orders_qs = Order.objects.select_related('user').all()

    if date_from_str:
        try:
            date_from = datetime.fromisoformat(date_from_str)
            orders_qs = orders_qs.filter(order_time__gte=date_from)
        except ValueError:
            date_from = None
    else:
        date_from = None

    if date_to_str:
        try:
            # include entire day
            date_to = datetime.fromisoformat(date_to_str)
            date_to_end = datetime.combine(date_to.date(), datetime.max.time(), tzinfo=timezone.get_current_timezone())
            orders_qs = orders_qs.filter(order_time__lte=date_to_end)
        except ValueError:
            date_to = None
    else:
        date_to = None

    if status_filter:
        orders_qs = orders_qs.filter(status=status_filter)

    orders_qs = orders_qs.order_by('-order_time')

    paginator = Paginator(orders_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    today = timezone.localdate()
    today_completed = Order.objects.filter(status='Completed', order_time__date=today).count()

    return render(
        request,
        'owner/reports_orders.html',
        {
            'page_obj': page_obj,
            'status_filter': status_filter,
            'date_from': date_from_str,
            'date_to': date_to_str,
            'today': today,
            'today_completed': today_completed,
        }
    )


def owner_reports_payments(request):
    if not owner_required(request):
        return redirect('login')

    date_from_str = request.GET.get('from', '').strip()
    date_to_str = request.GET.get('to', '').strip()
    status_filter = request.GET.get('status', '').strip()
    mode_filter = request.GET.get('mode', '').strip()

    payments_qs = Payment.objects.select_related('order').all()

    if date_from_str:
        try:
            date_from = datetime.fromisoformat(date_from_str)
            payments_qs = payments_qs.filter(payment_time__gte=date_from)
        except ValueError:
            date_from = None
    else:
        date_from = None

    if date_to_str:
        try:
            date_to = datetime.fromisoformat(date_to_str)
            date_to_end = datetime.combine(date_to.date(), datetime.max.time(), tzinfo=timezone.get_current_timezone())
            payments_qs = payments_qs.filter(payment_time__lte=date_to_end)
        except ValueError:
            date_to = None
    else:
        date_to = None

    if status_filter:
        payments_qs = payments_qs.filter(status=status_filter)

    if mode_filter:
        payments_qs = payments_qs.filter(mode__icontains=mode_filter)

    payments_qs = payments_qs.order_by('-payment_time')

    paginator = Paginator(payments_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    today = timezone.localdate()
    rev_agg = Payment.objects.filter(
        status='Completed',
        payment_time__date=today
    ).aggregate(total=Sum('order__price'))
    today_revenue = int(rev_agg['total'] or 0)

    return render(
        request,
        'owner/reports_payments.html',
        {
            'page_obj': page_obj,
            'status_filter': status_filter,
            'mode_filter': mode_filter,
            'date_from': date_from_str,
            'date_to': date_to_str,
            'today': today,
            'today_revenue': today_revenue,
        }
    )
