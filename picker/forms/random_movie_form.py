from django import forms

from sync.models import Movie
from sync.models.genre import Genre


class RandomMovieForm(forms.Form):
    GENRE_CHOICES = [("", "Any")]
    genre = forms.ChoiceField(choices=GENRE_CHOICES, required=False)
    count = forms.ChoiceField(choices=[(i, str(i)) for i in range(1, 5)], initial=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Fetch distinct genres that have at least one associated movie, ordered alphabetically
        genres_with_movies = (
            Genre.objects.filter(movies__isnull=False)
            .distinct()
            .order_by("name")
            .values_list("name", flat=True)
        )
        # Extend the choices with unique genres that have movies
        self.fields["genre"].choices += [(genre, genre) for genre in genres_with_movies]
