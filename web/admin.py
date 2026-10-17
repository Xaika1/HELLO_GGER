from django.contrib import admin
from .models import Product, Order, OrderItem

admin.site.register(Product)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'total', 'status')
    list_filter = ('status',)
    inlines = [OrderItemInline]
