# picker/forms.py
from django import forms


class SearchForm(forms.Form):
    query = forms.CharField(
        label="Search",
        max_length=255,
        widget=forms.TextInput(
            attrs={"placeholder": "Search for movies, shows, or actors..."}
        ),
    )
