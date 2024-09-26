# picker/urls.py

from django.urls import path

from picker.views.movie_detail_view import movie_detail_view
from picker.views.plex_content_view import plex_content_view
from picker.views.random_movie_view import random_movie_view
from picker.views.show_detail_view import show_detail_view

urlpatterns = [
    path("", plex_content_view, name="plex_content"),
    path("random/", random_movie_view, name="random_movie"),
    path("movies/<int:movie_id>/", movie_detail_view, name="movie_detail"),
    path("shows/<int:show_id>/", show_detail_view, name="show_detail"),
]
