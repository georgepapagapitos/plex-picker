# sync/models/episode.py

from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models

from sync.models.show import Show


class Episode(models.Model):
    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name="episodes")
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True, null=True)
    season_number = models.IntegerField()
    episode_number = models.IntegerField()
    duration = models.IntegerField(blank=True, null=True)
    plex_key = models.IntegerField(unique=True)
    tmdb_id = models.IntegerField(blank=True, null=True)
    rotten_tomatoes_rating = models.FloatField(blank=True, null=True)

    class Meta:
        ordering = ["show", "season_number", "episode_number"]
        unique_together = ("show", "season_number", "episode_number")

    def __str__(self):
        return f"{self.show.title} - S{self.season_number:02}E{self.episode_number:02}: {self.title}"

    def formatted_duration(self):
        """Formats the duration in hours and minutes."""
        if self.duration is None:
            return "N/A"

        # Convert milliseconds to total minutes
        total_minutes = self.duration // (1000 * 60)  # Convert to minutes
        hours, minutes = divmod(total_minutes, 60)

        return f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"

    def clean(self):
        """Custom validation to ensure data integrity."""
        if self.rotten_tomatoes_rating and not (
            0 <= self.rotten_tomatoes_rating <= 100
        ):
            raise ValidationError("Rating must be between 0 and 100.")
        if self.season_number < 1:
            raise ValidationError("Season number must be greater than 0.")
        if self.episode_number < 1:
            raise ValidationError("Episode number must be greater than 0.")
