# tests/picker/test_plex_content_view.py

from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from sync.models import Genre, Movie, Show


class PlexContentViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        drama = Genre.objects.create(name="Drama")
        comedy = Genre.objects.create(name="Comedy")

        cls.movie = Movie.objects.create(
            title="Test Movie",
            summary="A summary of the test movie.",
            year=2023,
            duration=120,
            poster_url="http://example.com/poster.jpg",
            plex_key="test_key",
            trailer_url="http://example.com/trailer",
            tmdb_id=12345,
            rotten_tomatoes_rating=8.5,
        )
        cls.movie.genres.add(drama)
        cls.show = Show.objects.create(
            title="Test Show",
            summary="A summary of the test show.",
            year=2023,
            duration=60,
            poster_url="http://example.com/show_poster.jpg",
            plex_key=1,
            tmdb_id=54321,
            rotten_tomatoes_rating=7,
        )
        cls.show.genres.add(comedy)

    def test_plex_content_view_success(self):
        response = self.client.get(reverse("plex_content"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "")
        self.assertContains(response, self.movie.title)
        self.assertContains(response, self.show.title)

    @patch("sync.models.Movie.objects.all")
    @patch("sync.models.Show.objects.all")
    def test_plex_content_view_error(self, mock_show, mock_movie):
        mock_movie.side_effect = Exception("Database error")
        mock_show.side_effect = Exception("Database error")

        response = self.client.get(reverse("plex_content"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Unexpected Error")
        self.assertContains(
            response, "An unexpected error occurred. Please try again later."
        )
