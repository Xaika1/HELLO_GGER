from django.urls import path

from . import panel, views

urlpatterns = [
    path('', views.index, name='index'),
    path('cart/', views.cart, name='cart'),
    path('cart/add/<int:pk>/', views.cart_add, name='cart-add'),
    path('cart/update/<int:pk>/', views.cart_update, name='cart-update'),
    path('cart/remove/<int:pk>/', views.cart_remove, name='cart-remove'),
    path('profile/', views.profile, name='profile'),

    path('panel/', panel.ProductList.as_view(), name='panel-products'),
    path('panel/products/add/', panel.ProductCreate.as_view(), name='panel-product-add'),
    path('panel/products/<int:pk>/', panel.ProductUpdate.as_view(), name='panel-product-edit'),
    path('panel/products/<int:pk>/delete/', panel.ProductDelete.as_view(), name='panel-product-delete'),
    path('panel/users/', panel.UserList.as_view(), name='panel-users'),
    path('panel/users/add/', panel.UserCreate.as_view(), name='panel-user-add'),
    path('panel/users/<int:pk>/', panel.UserUpdate.as_view(), name='panel-user-edit'),
    path('panel/users/<int:pk>/delete/', panel.UserDelete.as_view(), name='panel-user-delete'),

    path('login/', views.login_view, name='web-login'),
    path('logout/', views.logout_view, name='web-logout'),
    path('signup/', views.sign_up, name='web-signup'),
]
