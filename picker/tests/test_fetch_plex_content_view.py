from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from sync.models.movie import Movie
from sync.models.show import Show


class FetchPlexContentViewTests(TestCase):
    def setUp(self):
        # Create sample movie for testing
        self.movie = Movie.objects.create(
            title="Test Movie",
            summary="A summary of the test movie.",
            year=2023,
            duration=120,
            poster_url="http://example.com/poster.jpg",
            genres="Drama",
            plex_key="test_key",
            trailer_url="http://example.com/trailer",
            tmdb_id=12345,
            rotten_tomatoes_rating=8.5,
        )

        # Create sample show for testing
        self.show = Show.objects.create(
            title="Test Show",
            summary="A summary of the test show.",
            year=2023,
            duration=60,
            poster_url="http://example.com/show_poster.jpg",
            genres="Comedy",
            plex_key=1,
            tmdb_id=54321,
            rotten_tomatoes_rating=7,
        )

    def test_fetch_plex_content_view_success(self):
        response = self.client.get(
            reverse("fetch_plex_content")
        )  # Adjust to your URL name
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Plex Content")
        self.assertContains(response, self.movie.title)
        self.assertContains(response, self.show.title)

    @patch("sync.models.Movie.objects.all")
    @patch("sync.models.Show.objects.all")
    def test_fetch_plex_content_view_error(self, mock_show, mock_movie):
        # Simulate an error by making the queries raise an exception
        mock_movie.side_effect = Exception("Database error")
        mock_show.side_effect = Exception("Database error")

        response = self.client.get(
            reverse("fetch_plex_content")
        )  # Adjust to your URL name
        self.assertEqual(
            response.status_code, 200
        )  # Expecting 200 since it renders an error page
        self.assertContains(response, "Unexpected Error")
        self.assertContains(
            response, "An unexpected error occurred. Please try again later."
        )
