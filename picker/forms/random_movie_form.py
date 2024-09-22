# picker/forms/random_movie_form.py

from django import forms

from picker.helpers.random_movie_helpers import get_unique_genres


class RandomMovieForm(forms.Form):
    genre = forms.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["genre"].choices = [("", "Any")] + [
            (genre, genre) for genre in get_unique_genres()
        ]
