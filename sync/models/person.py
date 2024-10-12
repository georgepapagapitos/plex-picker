# sync/models/person.py

from django.db import models


class Person(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    photo_url = models.URLField(blank=True, null=True)
    tmdb_id = models.PositiveIntegerField(blank=True, null=True, unique=True)
    imdb_id = models.CharField(max_length=20, blank=True, null=True, unique=True)
    tvdb_id = models.PositiveIntegerField(blank=True, null=True, unique=True)
    birth_date = models.DateField(null=True, blank=True)
    death_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["last_name", "first_name"]
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["tmdb_id"]),
            models.Index(fields=["imdb_id"]),
            models.Index(fields=["tvdb_id"]),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
