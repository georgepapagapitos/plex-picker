# tests/picker/test_movie_detail_view.py

from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.test import TestCase
from django.urls import reverse

from sync.models.genre import Genre
from sync.models.movie import Movie
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


class MovieDetailViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.drama = Genre.objects.create(name="Drama")
        cls.movie = Movie.objects.create(
            title="Test Movie",
            summary="A summary of the test movie.",
            year=2023,
            duration=120 * 60 * 1000,
            poster_url="https://via.placeholder.com/150",
            plex_key="test_key",
            trailer_url="http://example.com/trailer.mp4",
            tmdb_id=12345,
            rotten_tomatoes_rating=85.0,
        )
        cls.movie.genres.add(cls.drama)
        cls.movie.optimized_art.save(
            "optimized_art.jpg", ContentFile(b"This is a test image file.")
        )

    @patch("sync.models.mixins.ImageOptimizationMixin.optimize_image")
    def test_movie_detail_view_success(self, mock_optimize_image):
        mock_optimize_image.return_value = True
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"Test Image Content"
        response = self.client.get(f"/movies/{self.movie.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.movie.title)

    def test_movie_detail_view_not_found(self):
        nonexistent_movie_id = 99999
        response = self.client.get(reverse("movie_detail", args=[nonexistent_movie_id]))
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Error", status_code=404)

    def test_movie_detail_view_context(self):
        response = self.client.get(reverse("movie_detail", args=[self.movie.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["media"], self.movie)

    def test_invalid_movie_data(self):
        with self.assertRaises(ValidationError):
            invalid_movie = Movie(
                title="Invalid Movie",
                year=1887,
                rotten_tomatoes_rating=105.0,
            )
            invalid_movie.clean()
