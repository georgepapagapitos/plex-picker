# tests/picker/test_random_movie_view.py

from django.test import TestCase

from picker.helpers.movie_helpers import get_filtered_movies, get_random_movies
from sync.models.genre import Genre
from sync.models.movie import Movie


class RandomMovieViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        action = Genre.objects.create(name="Action")
        comedy = Genre.objects.create(name="Comedy")
        drama = Genre.objects.create(name="Drama")
        cls.movie1 = Movie.objects.create(
            title="Movie 1", tmdb_id=1, plex_key="plex_key_1"
        )
        cls.movie1.genres.set([action, comedy])
        cls.movie2 = Movie.objects.create(
            title="Movie 2", tmdb_id=2, plex_key="plex_key_2"
        )
        cls.movie2.genres.set([action])
        cls.movie3 = Movie.objects.create(
            title="Movie 3", tmdb_id=3, plex_key="plex_key_3"
        )
        cls.movie3.genres.set([drama])

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
