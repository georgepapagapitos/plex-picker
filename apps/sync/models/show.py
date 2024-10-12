# apps/sync/models/show.py

from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models

from apps.sync.models.genre import Genre
from apps.sync.models.mixins import (
    FormattedActorsMixin,
    FormattedDurationMixin,
    FormattedGenresMixin,
    ImageOptimizationMixin,
)
from apps.sync.models.person import Person
from apps.sync.models.studio import Studio


class Show(
    FormattedActorsMixin,
    FormattedDurationMixin,
    FormattedGenresMixin,
    ImageOptimizationMixin,
    models.Model,
):
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True)  # Duration in milliseconds
    poster_url = models.URLField(blank=True, null=True)
    genres = models.ManyToManyField(Genre, related_name="shows")
    plex_key = models.CharField(max_length=255, unique=True)
    tmdb_id = models.PositiveIntegerField(blank=True, null=True)
    rotten_tomatoes_rating = models.FloatField(blank=True, null=True)
    content_rating = models.CharField(max_length=10, blank=True, null=True)
    art = models.URLField(blank=True, null=True)
    trailer_url = models.URLField(blank=True, null=True)
    tagline = models.TextField(null=True, blank=True)
    studio = models.ForeignKey(
        Studio, on_delete=models.SET_NULL, null=True, related_name="shows"
    )
    audience_rating = models.FloatField(null=True, blank=True)
    audience_rating_image = models.CharField(max_length=255, null=True, blank=True)
    originally_available_at = models.DateField(null=True, blank=True)

    # Metadata fields
    added_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    last_viewed_at = models.DateTimeField(null=True, blank=True)
    # TODO: add guid to sync
    guid = models.CharField(max_length=255, null=True, blank=True)

    # Show-specific fields
    episode_sort = models.IntegerField(
        default=-1
    )  # -1: Library default, 0: Oldest first, 1: Newest first
    flatten_seasons = models.IntegerField(
        default=-1
    )  # -1: Library default, 0: Hide, 1: Show
    season_count = models.IntegerField(default=0)
    episode_count = models.IntegerField(default=0)
    view_count = models.IntegerField(default=0)

    # Settings fields
    use_original_title = models.IntegerField(
        default=-1
    )  # -1: Library default, 0: No, 1: Yes
    enable_credits_marker_generation = models.IntegerField(
        default=-1
    )  # -1: Library default, 0: Disabled

    class Meta:
        ordering = ["title"]
        verbose_name = "Show"
        verbose_name_plural = "Shows"
        indexes = [
            models.Index(fields=["year"]),
            models.Index(fields=["tmdb_id"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.year})"

    def get_roles_by_type(self, role_type):
        return self.roles.filter(role_type=role_type).select_related("person")

    def get_actors(self):
        return self.get_roles_by_type("ACTOR")

    def get_directors(self):
        return self.get_roles_by_type("DIRECTOR")

    def get_producers(self):
        return self.get_roles_by_type("PRODUCER")

    def get_writers(self):
        return self.get_roles_by_type("WRITER")

    def get_people_by_role(self, role_type):
        return Person.objects.filter(roles__show=self, roles__role_type=role_type)

    def get_cast(self):
        return self.get_people_by_role("ACTOR")

    def clean(self):
        current_year = datetime.now().year
        if self.year and (self.year < 1888 or self.year > current_year):
            raise ValidationError("Year must be between 1888 and the current year.")
        if self.rotten_tomatoes_rating is not None and not (
            0 <= self.rotten_tomatoes_rating <= 100
        ):
            raise ValidationError("Rating must be between 0 and 100.")

    @property
    def type(self):
        return "show"

    @property
    def is_played(self):
        return self.view_count > 0 and self.view_count == self.episode_count
