# apps/picker/tests/test_movie_helpers.py

from unittest.mock import MagicMock, patch

from django.test import TestCase
from picker.helpers.movie_helpers import get_filtered_movies, get_random_movies
from sync.models import Genre, Movie


class TestRandomMovieHelpers(TestCase):
    @classmethod
    def setUpTestData(cls):
        action = Genre.objects.create(name="Action")
        comedy = Genre.objects.create(name="Comedy")
        drama = Genre.objects.create(name="Drama")
        horror = Genre.objects.create(name="Horror")
        cls.movie1 = Movie.objects.create(
            title="Movie 1", tmdb_id=1, plex_key="plex_key_1"
        )
        cls.movie1.genres.add(action, comedy)
        cls.movie2 = Movie.objects.create(
            title="Movie 2", tmdb_id=2, plex_key="plex_key_2"
        )
        cls.movie2.genres.add(action)
        cls.movie3 = Movie.objects.create(
            title="Movie 3", tmdb_id=3, plex_key="plex_key_3"
        )
        cls.movie3.genres.add(drama)
        cls.movie4 = Movie.objects.create(
            title="Movie 4", tmdb_id=4, plex_key="plex_key_4"
        )
        cls.movie4.genres.add()
        cls.movie5 = Movie.objects.create(
            title="Movie 5", tmdb_id=5, plex_key="plex_key_5"
        )
        cls.movie5.genres.add(horror)

    def test_get_filtered_movies(self):
        query = get_filtered_movies("Action")
        movies = Movie.objects.filter(query)
        self.assertIn(self.movie1, movies)
        self.assertIn(self.movie2, movies)
        self.assertNotIn(self.movie3, movies)
        self.assertNotIn(self.movie4, movies)

    @patch("sync.models.Movie.objects.all")
    def test_get_random_movies(self, mock_all):
        mock_queryset = MagicMock()
        mock_queryset.order_by.return_value = [
            self.movie1,
            self.movie2,
            self.movie3,
            self.movie5,
        ]
        mock_all.return_value = mock_queryset
        movies = get_random_movies(mock_all.return_value, 2)
        self.assertEqual(len(movies), 2)
        self.assertTrue(
            set(movies).issubset({self.movie1, self.movie2, self.movie3, self.movie5})
        )
        self.assertTrue(
            all(
                movie.title
                in {
                    self.movie1.title,
                    self.movie2.title,
                    self.movie3.title,
                    self.movie5.title,
                }
                for movie in movies
            )
        )
