# picker/templatetags/image_tags.py

from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def lazy_load_image(url, alt_text, classes=""):
    return mark_safe(
        f'<img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=" data-src="{url}" alt="{alt_text}" class="lazyload {classes}">'
    )
