from typing import List

from sync.models.genre import Genre
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


def get_or_create_genres(genre_names: str) -> List[Genre]:
    """
    Fetches or creates Genre instances from a comma-separated string of genre names.

    Args:
        genre_names (str): A comma-separated string of genre names.

    Returns:
        List[Genre]: A list of Genre instances.
    """
    logger.debug("Processing genres for creation/updating.")

    # Split the input string by commas, remove extra whitespace, and filter out empty strings
    genre_list = [g.strip() for g in genre_names.split(",") if g.strip()]

    genre_objects = []
    for genre_name in genre_list:
        # Get or create the genre, ensuring no duplicates are created
        genre, created = Genre.objects.get_or_create(name=genre_name)
        genre_objects.append(genre)

        if created:
            logger.info(f"Created new genre: {genre_name}")
        else:
            logger.debug(f"Genre already exists: {genre_name}")

    logger.debug(f"Genre objects created or fetched: {genre_objects}")
    return genre_objects
