# picker/forms/tests/test_forms.py

from django.test import TestCase

from picker.forms import SearchForm


class SearchFormTests(TestCase):
    def test_valid_form(self):
        """Test that the form is valid with a valid query."""
        form_data = {"query": "Inception"}
        form = SearchForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["query"], "Inception")

    def test_empty_query(self):
        """Test that the form is invalid with an empty query."""
        form_data = {"query": ""}
        form = SearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("query", form.errors)
        self.assertEqual(form.errors["query"], ["This field is required."])

    def test_too_long_query(self):
        """Test that the form is invalid with a query that exceeds max length."""
        form_data = {"query": "a" * 256}  # 256 characters
        form = SearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("query", form.errors)
        self.assertEqual(
            form.errors["query"],
            ["Ensure this value has at most 255 characters (it has 256)."],
        )

    def test_valid_query_with_whitespace(self):
        """Test that the form is valid with a valid query that has leading/trailing whitespace."""
        form_data = {"query": "   Interstellar   "}
        form = SearchForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(
            form.cleaned_data["query"], "Interstellar"
        )  # Adjusted to match cleaned value
