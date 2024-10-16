from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from backend import settings

urlpatterns = [
    path('admin/', admin.site.urls),
] + static(settings.FILES_URL, document_root=settings.FILES_ROOT)
