# picker/urls.py

from django.urls import path

from picker.views import MovieCastView
from picker.views.movie_detail_view import MovieDetailView
from picker.views.person_detail_view import PersonDetailView
from picker.views.plex_content_view import PlexContentView
from picker.views.random_movie_view import RandomMovieView
from picker.views.show_detail_view import ShowDetailView

urlpatterns = [
    path("", PlexContentView.as_view(), name="plex_content"),
    path("movies/<int:movie_id>/", MovieDetailView.as_view(), name="movie_detail"),
    path("movies/<int:movie_id>/cast/", MovieCastView.as_view(), name="movie_cast"),
    path("person/<int:person_id>", PersonDetailView.as_view(), name="person_detail"),
    path("shows/<int:show_id>/", ShowDetailView.as_view(), name="show_detail"),
    path("random/", RandomMovieView.as_view(), name="random_movie"),
]
