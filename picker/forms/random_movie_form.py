# picker/forms/random_movie_form.py

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from django import forms
from django.db.models import Max, Min

from sync.models import Movie
from sync.models.genre import Genre
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


class RandomMovieForm(forms.Form):
    """Form to filter and select random movies based on various criteria."""

    # Default "Any" option for genres
    GENRE_CHOICES: List[Tuple[str, str]] = [("", "Any")]

    genre = forms.MultipleChoiceField(
        choices=GENRE_CHOICES,
        required=False,
        widget=forms.SelectMultiple(
            attrs={
                "class": "bg-gray-700 text-gray-200 placeholder-gray-400 border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500"
            }
        ),
    )
    count = forms.ChoiceField(choices=[(i, str(i)) for i in range(1, 5)], initial=1)
    min_rotten_tomatoes_rating = forms.ChoiceField(required=False)
    max_duration = forms.ChoiceField(required=False)
    min_year = forms.ChoiceField(required=False)
    max_year = forms.ChoiceField(required=False)

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Initialize the form, set CSS classes for fields, and populate dynamic choices.

        This method applies consistent Tailwind CSS classes to all fields and
        fetches distinct genres with associated movies to populate the genre field.
        It also sets initial values for fields if data is provided.
        """
        super().__init__(*args, **kwargs)

        # Apply Tailwind CSS classes to all fields
        for field in self.fields.values():
            field.widget.attrs.update(
                {
                    "class": "bg-gray-700 text-gray-200 placeholder-gray-400 border-gray-600 rounded-md focus:ring-blue-500 focus:border-blue-500"
                }
            )

        # Fetch and add genre choices
        logger.info("Fetching genres with associated movies.")
        genres_with_movies = (
            Genre.objects.filter(movies__isnull=False)
            .distinct()
            .order_by("name")
            .values_list("name", flat=True)
        )
        self.fields["genre"].choices += [(genre, genre) for genre in genres_with_movies]

        # Set dynamic choices for other fields
        self.fields["min_rotten_tomatoes_rating"].choices = self.get_rating_choices()
        self.fields["max_duration"].choices = self.get_duration_choices()
        self.fields["min_year"].choices = self.get_year_choices()
        self.fields["max_year"].choices = self.get_year_choices()

        # Set initial values if data is provided
        if self.data and "reset" not in self.data:
            for field in self.fields:
                if field in self.data:
                    if field == "genre":
                        value = (
                            self.data.get(field)
                            if isinstance(self.data, dict)
                            else self.data.getlist(field)
                        )
                        self.fields[field].initial = (
                            value if isinstance(value, list) else [value]
                        )
                    else:
                        self.fields[field].initial = self.data.get(field)

    def clean_min_rotten_tomatoes_rating(self) -> Optional[float]:
        """Validate and return the minimum Rotten Tomatoes rating as a float."""
        value = self.cleaned_data.get("min_rotten_tomatoes_rating")
        return float(value) if value else None

    def clean_max_duration(self) -> Optional[int]:
        """Validate and return the maximum duration as an integer (in minutes)."""
        value = self.cleaned_data.get("max_duration")
        return int(value) if value else None

    def get_duration_choices(self) -> List[Tuple[Optional[int], str]]:
        """Generate a list of duration choices based on available movies."""
        durations = Movie.objects.aggregate(
            min_duration=Min("duration"), max_duration=Max("duration")
        )
        logger.debug(f"Movie durations: {durations}")

        min_duration = (durations["min_duration"] or 0) // 60000
        max_duration = (durations["max_duration"] or 0) // 60000

        choices = [("", "Any")]
        for hours in range(0, (max_duration // 60) + 1):  # Up to the maximum hours
            for minutes in range(0, 60, 30):  # Every 30 minutes
                total_minutes = hours * 60 + minutes
                if total_minutes < min_duration or total_minutes > max_duration:
                    continue  # Skip if not in range

                if min_duration <= total_minutes <= max_duration:
                    label = (
                        f"{hours}h {minutes}m"
                        if hours and minutes
                        else f"{hours}h" if hours else f"{minutes}m"
                    )
                    choices.append((total_minutes, label))
        return choices

    def get_rating_choices(self) -> List[Tuple[Optional[float], str]]:
        """Generate a list of rating choices based on available movies."""
        ratings = Movie.objects.aggregate(
            min_rating=Min("rotten_tomatoes_rating"),
            max_rating=Max("rotten_tomatoes_rating"),
        )
        logger.debug(f"Movie ratings: {ratings}")

        # Handle None values for min and max ratings
        min_rating = ratings["min_rating"] or 0
        max_rating = ratings["max_rating"] or 100

        choices = [("", "Any")]
        for rating in range(int(min_rating), int(max_rating) + 1, 10):
            choices.append((float(rating), f"{rating}%"))
        return choices

    def clean_min_year(self) -> Optional[int]:
        """Validate and return the minimum year as an integer."""
        value = self.cleaned_data.get("min_year")
        return int(value) if value else None

    def clean_max_year(self) -> Optional[int]:
        """Validate and return the maximum year as an integer."""
        value = self.cleaned_data.get("max_year")
        return int(value) if value else None

    def get_year_choices(self) -> List[Tuple[Optional[int], str]]:
        """Generate a list of year choices based on available movies."""
        years = Movie.objects.aggregate(
            min_year=Min("year"),
            max_year=Max("year"),
        )
        logger.debug(f"Movie years: {years}")

        min_year = years["min_year"] or 1888
        max_year = years["max_year"] or datetime.now().year

        choices = [("", "Any")]
        for year in range(min_year, max_year + 1):
            choices.append((year, str(year)))
        return choices

    def is_reset(self) -> bool:
        """Check if the form data contains a reset action."""
        return "reset" in self.data
