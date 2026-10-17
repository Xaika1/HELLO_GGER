from django.contrib import admin
from django.urls import path, include

handler404 = 'web.errors.custom_404'
handler403 = 'web.errors.custom_403'
handler500 = 'web.errors.custom_500'

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('web.urls')),
]
