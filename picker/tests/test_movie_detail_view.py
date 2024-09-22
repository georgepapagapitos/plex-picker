from django.test import TestCase
from django.urls import reverse

from sync.models.movie import Movie


class MovieDetailViewTests(TestCase):
    def setUp(self):
        # Create a sample movie for testing
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

    def test_movie_detail_view_success(self):
        response = self.client.get(reverse("movie_detail", args=[self.movie.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.movie.title)
        self.assertContains(response, self.movie.summary)

    def test_movie_detail_view_not_found(self):
        response = self.client.get(
            reverse("movie_detail", args=[999])
        )  # Non-existent ID
        self.assertEqual(
            response.status_code, 200
        )  # Expecting 200 since it renders an error page
        self.assertContains(response, "Oops! Something went wrong.")
        self.assertContains(response, "The requested movie was not found.")
