# sync/models/episode.py

from django.db import models

from sync.models.show import Show


class Episode(models.Model):
    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name="episodes")
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True, null=True)
    season_number = models.IntegerField()
    episode_number = models.IntegerField()
    duration = models.IntegerField(blank=True, null=True)  # Duration in milliseconds
    plex_key = models.IntegerField(unique=True)
    tmdb_id = models.IntegerField(blank=True, null=True)
    rotten_tomatoes_rating = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.show.title} - S{self.season_number}E{self.episode_number}: {self.title}"
