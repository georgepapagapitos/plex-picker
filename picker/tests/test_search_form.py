# picker/tests/test_search_form.py

from django.test import TestCase

from picker.forms import SearchForm


class SearchFormTests(TestCase):
    def test_valid_form(self):
        form_data = {"query": "Inception"}
        form = SearchForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["query"], "Inception")

    def test_empty_query(self):
        form_data = {"query": ""}
        form = SearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("query", form.errors)
        self.assertEqual(form.errors["query"], ["This field is required."])

    def test_too_long_query(self):
        form_data = {"query": "a" * 256}
        form = SearchForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("query", form.errors)
        self.assertEqual(
            form.errors["query"],
            ["Ensure this value has at most 255 characters (it has 256)."],
        )

    def test_valid_query_with_whitespace(self):
        form_data = {"query": "   Interstellar   "}
        form = SearchForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data["query"], "Interstellar")

    def test_form_widget_attributes(self):
        form = SearchForm()
        self.assertEqual(
            form.fields["query"].widget.attrs["placeholder"], "Search Movies & TV"
        )
