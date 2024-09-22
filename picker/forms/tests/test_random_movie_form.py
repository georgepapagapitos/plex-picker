from django.test import TestCase

from picker.forms import RandomMovieForm


class RandomMovieFormTests(TestCase):

    def setUp(self):
        self.genres = ["Action", "Comedy", "Drama"]  # Sample genres for testing

    def test_form_initialization_with_genres(self):
        form = RandomMovieForm(genres=self.genres)
        self.assertIn(("Action", "Action"), form.fields["genre"].choices)
        self.assertIn(("Comedy", "Comedy"), form.fields["genre"].choices)
        self.assertIn(("Drama", "Drama"), form.fields["genre"].choices)

    def test_form_with_valid_data(self):
        form_data = {"genre": "Action", "count": "2"}
        form = RandomMovieForm(data=form_data, genres=self.genres)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["genre"], "Action")
        self.assertEqual(form.cleaned_data["count"], "2")

    def test_form_with_invalid_count(self):
        form_data = {"genre": "Action", "count": "5"}  # Invalid count (max is 4)
        form = RandomMovieForm(data=form_data, genres=self.genres)
        self.assertFalse(form.is_valid())
        self.assertIn("count", form.errors)

    def test_form_without_data(self):
        form = RandomMovieForm(data={}, genres=self.genres)
        self.assertFalse(form.is_valid())
        self.assertIn(
            "count", form.errors
        )  # Count should be required if genre is not selected

    def test_empty_genre_choices(self):
        form = RandomMovieForm(genres=[])
        self.assertEqual(
            form.fields["genre"].choices, [("", "Any")]
        )  # Only the "Any" option should remain
