from django.test import TestCase

from picker.views import get_filtered_movies, get_random_movies, get_unique_genres
from sync.models.movie import Movie


class MovieUtilsTests(TestCase):
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

    def test_get_unique_genres(self):
        genres = get_unique_genres()
        self.assertEqual(genres, ["Action", "Comedy", "Drama"])

    def test_get_filtered_movies(self):
        query = get_filtered_movies("Action")
        movies = Movie.objects.filter(query)
        self.assertIn(self.movie1, movies)
        self.assertIn(self.movie2, movies)
        self.assertNotIn(self.movie3, movies)

    def test_get_random_movies(self):
        movies = get_random_movies(Movie.objects.all(), 2)
        self.assertEqual(len(movies), 2)
        self.assertTrue(set(movies).issubset({self.movie1, self.movie2, self.movie3}))
