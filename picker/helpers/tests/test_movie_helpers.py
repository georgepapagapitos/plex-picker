from unittest.mock import MagicMock, patch

from django.test import TestCase

from picker.helpers.movie_helpers import get_filtered_movies, get_random_movies
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

    def test_get_filtered_movies(self):
        query = get_filtered_movies("Action")
        movies = Movie.objects.filter(query)
        self.assertIn(self.movie1, movies)
        self.assertIn(self.movie2, movies)
        self.assertNotIn(self.movie3, movies)
        self.assertNotIn(self.movie4, movies)

    @patch("sync.models.Movie.objects.all")
    def test_get_random_movies(self, mock_all):
        # Create a mock queryset
        mock_queryset = MagicMock()
        # Set the return value for the order_by method
        mock_queryset.order_by.return_value = [
            self.movie1,
            self.movie2,
            self.movie3,
            self.movie5,
        ]

        # Set the mock to return the mock queryset
        mock_all.return_value = mock_queryset

        # Call the function under test
        movies = get_random_movies(mock_all.return_value, 2)

        # Assertions
        self.assertEqual(len(movies), 2)
        self.assertTrue(
            set(movies).issubset({self.movie1, self.movie2, self.movie3, self.movie5})
        )
