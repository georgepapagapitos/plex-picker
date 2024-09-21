from unittest.mock import patch

from django.test import TestCase

from picker.views import (
    fetch_trailer_url,
    get_filtered_movies,
    get_random_movies,
    get_unique_genres,
)
from sync.models import Movie


class MovieUtilsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create test data for the Movie model
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
        # Assuming get_random_movies should return a list of movies
        movies = get_random_movies(Movie.objects.all(), 2)
        self.assertEqual(len(movies), 2)
        self.assertTrue(set(movies).issubset({self.movie1, self.movie2, self.movie3}))

    def test_fetch_trailer_url_existing(self):
        self.movie1.trailer_url = "http://existing_trailer.com"
        self.movie1.save()

        trailer_url = fetch_trailer_url(self.movie1)
        self.assertEqual(trailer_url, "http://existing_trailer.com")
        self.assertEqual(self.movie1.trailer_url, "http://existing_trailer.com")
