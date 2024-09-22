# picker/forms.py

from django import forms


class RandomMovieForm(forms.Form):
    GENRE_CHOICES = [("", "Any")]
    genre = forms.ChoiceField(choices=GENRE_CHOICES, required=False)
    count = forms.ChoiceField(choices=[(i, str(i)) for i in range(1, 5)], initial=1)

    def __init__(self, *args, **kwargs):
        genres = kwargs.pop("genres", [])
        super().__init__(*args, **kwargs)
        # Extend the choices with unique genres
        self.fields["genre"].choices += [(genre, genre) for genre in genres]
