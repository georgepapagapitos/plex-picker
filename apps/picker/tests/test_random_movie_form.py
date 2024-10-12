# apps/picker/tests/test_random_movie_form.py

from django.http import QueryDict
from django.test import TestCase
from picker.forms.random_movie_form import RandomMovieForm
from sync.models import Genre, Movie


class RandomMovieFormTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        genre1 = Genre.objects.create(name="Action")
        genre2 = Genre.objects.create(name="Comedy")
        movie1 = Movie.objects.create(
            title="Test Movie 1",
            year=2020,
            duration=7200000,
            rotten_tomatoes_rating=85,
            plex_key="movie1",
        )
        movie1.genres.add(genre1)
        movie2 = Movie.objects.create(
            title="Test Movie 2",
            year=2021,
            duration=5400000,
            rotten_tomatoes_rating=75,
            plex_key="movie2",
        )
        movie2.genres.add(genre2)

    def test_form_fields(self):
        form = RandomMovieForm()
        self.assertIn("genre", form.fields)
        self.assertIn("count", form.fields)
        self.assertIn("min_rotten_tomatoes_rating", form.fields)
        self.assertIn("max_duration", form.fields)
        self.assertIn("min_year", form.fields)
        self.assertIn("max_year", form.fields)

    def test_genre_choices(self):
        form = RandomMovieForm()
        genre_choices = [choice[1] for choice in form.fields["genre"].choices]
        self.assertIn("Any", genre_choices)
        self.assertIn("Action", genre_choices)
        self.assertIn("Comedy", genre_choices)

    def test_count_choices(self):
        form = RandomMovieForm()
        count_choices = [int(choice[1]) for choice in form.fields["count"].choices]
        self.assertEqual(count_choices, [1, 2, 3, 4])

    def test_rating_choices(self):
        form = RandomMovieForm()
        rating_choices = [
            choice[1] for choice in form.fields["min_rotten_tomatoes_rating"].choices
        ]
        self.assertIn("Any", rating_choices)
        self.assertIn("75%", rating_choices)
        self.assertIn("85%", rating_choices)

    def test_duration_choices(self):
        form = RandomMovieForm()
        duration_choices = [choice[1] for choice in form.fields["max_duration"].choices]
        self.assertIn("Any", duration_choices)
        self.assertIn("1h 30m", duration_choices)
        self.assertIn("2h", duration_choices)

    def test_year_choices(self):
        form = RandomMovieForm()
        year_choices = [choice[1] for choice in form.fields["min_year"].choices]
        self.assertIn("Any", year_choices)
        self.assertIn("2020", year_choices)
        self.assertIn("2021", year_choices)

    def test_clean_min_rotten_tomatoes_rating(self):
        form = RandomMovieForm({"min_rotten_tomatoes_rating": "75", "count": "1"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["min_rotten_tomatoes_rating"], 75)

    def test_clean_max_duration(self):
        form = RandomMovieForm({"max_duration": "120", "count": "1"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["max_duration"], 120)

    def test_clean_min_year(self):
        form = RandomMovieForm({"min_year": "2020", "count": "1"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["min_year"], 2020)

    def test_clean_max_year(self):
        form = RandomMovieForm({"max_year": "2021", "count": "1"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["max_year"], 2021)

    def test_is_reset(self):
        form = RandomMovieForm({"reset": True})
        self.assertTrue(form.is_reset())

    def test_form_initial_values(self):
        form = RandomMovieForm(data={"genre": ["Action", "Comedy"], "count": "2"})
        self.assertEqual(form.fields["genre"].initial, ["Action", "Comedy"])
        self.assertEqual(form.fields["count"].initial, "2")

    def test_form_validation(self):
        form_data = {
            "genre": ["Action", "Comedy"],
            "count": "2",
            "min_rotten_tomatoes_rating": "75",
            "max_duration": "120",
            "min_year": "2020",
            "max_year": "2021",
        }
        form = RandomMovieForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_validation_with_empty_fields(self):
        form_data = {
            "genre": [],
            "count": "1",
            "min_rotten_tomatoes_rating": "",
            "max_duration": "",
            "min_year": "",
            "max_year": "",
        }
        form = RandomMovieForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_clean_methods_with_empty_values(self):
        form = RandomMovieForm(
            {
                "count": "1",
                "min_rotten_tomatoes_rating": "",
                "max_duration": "",
                "min_year": "",
                "max_year": "",
            }
        )
        self.assertTrue(form.is_valid())
        self.assertIsNone(form.cleaned_data["min_rotten_tomatoes_rating"])
        self.assertIsNone(form.cleaned_data["max_duration"])
        self.assertIsNone(form.cleaned_data["min_year"])
        self.assertIsNone(form.cleaned_data["max_year"])

    def test_multiple_genre_selection(self):
        form = RandomMovieForm(data={"genre": ["Action", "Comedy"], "count": "1"})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["genre"], ["Action", "Comedy"])

    def test_form_initial_values_single_genre(self):
        form = RandomMovieForm(data={"genre": "Action", "count": "2"})
        self.assertEqual(form.fields["genre"].initial, ["Action"])
        self.assertEqual(form.fields["count"].initial, "2")

    def test_form_with_querydict(self):
        query_dict = QueryDict("genre=Action&genre=Comedy&count=2")
        form = RandomMovieForm(data=query_dict)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["genre"], ["Action", "Comedy"])
        self.assertEqual(form.cleaned_data["count"], "2")
