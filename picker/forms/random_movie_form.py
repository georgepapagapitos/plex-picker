from django import forms
from django.db.models import Max, Min

from sync.models import Movie
from sync.models.genre import Genre


class RandomMovieForm(forms.Form):
    GENRE_CHOICES = [("", "Any")]
    genre = forms.ChoiceField(choices=GENRE_CHOICES, required=False)
    count = forms.ChoiceField(choices=[(i, str(i)) for i in range(1, 5)], initial=1)

    # Initialize fields for min rating and max duration without choices
    min_rotten_tomatoes_rating = forms.ChoiceField(required=False)
    max_duration = forms.ChoiceField(required=False)

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

        # Set rating choices including "Any"
        self.fields["min_rotten_tomatoes_rating"].choices = self.get_rating_choices()
        # Set duration choices including "Any"
        self.fields["max_duration"].choices = self.get_duration_choices()

    def clean_min_rotten_tomatoes_rating(self):
        value = self.cleaned_data.get("min_rotten_tomatoes_rating")
        return int(value) if value else None

    def clean_max_duration(self):
        value = self.cleaned_data.get("max_duration")
        return int(value) if value else None

    def get_duration_choices(self):
        """Generate duration choices in a human-readable format based on existing movies."""
        durations = Movie.objects.aggregate(
            min_duration=Min("duration"), max_duration=Max("duration")
        )

        min_duration = (
            int(durations["min_duration"] // 60000) if durations["min_duration"] else 0
        )
        max_duration = (
            int(durations["max_duration"] // 60000) if durations["max_duration"] else 0
        )

        choices = [("", "Any")]  # Start with "Any" option

        for hours in range(0, (max_duration // 60) + 1):  # Up to the maximum hours
            for minutes in range(0, 60, 30):  # Every 30 minutes
                total_minutes = hours * 60 + minutes
                if total_minutes < min_duration or total_minutes > max_duration:
                    continue  # Skip if not in range

                if hours > 0 and minutes > 0:
                    choices.append((total_minutes, f"{hours}h {minutes}m"))
                elif hours > 0:
                    choices.append((total_minutes, f"{hours}h"))
                else:
                    choices.append((total_minutes, f"{minutes}m"))

        return choices

    def get_rating_choices(self):
        """Generate rating choices based on existing movies."""
        ratings = Movie.objects.aggregate(
            min_rating=Min("rotten_tomatoes_rating"),
            max_rating=Max("rotten_tomatoes_rating"),
        )

        # Handle None values for min and max ratings
        min_rating = (
            int(ratings["min_rating"]) if ratings["min_rating"] is not None else 0
        )
        max_rating = (
            int(ratings["max_rating"]) if ratings["max_rating"] is not None else 100
        )

        choices = [("", "Any")]  # Start with "Any" option

        # Generate choices in increments of 10
        for rating in range(min_rating, max_rating + 1, 10):
            choices.append((rating, f"{rating}%"))

        return choices
