from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from .forms import ProductForm, UserForm
from .models import Product


class AdminOnly(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class ProtectSuperusers:
    def get_object(self, queryset=None):
        user = super().get_object(queryset)
        if user.is_superuser and not self.request.user.is_superuser:
            raise PermissionDenied
        return user


class ProductList(AdminOnly, ListView):
    model = Product
    ordering = 'name'
    template_name = 'panel/products.html'


class ProductCreate(AdminOnly, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'panel/form.html'
    success_url = reverse_lazy('panel-products')
    extra_context = {'title': 'Новый товар'}


class ProductUpdate(AdminOnly, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'panel/form.html'
    success_url = reverse_lazy('panel-products')
    extra_context = {'title': 'Редактирование товара'}


class ProductDelete(AdminOnly, DeleteView):
    model = Product
    template_name = 'panel/delete.html'
    success_url = reverse_lazy('panel-products')


class UserList(AdminOnly, ListView):
    model = User
    ordering = 'username'
    template_name = 'panel/users.html'


class UserCreate(AdminOnly, CreateView):
    model = User
    form_class = UserForm
    template_name = 'panel/form.html'
    success_url = reverse_lazy('panel-users')
    extra_context = {'title': 'Новый пользователь'}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if not self.request.user.is_superuser:
            form.fields['is_staff'].disabled = True
        return form


class UserUpdate(AdminOnly, ProtectSuperusers, UpdateView):
    model = User
    form_class = UserForm
    template_name = 'panel/form.html'
    success_url = reverse_lazy('panel-users')
    extra_context = {'title': 'Редактирование пользователя'}

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.object == self.request.user:
            form.fields['is_staff'].disabled = True
            form.fields['is_active'].disabled = True
        if not self.request.user.is_superuser:
            form.fields['is_staff'].disabled = True
        return form


class UserDelete(AdminOnly, ProtectSuperusers, DeleteView):
    model = User
    template_name = 'panel/delete.html'
    success_url = reverse_lazy('panel-users')

    def post(self, request, *args, **kwargs):
        if self.get_object() == request.user:
            messages.error(request, 'Нельзя удалить самого себя')
            return redirect('panel-users')
        return super().post(request, *args, **kwargs)
