# sync/models/mixins.py

import os
from io import BytesIO

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image

from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


class FormattedDurationMixin:
    def formatted_duration(self):
        if self.duration is None:
            return "N/A"
        total_minutes = self.duration // (1000 * 60)  # Convert milliseconds to minutes
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"


class FormattedActorsMixin:
    def formatted_actors(self, limit=None):
        actor_roles = (
            self.roles.filter(role_type="ACTOR")
            .select_related("person")
            .order_by("person__last_name", "person__first_name")
        )
        if limit:
            actor_roles = actor_roles[:limit]
        if not actor_roles:
            return "No cast information available"

        def format_actor_name(role):
            person = role.person
            name = f"{person.first_name} {person.last_name}".strip() or "Unknown Actor"
            if role.character_name:
                return f"{name} as {role.character_name}"
            return name

        return ", ".join(format_actor_name(role) for role in actor_roles)


class FormattedGenresMixin:
    def formatted_genres(self):
        return ", ".join(genre.name for genre in self.genres.all())


class ImageOptimizationMixin(models.Model):
    optimized_poster = models.ImageField(
        upload_to="optimized_posters/", blank=True, null=True
    )
    optimized_art = models.ImageField(upload_to="optimized_art/", blank=True, null=True)
    _optimizing = False  # Flag to prevent recursive optimization
    _logged_optimized_images = set()  # Track logged image statuses

    class Meta:
        abstract = True

    @staticmethod
    def optimize_image(image_url, size):
        if not image_url:
            return None
        try:
            if image_url.startswith("http"):
                response = requests.get(image_url)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content))
            else:
                img_path = os.path.join(settings.MEDIA_ROOT, image_url)
                img = Image.open(img_path)

            img.thumbnail(size)
            img_io = BytesIO()
            img.save(img_io, format="WEBP", quality=85)
            return ContentFile(img_io.getvalue())
        except (requests.RequestException, IOError, OSError) as e:
            logger.error(f"Error optimizing image {image_url}: {str(e)}")
            return None

    def optimize_images(self):
        if self._optimizing:
            logger.debug(f"Skipping optimization for {self.pk} to prevent recursion.")
            return

        self._optimizing = True
        logger.info(
            f"Starting optimization for {self.pk}"
        )  # Log when optimization starts
        try:
            # Optimize poster
            if self.optimized_poster:  # Check if optimized poster already exists
                logger.info(f"Optimized poster already exists for {self.pk}")
            elif hasattr(self, "poster_url"):
                poster_content = self.optimize_image(self.poster_url, (300, 450))
                if poster_content:
                    self.optimized_poster.save(
                        f"{self.id}_poster.webp", poster_content, save=False
                    )
                    logger.info(
                        f"Successfully optimized and saved poster for {self.pk}"
                    )

            # Optimize art
            if self.optimized_art:  # Check if optimized art already exists
                logger.info(f"Optimized art already exists for {self.pk}")
            elif hasattr(self, "art"):
                art_content = self.optimize_image(self.art, (1280, 720))
                if art_content:
                    self.optimized_art.save(
                        f"{self.id}_art.webp", art_content, save=False
                    )
                    logger.info(f"Successfully optimized and saved art for {self.pk}")

            # Save if any images were optimized
            if self.optimized_poster or self.optimized_art:
                logger.debug(f"Saving optimized images for {self.pk}")
                super().save(
                    update_fields=["optimized_poster", "optimized_art"]
                )  # Save only the fields that were changed
        except Exception as e:
            logger.error(f"Error during image optimization for {self.pk}: {str(e)}")
        finally:
            self._optimizing = False
            logger.info(
                f"Finished optimization for {self.pk}"
            )  # Log when optimization finishes

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self._optimizing:
            self.optimize_images()


@receiver(post_save, sender="sync.Movie")
@receiver(post_save, sender="sync.Show")
def optimize_media_images(sender, instance, created, **kwargs):
    instance.optimize_images()
