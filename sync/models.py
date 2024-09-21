from django.db import models


class Movie(models.Model):
    title = models.CharField(max_length=255)
    summary = models.TextField(null=True, blank=True)
    year = models.IntegerField(null=True, blank=True)
    duration = models.IntegerField(null=True, blank=True)
    poster_url = models.URLField(null=True, blank=True)
    genres = models.TextField(null=True, blank=True)
    plex_key = models.CharField(max_length=255, unique=True)
    trailer_url = models.URLField(null=True, blank=True)
    tmdb_id = models.PositiveIntegerField(null=True, blank=True)
    rotten_tomatoes_rating = models.FloatField(null=True, blank=True)

    def __str__(self):
        return self.title
