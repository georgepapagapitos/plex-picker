# sync/models/actor.py
from django.db import models


class Actor(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    photo_url = models.URLField(blank=True, null=True)
    tmdb_id = models.PositiveIntegerField(blank=True, null=True, unique=True)
    shows = models.ManyToManyField("Show", related_name="actors", blank=True)
    movies = models.ManyToManyField("Movie", related_name="actors", blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["tmdb_id"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
