# sync/models/role.py

from django.db import models


class Role(models.Model):
    ROLE_TYPES = [
        ("ACTOR", "Actor"),
        ("DIRECTOR", "Director"),
        ("PRODUCER", "Producer"),
        ("WRITER", "Writer"),
        ("CINEMATOGRAPHER", "Cinematographer"),
        ("COMPOSER", "Composer"),
        ("EDITOR", "Editor"),
        ("OTHER", "Other"),
    ]

    person = models.ForeignKey("Person", on_delete=models.CASCADE, related_name="roles")
    role_type = models.CharField(max_length=20, choices=ROLE_TYPES)
    movie = models.ForeignKey(
        "Movie", on_delete=models.CASCADE, null=True, blank=True, related_name="roles"
    )
    show = models.ForeignKey(
        "Show", on_delete=models.CASCADE, null=True, blank=True, related_name="roles"
    )
    episode = models.ForeignKey(
        "Episode", on_delete=models.CASCADE, null=True, blank=True, related_name="roles"
    )
    character_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=["role_type"]),
        ]

    def __str__(self):
        media = self.movie or self.show or self.episode
        role_info = f"{self.get_role_type_display()}"
        if self.role_type == "ACTOR" and self.character_name:
            role_info += f" as {self.character_name}"
        return f"{self.person} - {role_info} in {media}"

    def get_media_type(self):
        if self.movie:
            return "Movie"
        elif self.show:
            return "Show"
        elif self.episode:
            return "Episode"
        return "Unknown"
