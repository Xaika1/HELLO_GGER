from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase

from .models import MAX_QUANTITY, CartItem, Order, Product


class ShopTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('anna', 'anna@kitty.ru', '123456')
        self.product = Product.objects.create(name='Кружка', price=690)
        self.client.force_login(self.user)

    def test_add_to_cart(self):
        self.client.post(f'/cart/add/{self.product.pk}/')
        self.client.post(f'/cart/add/{self.product.pk}/')
        self.assertEqual(self.user.cart.get().quantity, 2)

    def test_quantity_is_limited(self):
        self.client.post(f'/cart/add/{self.product.pk}/')
        item = self.user.cart.get()
        self.client.post(f'/cart/update/{item.pk}/', {'quantity': 10 ** 20})
        item.refresh_from_db()
        self.assertEqual(item.quantity, MAX_QUANTITY)

    def test_order_clears_cart(self):
        self.client.post(f'/cart/add/{self.product.pk}/')
        self.client.post('/cart/')
        order = Order.objects.get(user=self.user)
        self.assertEqual(order.total, 690)
        self.assertFalse(self.user.cart.exists())

    def test_stale_cart_item_redirects(self):
        response = self.client.post('/cart/update/999/', {'quantity': 2})
        self.assertRedirects(response, '/cart/')

    def test_cannot_change_foreign_cart(self):
        other = User.objects.create_user('kate', 'kate@kitty.ru', '123456')
        item = CartItem.objects.create(user=other, product=self.product)
        self.client.post(f'/cart/update/{item.pk}/', {'quantity': 50})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)


class AuthTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_signup_requires_name_and_unique_email(self):
        User.objects.create_user('kate', 'kate@kitty.ru', '123456')
        response = self.client.post('/signup/', {
            'username': 'anna', 'first_name': '', 'last_name': 'Котова',
            'email': 'KATE@kitty.ru', 'password1': '123456', 'password2': '123456',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('first_name', response.context['form'].errors)
        self.assertIn('email', response.context['form'].errors)

    def test_login_is_blocked_after_five_failures(self):
        User.objects.create_user('anna', 'anna@kitty.ru', '123456')
        for _ in range(5):
            self.client.post('/login/', {'username': 'anna', 'password': 'wrong'})
        response = self.client.post('/login/', {'username': 'anna', 'password': '123456'})
        self.assertEqual(response.status_code, 200)

    def test_open_redirect_is_ignored(self):
        User.objects.create_user('anna', 'anna@kitty.ru', '123456')
        response = self.client.post('/login/?next=https://evil.com', {'username': 'anna', 'password': '123456'})
        self.assertRedirects(response, '/', fetch_redirect_response=False)


class PanelTests(TestCase):
    def setUp(self):
        self.admin = User.objects.get(username='admin')
        self.manager = User.objects.create_user('manager', 'm@kitty.ru', '123456', is_staff=True)

    def test_regular_user_has_no_access(self):
        user = User.objects.create_user('anna', 'anna@kitty.ru', '123456')
        self.client.force_login(user)
        self.assertEqual(self.client.get('/panel/').status_code, 403)

    def test_manager_cannot_touch_superuser(self):
        self.client.force_login(self.manager)
        self.assertEqual(self.client.get(f'/panel/users/{self.admin.pk}/').status_code, 403)
        self.client.post(f'/panel/users/{self.admin.pk}/delete/')
        self.assertTrue(User.objects.filter(pk=self.admin.pk).exists())

    def test_price_must_be_positive(self):
        self.client.force_login(self.admin)
        self.client.post('/panel/products/add/', {'name': 'Брелок', 'price': '0'})
        self.assertFalse(Product.objects.filter(name='Брелок').exists())
