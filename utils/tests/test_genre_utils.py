from django.test import TestCase

from sync.models import Movie
from sync.models.genre import Genre


class TestGenreUtils(TestCase):
    @classmethod
    def setUpTestData(cls):
        action = Genre.objects.create(name="Action")
        comedy = Genre.objects.create(name="Comedy")
        drama = Genre.objects.create(name="Drama")

        cls.movie1 = Movie.objects.create(
            title="Movie 1", tmdb_id=1, plex_key="plex_key_1"
        )
        cls.movie2 = Movie.objects.create(
            title="Movie 2", tmdb_id=2, plex_key="plex_key_2"
        )
        cls.movie3 = Movie.objects.create(
            title="Movie 3", tmdb_id=3, plex_key="plex_key_3"
        )
        cls.movie4 = Movie.objects.create(
            title="Movie 4", genres=None, tmdb_id=4, plex_key="plex_key_4"
        )
        cls.movie5 = Movie.objects.create(
            title="Movie 5", genres="Horror", tmdb_id=5, plex_key="plex_key_5"
        )
