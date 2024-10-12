# sync/models/movie.py

from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import models

from sync.models.genre import Genre
from sync.models.mixins import (
    FormattedActorsMixin,
    FormattedDurationMixin,
    FormattedGenresMixin,
    ImageOptimizationMixin,
)
from sync.models.person import Person
from sync.models.studio import Studio


class Movie(
    FormattedActorsMixin,
    FormattedDurationMixin,
    FormattedGenresMixin,
    ImageOptimizationMixin,
    models.Model,
):
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
    art = models.URLField(null=True, blank=True)
    tagline = models.TextField(null=True, blank=True)
    studio = models.ForeignKey(
        Studio, on_delete=models.SET_NULL, null=True, related_name="movies"
    )
    audience_rating = models.FloatField(null=True, blank=True)
    audience_rating_image = models.CharField(max_length=255, null=True, blank=True)
    chapter_source = models.CharField(max_length=50, null=True, blank=True)
    edition_title = models.CharField(max_length=255, null=True, blank=True)
    original_title = models.CharField(max_length=255, null=True, blank=True)
    originally_available_at = models.DateField(null=True, blank=True)
    rating_image = models.CharField(max_length=255, null=True, blank=True)
    view_count = models.IntegerField(default=0)
    tmdb_url = models.URLField(null=True, blank=True)
    trakt_url = models.URLField(null=True, blank=True)
    imdb_url = models.URLField(null=True, blank=True)

    # Metadata fields
    added_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    last_viewed_at = models.DateTimeField(null=True, blank=True)
    # TODO: add guid to sync
    guid = models.CharField(max_length=255, null=True, blank=True)

    # Settings fields
    use_original_title = models.IntegerField(
        default=-1
    )  # -1: Library default, 0: No, 1: Yes
    enable_credits_marker_generation = models.IntegerField(
        default=-1
    )  # -1: Library default, 0: Disabled

    class Meta:
        ordering = ["title"]
        verbose_name = "Movie"
        verbose_name_plural = "Movies"
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
        return Person.objects.filter(roles__movie=self, roles__role_type=role_type)

    def get_cast(self):
        return self.get_people_by_role("ACTOR")

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

    @property
    def has_credits_marker(self):
        return self.enable_credits_marker_generation == 1

    @property
    def locations(self):
        return [media.file for media in self.media_set.all()]
