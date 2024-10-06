# sync/models/episode.py


from django.core.exceptions import ValidationError
from django.db import models

from sync.models.mixins import FormattedActorsMixin, FormattedDurationMixin
from sync.models.person import Person
from sync.models.show import Show


class Episode(
    FormattedActorsMixin,
    FormattedDurationMixin,
    models.Model,
):
    show = models.ForeignKey(Show, on_delete=models.CASCADE, related_name="episodes")
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True, null=True)
    season_number = models.IntegerField()
    episode_number = models.IntegerField()
    duration = models.IntegerField(blank=True, null=True)
    plex_key = models.IntegerField(unique=True)
    tmdb_id = models.IntegerField(blank=True, null=True)
    rotten_tomatoes_rating = models.FloatField(blank=True, null=True)
    audience_rating = models.FloatField(null=True, blank=True)
    audience_rating_image = models.CharField(max_length=255, null=True, blank=True)
    originally_available_at = models.DateField(null=True, blank=True)

    # Metadata fields
    added_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)
    last_viewed_at = models.DateTimeField(null=True, blank=True)
    # TODO: add guid to sync
    guid = models.CharField(max_length=255, null=True, blank=True)

    # Episode-specific fields
    absolute_index = models.IntegerField(
        null=True, blank=True
    )  # Absolute episode number
    view_count = models.IntegerField(default=0)

    # Marker flags
    has_commercial_marker = models.BooleanField(default=False)
    has_intro_marker = models.BooleanField(default=False)
    has_credits_marker = models.BooleanField(default=False)

    class Meta:
        ordering = ["show", "season_number", "episode_number"]
        unique_together = ("show", "season_number", "episode_number")

    def __str__(self):
        return f"{self.show.title} - S{self.season_number:02}E{self.episode_number:02}: {self.title}"

    def get_roles_by_type(self, role_type):
        return self.roles.filter(role_type=role_type).select_related("person")

    def get_actors(self):
        return self.get_roles_by_type("ACTOR")

    def get_directors(self):
        return self.get_roles_by_type("DIRECTOR")

    def get_writers(self):
        return self.get_roles_by_type("WRITER")

    def get_people_by_role(self, role_type):
        return Person.objects.filter(roles__episode=self, roles__role_type=role_type)

    def get_cast(self):
        return self.get_people_by_role("ACTOR")

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

    @property
    def season_episode(self):
        return f"S{self.season_number:02d}E{self.episode_number:02d}"

    @property
    def locations(self):
        return [media.file for media in self.media_set.all()]
