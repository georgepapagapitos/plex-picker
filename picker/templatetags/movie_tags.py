# picker/templatetags/movie_tags.py

from django import template
from django.urls import reverse

register = template.Library()


@register.simple_tag
def get_detail_url(movie):
    if movie.type == "movie":
        return reverse("movie_detail", args=[movie.id])
    else:
        return reverse("show_detail", args=[movie.id])
