# tests/sync/test_movie_model.py

from django.test import TestCase

from sync.models import Genre, Movie


class MovieModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create genres for the movie
        cls.action = Genre.objects.create(name="Action")
        cls.sci_fi = Genre.objects.create(name="Sci-Fi")
        cls.drama = Genre.objects.create(name="Drama")

        # Create a movie with duration set in milliseconds
        cls.movie = Movie.objects.create(
            title="Inception",
            summary="A mind-bending thriller",
            year=2010,
            duration=148 * 60 * 1000,  # 148 minutes in milliseconds
            poster_url="http://example.com/inception.jpg",
            plex_key="plex_key_1",
            trailer_url="http://example.com/trailer.mp4",
            tmdb_id=123456,
            rotten_tomatoes_rating=86.0,
        )
        cls.movie.genres.add(cls.action, cls.sci_fi, cls.drama)

    def test_movie_creation(self):
        self.assertEqual(self.movie.title, "Inception")
        self.assertEqual(self.movie.summary, "A mind-bending thriller")
        self.assertEqual(self.movie.year, 2010)

    def test_str_method(self):
        self.assertEqual(str(self.movie), "Inception (2010)")

    def test_movie_genres(self):
        self.assertEqual(self.movie.genres.count(), 3)
        self.assertIn(self.action, self.movie.genres.all())
        self.assertIn(self.sci_fi, self.movie.genres.all())
        self.assertIn(self.drama, self.movie.genres.all())

    def test_formatted_duration(self):
        self.assertEqual(self.movie.formatted_duration(), "2h 28m")  # Expected format

    def test_formatted_genres(self):
        expected_genres = "Action, Sci-Fi, Drama"
        self.assertEqual(self.movie.formatted_genres(), expected_genres)
