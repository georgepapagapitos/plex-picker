from django.test import TestCase

from picker.helpers.genre_helpers import get_unique_genres
from sync.models import Movie


class TestRandomMovieHelpers(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.movie1 = Movie.objects.create(
            title="Movie 1", genres="Action, Comedy", tmdb_id=1, plex_key="plex_key_1"
        )
        cls.movie2 = Movie.objects.create(
            title="Movie 2", genres="Action", tmdb_id=2, plex_key="plex_key_2"
        )
        cls.movie3 = Movie.objects.create(
            title="Movie 3", genres="Drama", tmdb_id=3, plex_key="plex_key_3"
        )
        cls.movie4 = Movie.objects.create(
            title="Movie 4", genres=None, tmdb_id=4, plex_key="plex_key_4"
        )
        cls.movie5 = Movie.objects.create(
            title="Movie 5", genres="Horror", tmdb_id=5, plex_key="plex_key_5"
        )

    def test_get_unique_genres(self):
        genres = get_unique_genres()
        self.assertEqual(genres, ["Action", "Comedy", "Drama", "Horror"])
