from decimal import Decimal

from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

MAX_QUANTITY = 99


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True, max_length=1000)
    price = models.DecimalField(max_digits=8, decimal_places=2,
                                validators=[MinValueValidator(Decimal('0.01'))])

    def __str__(self):
        return self.name


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[
        MinValueValidator(1), MaxValueValidator(MAX_QUANTITY)])

    class Meta:
        unique_together = ('user', 'product')

    @property
    def total(self):
        return self.product.price * self.quantity


class Order(models.Model):
    STATUSES = [
        ('new', 'Новый'),
        ('done', 'Выполнен'),
        ('canceled', 'Отменён'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUSES, default='new')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f'Заказ №{self.pk}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    @property
    def total(self):
        return self.price * self.quantity
