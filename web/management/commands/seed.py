from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction

from web.models import Product, Order, OrderItem

PRODUCTS = [
    ('Плюшевая Hello Kitty', 'Мягкая игрушка 30 см в розовом платье с бантиком', '1990'),
    ('Кружка Hello Kitty', 'Керамическая кружка 350 мл, можно в посудомойку', '690'),
    ('Рюкзак Hello Kitty', 'Городской рюкзак с ушками и отделением для ноутбука', '3490'),
    ('Пенал Hello Kitty', 'Пенал на молнии с двумя отделениями', '990'),
    ('Наклейки', 'Набор из 50 виниловых наклеек', '150'),
    ('Ночник Hello Kitty', 'Светильник с тёплым светом и таймером', '1500'),
    ('Брелок Hello Kitty', 'Брелок из мягкого пластика с карабином', '250'),
    ('Блокнот Hello Kitty', 'Блокнот А5 на 80 листов в точку', '390'),
    ('Пижама Hello Kitty', 'Хлопковая пижама, размеры S–L', '2490'),
    ('Тапочки Hello Kitty', 'Пушистые тапочки с бантиками', '1290'),
    ('Зонт Hello Kitty', 'Складной зонт с автоматическим открыванием', '1790'),
    ('Бутылка Hello Kitty', 'Бутылка для воды 500 мл с трубочкой', '590'),
]

USERS = [
    ('anna', 'Анна', 'Котова', 'anna@kitty.ru'),
    ('maria', 'Мария', 'Белова', 'maria@kitty.ru'),
    ('kate', 'Екатерина', 'Розова', 'kate@kitty.ru'),
]

ORDERS = {
    'anna': [('done', [('Плюшевая Hello Kitty', 1), ('Наклейки', 2)]),
             ('new', [('Кружка Hello Kitty', 2)])],
    'maria': [('canceled', [('Рюкзак Hello Kitty', 1)]),
              ('done', [('Пенал Hello Kitty', 1), ('Блокнот Hello Kitty', 3)])],
    'kate': [('new', [('Пижама Hello Kitty', 1), ('Тапочки Hello Kitty', 1)])],
}


class Command(BaseCommand):
    help = 'Заполняет базу тестовыми товарами, пользователями и заказами'

    @transaction.atomic
    def handle(self, *args, **options):
        products = {}
        for name, description, price in PRODUCTS:
            product, _ = Product.objects.update_or_create(
                name=name, defaults={'description': description, 'price': Decimal(price)})
            products[name] = product

        for username, first_name, last_name, email in USERS:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'first_name': first_name, 'last_name': last_name, 'email': email})
            if created:
                user.set_password('123456')
                user.save()

        manager, created = User.objects.get_or_create(
            username='manager',
            defaults={'first_name': 'Ольга', 'last_name': 'Менеджерова',
                      'email': 'manager@kitty.ru', 'is_staff': True})
        if created:
            manager.set_password('manager123')
            manager.save()

        for username, orders in ORDERS.items():
            user = User.objects.get(username=username)
            if user.orders.exists():
                continue
            for status, lines in orders:
                total = sum(products[name].price * qty for name, qty in lines)
                order = Order.objects.create(user=user, status=status, total=total)
                OrderItem.objects.bulk_create([
                    OrderItem(order=order, product=products[name], name=name,
                              price=products[name].price, quantity=qty)
                    for name, qty in lines
                ])

        self.stdout.write(self.style.SUCCESS(
            f'Товаров: {Product.objects.count()}, пользователей: {User.objects.count()}, '
            f'заказов: {Order.objects.count()}'))
