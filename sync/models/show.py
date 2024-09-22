# sync/models/show.py

from django.db import models


class Show(models.Model):
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True)
    poster_url = models.URLField(blank=True, null=True)
    genres = models.CharField(max_length=255, blank=True, null=True)
    plex_key = models.IntegerField(unique=True)
    tmdb_id = models.IntegerField(blank=True, null=True)
    rotten_tomatoes_rating = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} ({self.year})"
