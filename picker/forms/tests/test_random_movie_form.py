from django import forms
from django.db.models import Max, Min

from sync.models import Movie
from sync.models.genre import Genre


class RandomMovieForm(forms.Form):
    GENRE_CHOICES = [("", "Any")]
    genre = forms.ChoiceField(choices=GENRE_CHOICES, required=False)
    count = forms.ChoiceField(choices=[(i, str(i)) for i in range(1, 5)], initial=1)

    min_rotten_tomatoes_rating = forms.ChoiceField(required=False)
    max_duration = forms.ChoiceField(required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        genres_with_movies = (
            Genre.objects.filter(movies__isnull=False)
            .distinct()
            .order_by("name")
            .values_list("name", flat=True)
        )
        self.fields["genre"].choices += [(genre, genre) for genre in genres_with_movies]
        self.fields["min_rotten_tomatoes_rating"].choices = self.get_rating_choices()
        self.fields["max_duration"].choices = self.get_duration_choices()

    def clean_min_rotten_tomatoes_rating(self):
        value = self.cleaned_data.get("min_rotten_tomatoes_rating")
        return int(value) if value else None

    def clean_max_duration(self):
        value = self.cleaned_data.get("max_duration")
        return int(value) if value else ""  # Change to return empty string

    def get_duration_choices(self):
        durations = Movie.objects.aggregate(
            min_duration=Min("duration"), max_duration=Max("duration")
        )

        min_duration = (
            int(durations["min_duration"] // 60000) if durations["min_duration"] else 0
        )
        max_duration = (
            int(durations["max_duration"] // 60000) if durations["max_duration"] else 0
        )

        choices = [("", "Any")]

        for hours in range(0, (max_duration // 60) + 1):
            for minutes in range(0, 60, 30):
                total_minutes = hours * 60 + minutes
                if total_minutes < min_duration or total_minutes > max_duration:
                    continue

                if hours > 0 and minutes > 0:
                    choices.append((total_minutes, f"{hours}h {minutes}m"))
                elif hours > 0:
                    choices.append((total_minutes, f"{hours}h"))
                else:
                    choices.append((total_minutes, f"{minutes}m"))

        return choices

    def get_rating_choices(self):
        ratings = Movie.objects.aggregate(
            min_rating=Min("rotten_tomatoes_rating"),
            max_rating=Max("rotten_tomatoes_rating"),
        )

        min_rating = (
            int(ratings["min_rating"]) if ratings["min_rating"] is not None else 0
        )
        max_rating = (
            int(ratings["max_rating"]) if ratings["max_rating"] is not None else 100
        )

        choices = [("", "Any")]

        for rating in range(min_rating, max_rating + 1, 10):
            choices.append((rating, f"{rating}%"))

        return choices
