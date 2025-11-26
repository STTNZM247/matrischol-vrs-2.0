from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static


def home(request):
    return render(request, 'home.html')


urlpatterns = [
    path('', home, name='home'),
    path('accounts/', include('accounts.urls')),
    path('school/', include('school.urls')),
    path('adminpanel/', include('adminpanel.urls')),
    path('admin/', admin.site.urls),
]

# Servir archivos media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
