from django.test import TestCase

from sync.models import Movie


class MovieModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.movie = Movie.objects.create(
            title="Inception",
            summary="A mind-bending thriller",
            year=2010,
            duration=148,
            poster_url="http://example.com/inception.jpg",
            genres="Action, Sci-Fi",
            plex_key="plex_key_1",
            trailer_url="http://example.com/trailer.mp4",
            tmdb_id=123456,
            rotten_tomatoes_rating=86.0,
        )

    def test_movie_creation(self):
        self.assertEqual(self.movie.title, "Inception")
        self.assertEqual(self.movie.summary, "A mind-bending thriller")
        self.assertEqual(self.movie.year, 2010)

    def test_str_method(self):
        self.assertEqual(str(self.movie), "Inception")
