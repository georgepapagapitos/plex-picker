# sync/models/studio.py

from django.db import models


class Studio(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Studio"
        verbose_name_plural = "Studios"

    def __str__(self):
        return self.name
