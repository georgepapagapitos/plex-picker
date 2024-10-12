# sync/models/mixins.py

import os
from io import BytesIO
from typing import Optional, Tuple

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image

from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


class FormattedDurationMixin:
    def formatted_duration(self) -> str:
        """
        Format the duration in milliseconds to a human-readable string.

        Returns:
            str: Formatted duration string (e.g., "2h 30m" or "45m")
        """
        if self.duration is None:
            return "N/A"
        total_minutes = self.duration // (1000 * 60)  # Convert milliseconds to minutes
        hours, minutes = divmod(total_minutes, 60)
        return f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m"


class FormattedActorsMixin:
    def formatted_actors(self, limit: Optional[int] = None) -> str:
        """
        Format a list of actors with their character names.

        Args:
            limit (Optional[int]): Maximum number of actors to include

        Returns:
            str: Formatted string of actors and their roles
        """
        actor_roles = (
            self.roles.filter(role_type="ACTOR")
            .select_related("person")
            .order_by("order", "id")
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
    def formatted_genres(self) -> str:
        """
        Format a list of genres as a comma-separated string.

        Returns:
            str: Comma-separated list of genre names
        """
        return ", ".join(genre.name for genre in self.genres.all())


class ImageOptimizationMixin(models.Model):
    optimized_poster = models.ImageField(
        upload_to="optimized_posters/", blank=True, null=True
    )
    optimized_art = models.ImageField(upload_to="optimized_art/", blank=True, null=True)
    _optimizing = False  # Flag to prevent recursive optimization

    class Meta:
        abstract = True

    @staticmethod
    def optimize_image(image_url: str, size: Tuple[int, int]) -> Optional[ContentFile]:
        """
        Optimize an image by resizing and converting to WebP format.

        Args:
            image_url (str): URL or file path of the image to optimize
            size (Tuple[int, int]): Desired dimensions (width, height)

        Returns:
            Optional[ContentFile]: Optimized image content or None if optimization fails
        """
        if not image_url:
            logger.warning("No image URL provided for optimization")
            return None
        try:
            if image_url.startswith("http"):
                response = requests.get(image_url, timeout=10)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content))
            else:
                img_path = os.path.join(settings.MEDIA_ROOT, image_url)
                if not os.path.exists(img_path):
                    raise FileNotFoundError(f"Image file not found: {img_path}")
                img = Image.open(img_path)

            img.thumbnail(size)
            img_io = BytesIO()
            img.save(img_io, format="WEBP", quality=85)
            return ContentFile(img_io.getvalue())
        except (requests.RequestException, IOError, OSError) as e:
            logger.error(f"Error optimizing image {image_url}: {str(e)}")
            return None

    def optimize_images(self):
        """
        Optimize poster and art images for the model instance.
        """
        if self._optimizing:
            logger.debug(f"Skipping optimization for {self.pk} to prevent recursion.")
            return

        self._optimizing = True
        logger.info(f"Starting optimization for {self.pk}")
        try:
            if hasattr(self, "poster_url"):
                poster_content = self.optimize_image(self.poster_url, (300, 450))
                if poster_content:
                    if self.optimized_poster:
                        self.optimized_poster.delete(save=False)
                    self.optimized_poster.save(
                        f"{self.pk}_poster.webp", poster_content, save=False
                    )
                    logger.info(
                        f"Successfully optimized and saved poster for {self.pk}"
                    )

            if hasattr(self, "art"):
                art_content = self.optimize_image(self.art, (1280, 720))
                if art_content:
                    if self.optimized_art:
                        self.optimized_art.delete(save=False)
                    self.optimized_art.save(
                        f"{self.pk}_art.webp", art_content, save=False
                    )
                    logger.info(
                        f"Successfully optimized and saved art for {self.__class__.__name__} {self.pk}"
                    )
                else:
                    logger.warning(
                        f"Failed to optimize art for {self.__class__.__name__} {self.pk}"
                    )

            # Save the changes
            super().save(update_fields=["optimized_poster", "optimized_art"])
            logger.info(f"Saved optimized images for {self.pk}")
        except Exception as e:
            logger.error(f"Error during image optimization for {self.pk}: {str(e)}")
        finally:
            self._optimizing = False
            logger.info(f"Finished optimization for {self.pk}")

    def save(self, *args, **kwargs):
        """
        Override the save method to perform image optimization after saving.
        """
        try:
            super().save(*args, **kwargs)
            if not self._optimizing:
                self.optimize_images()
        except Exception as e:
            logger.error(f"Error saving {self.__class__.__name__} {self.pk}: {str(e)}")
            raise

    def clean(self):
        """
        Perform model validation before saving.
        """
        super().clean()
        if hasattr(self, "poster_url") and not self.poster_url:
            raise ValidationError({"poster_url": "Poster URL is required."})
        if hasattr(self, "art") and not self.art:
            raise ValidationError({"art": "Art image is required."})


@receiver(post_save, sender="sync.Movie")
@receiver(post_save, sender="sync.Show")
def optimize_media_images(sender, instance, created, **kwargs):
    """
    Signal receiver to optimize images after saving Movie or Show instances.
    """
    try:
        instance.optimize_images()
    except Exception as e:
        logger.error(
            f"Error optimizing images for {sender.__name__} {instance.pk}: {str(e)}"
        )
