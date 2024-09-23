from django.urls import path

from picker.views import fetch_plex_content, fetch_random_movie, movie_detail_view

urlpatterns = [
    path("", fetch_plex_content, name="fetch_plex_content"),
    path("random-movie/", fetch_random_movie, name="fetch_random_movie"),
    path("movies/<int:movie_id>/", movie_detail_view, name="movie_detail"),
]
