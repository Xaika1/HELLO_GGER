from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .forms import RegisterForm
from .models import MAX_QUANTITY, Product, CartItem, Order, OrderItem

LOGIN_ATTEMPTS = 5
LOGIN_LOCK_SECONDS = 300

SORTS = {
    'name': 'По названию',
    'price': 'Сначала дешёвые',
    '-price': 'Сначала дорогие',
}


def safe_next(request, url, default='index'):
    if url and url_has_allowed_host_and_scheme(url, allowed_hosts={request.get_host()}):
        return url
    return default


def index(request):
    sort = request.GET.get('sort', 'name')
    if sort not in SORTS:
        sort = 'name'
    query = request.GET.get('q', '').strip()[:100]

    products = list(Product.objects.order_by(sort, 'pk'))
    if sort == 'name':
        products.sort(key=lambda p: p.name.casefold())
    if query:
        products = [p for p in products if query.casefold() in p.name.casefold()]

    return render(request, 'main/index.html', {
        'products': products,
        'sorts': SORTS,
        'sort': sort,
        'query': query,
    })


@never_cache
@login_required
def cart(request):
    items = list(request.user.cart.select_related('product'))
    total = sum(item.total for item in items)

    if request.method == 'POST' and items:
        with transaction.atomic():
            deleted, _ = CartItem.objects.filter(pk__in=[item.pk for item in items]).delete()
            if deleted != len(items):
                transaction.set_rollback(True)
                messages.error(request, 'Корзина изменилась, проверьте заказ ещё раз')
                return redirect('cart')
            order = Order.objects.create(user=request.user, total=total)
            OrderItem.objects.bulk_create([
                OrderItem(order=order, product=item.product, name=item.product.name,
                          price=item.product.price, quantity=item.quantity)
                for item in items
            ])
        messages.success(request, f'Заказ №{order.pk} оформлен')
        return redirect('profile')

    return render(request, 'main/cart.html', {'items': items, 'total': total})


@login_required
@require_POST
def cart_add(request, pk):
    product = get_object_or_404(Product, pk=pk)
    item, created = CartItem.objects.get_or_create(user=request.user, product=product)
    if not created:
        if item.quantity >= MAX_QUANTITY:
            messages.error(request, f'Больше {MAX_QUANTITY} шт. одного товара добавить нельзя')
            return redirect(safe_next(request, request.POST.get('next')))
        item.quantity += 1
        item.save()
    messages.success(request, f'«{product.name}» добавлен в корзину')
    return redirect(safe_next(request, request.POST.get('next')))


@login_required
@require_POST
def cart_update(request, pk):
    item = CartItem.objects.filter(pk=pk, user=request.user).first()
    if item is None:
        messages.error(request, 'Этого товара уже нет в корзине')
        return redirect('cart')
    try:
        quantity = int(request.POST.get('quantity', ''))
    except ValueError:
        return redirect('cart')
    if quantity <= 0:
        item.delete()
    else:
        if quantity > MAX_QUANTITY:
            messages.error(request, f'Максимум {MAX_QUANTITY} шт. одного товара')
        item.quantity = min(quantity, MAX_QUANTITY)
        item.save()
    return redirect('cart')


@login_required
@require_POST
def cart_remove(request, pk):
    CartItem.objects.filter(pk=pk, user=request.user).delete()
    return redirect('cart')


@never_cache
@login_required
def profile(request):
    return render(request, 'main/profile.html', {
        'orders': request.user.orders.prefetch_related('items').order_by('-created_at'),
    })


@require_POST
def logout_view(request):
    auth_logout(request)
    return redirect('web-login')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        username = request.POST.get('username', '')[:150]
        key = f"login:{request.META.get('REMOTE_ADDR')}:{username.lower()}"
        attempts = cache.get(key, 0)
        if attempts >= LOGIN_ATTEMPTS:
            messages.error(request, 'Слишком много попыток. Попробуйте через 5 минут')
            return render(request, 'registration/login.html')

        user = authenticate(request, username=username, password=request.POST.get('password'))
        if user is not None:
            cache.delete(key)
            auth_login(request, user)
            return redirect(safe_next(request, request.GET.get('next')))
        cache.set(key, attempts + 1, LOGIN_LOCK_SECONDS)
        messages.error(request, 'Неверный логин или пароль')
    return render(request, 'registration/login.html')


def sign_up(request):
    if request.user.is_authenticated:
        return redirect('index')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        auth_login(request, form.save())
        return redirect('index')
    return render(request, 'registration/reg.html', {'form': form})
