from django.test import TestCase

from picker.forms import RandomMovieForm
from sync.models import Movie  # Assuming Movie is in sync.models
from sync.models.genre import Genre


class RandomMovieFormTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Create Genre instances
        action = Genre.objects.create(name="Action")
        comedy = Genre.objects.create(name="Comedy")
        drama = Genre.objects.create(name="Drama")

        # Create Movies associated with these genres
        Movie.objects.create(
            title="Action Movie", duration=120, year=2022, plex_key="action_1"
        )
        Movie.objects.create(
            title="Comedy Movie", duration=90, year=2021, plex_key="comedy_1"
        )
        Movie.objects.create(
            title="Drama Movie", duration=140, year=2020, plex_key="drama_1"
        )

        # Add genres to movies to reflect the associations
        Movie.objects.filter(title="Action Movie").first().genres.add(action)
        Movie.objects.filter(title="Comedy Movie").first().genres.add(comedy)
        Movie.objects.filter(title="Drama Movie").first().genres.add(drama)

        cls.genre_names = [action.name, comedy.name, drama.name]

    def test_form_initialization_with_genres(self):
        form = RandomMovieForm()
        for genre in self.genre_names:
            self.assertIn((genre, genre), form.fields["genre"].choices)

    def test_form_with_valid_data(self):
        form_data = {"genre": "Action", "count": "2"}
        form = RandomMovieForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["genre"], "Action")
        self.assertEqual(form.cleaned_data["count"], "2")

    def test_form_with_invalid_count(self):
        form_data = {"genre": "Action", "count": "5"}  # Invalid count (max is 4)
        form = RandomMovieForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("count", form.errors)

    def test_form_without_data(self):
        form = RandomMovieForm(data={})
        self.assertFalse(form.is_valid())
        self.assertIn(
            "count", form.errors
        )  # Count should be required if genre is not selected

    def test_empty_genre_choices(self):
        # Case when there are no movies associated with genres
        Genre.objects.all().delete()  # Clear genres to simulate no available choices
        form = RandomMovieForm()
        self.assertEqual(
            form.fields["genre"].choices, [("", "Any")]
        )  # Only the "Any" option should remain
