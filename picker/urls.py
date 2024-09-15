from django.urls import path

from picker.views.fetch_plex_content_view import fetch_plex_content
from picker.views.fetch_random_movie_view import fetch_random_movie

urlpatterns = [
    path("content/", fetch_plex_content, name="fetch_plex_content"),
    path("random-movie/", fetch_random_movie, name="fetch_random_movie"),
]
