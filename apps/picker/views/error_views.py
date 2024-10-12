# apps/picker/views/error_views.py

from django.shortcuts import render


def custom_404_view(request, exception):
    return render(request, "error.html", status=404)
