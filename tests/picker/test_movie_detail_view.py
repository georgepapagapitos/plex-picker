# tests/picker/test_movie_detail_view.py

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse

from sync.models.genre import Genre
from sync.models.movie import Movie


class MovieDetailViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create genres to associate with the movie
        cls.drama = Genre.objects.create(name="Drama")

        # Create a sample movie for testing
        cls.movie = Movie.objects.create(
            title="Test Movie",
            summary="A summary of the test movie.",
            year=2023,
            duration=120 * 60 * 1000,  # Duration in milliseconds
            poster_url="http://example.com/poster.jpg",
            plex_key="test_key",
            trailer_url="http://example.com/trailer.mp4",
            tmdb_id=12345,
            rotten_tomatoes_rating=85.0,
        )
        cls.movie.genres.add(cls.drama)

    def test_movie_detail_view_success(self):
        # Test if the movie detail view renders correctly
        response = self.client.get(reverse("movie_detail", args=[self.movie.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.movie.title)
        self.assertContains(response, self.movie.summary)
        self.assertContains(response, self.movie.formatted_duration())
        self.assertContains(response, self.movie.formatted_genres())

    def test_movie_detail_view_not_found(self):
        # Test if a non-existent movie triggers a 404 error
        response = self.client.get(
            reverse("movie_detail", args=[999])
        )  # Non-existent ID
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "The requested movie was not found.")

    def test_movie_detail_view_context(self):
        # Test if the correct movie object is passed in the context
        response = self.client.get(reverse("movie_detail", args=[self.movie.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["media"], self.movie)

    def test_invalid_movie_data(self):
        # Test validation errors during movie creation
        with self.assertRaises(ValidationError):
            invalid_movie = Movie(
                title="Invalid Movie",
                year=1887,  # Year is below valid range
                rotten_tomatoes_rating=105.0,  # Rating is above valid range
            )
            invalid_movie.clean()  # Trigger validation
