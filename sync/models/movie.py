# sync/models/movie.py

from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models

from sync.models import Genre


class Movie(models.Model):
    class Meta:
        ordering = ["title"]
        verbose_name = "Movie"
        verbose_name_plural = "Movies"
        indexes = [
            models.Index(fields=["year"]),
            models.Index(fields=["tmdb_id"]),
        ]

    title = models.CharField(max_length=255)
    summary = models.TextField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)  # Duration in milliseconds
    poster_url = models.URLField(null=True, blank=True)
    genres = models.ManyToManyField(Genre, related_name="movies")
    plex_key = models.CharField(max_length=255, unique=True)
    trailer_url = models.URLField(null=True, blank=True)
    tmdb_id = models.PositiveIntegerField(null=True, blank=True)
    rotten_tomatoes_rating = models.FloatField(null=True, blank=True)
    content_rating = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.year})"

    def formatted_duration(self):
        if self.duration is None:
            return "N/A"
        # Convert milliseconds to total minutes
        total_minutes = self.duration // (1000 * 60)  # Convert to minutes
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

    def formatted_genres(self):
        return ", ".join(genre.name for genre in self.genres.all())

    def formatted_actors(self, limit=None):
        actors = self.actors.all().order_by("last_name", "first_name")
        if limit:
            actors = actors[:limit]

        if not actors:
            return "No cast information available"

        def format_actor_name(actor):
            if actor.first_name and actor.last_name:
                return f"{actor.first_name} {actor.last_name}"
            elif actor.first_name:
                return actor.first_name
            elif actor.last_name:
                return actor.last_name
            else:
                return "Unknown Actor"

        return ", ".join(format_actor_name(actor) for actor in actors)

    def clean(self):
        current_year = datetime.now().year  # Get the current year
        if self.year and (self.year < 1888 or self.year > current_year):
            raise ValidationError("Year must be between 1888 and the current year.")
        if self.rotten_tomatoes_rating is not None and not (
            0 <= self.rotten_tomatoes_rating <= 100
        ):
            raise ValidationError("Rating must be between 0 and 100.")
        if self.content_rating and len(self.content_rating) > 10:
            raise ValidationError("Content rating must be 10 characters or less.")

    @property
    def type(self):
        return "movie"
