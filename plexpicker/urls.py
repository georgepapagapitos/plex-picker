# plexpicker/urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from picker.views.error_views import custom_404_view

handler404 = custom_404_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("picker.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
