# apps/picker/forms/search_form.py

from django import forms


class SearchForm(forms.Form):
    query = forms.CharField(
        label="Search",
        max_length=255,
        widget=forms.TextInput(attrs={"placeholder": "Search Movies & TV"}),
    )
