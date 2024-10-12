# plexpicker/urls.py

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from picker.views import Custom404View

handler404 = Custom404View.as_view()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("picker.urls")),
    path("__reload__/", include("django_browser_reload.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
