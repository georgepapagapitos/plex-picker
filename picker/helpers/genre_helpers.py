# picker/helpers/genre_helpers.py

from typing import List

from sync.models.movie import Movie
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


def get_unique_genres() -> List[str]:
    logger.debug("Fetching unique genres from the database.")
    genres = Movie.objects.values_list("genres", flat=True).distinct()
    logger.debug(f"Raw genres fetched: {genres}")
    unique_genres = set()

    for genre in genres:
        if genre:
            for g in genre.strip().split(","):
                unique_genres.add(g.strip())

    # Sort and convert to list
    sorted_genres = sorted(unique_genres)

    logger.debug(f"Unique genres sorted: {sorted_genres}")
    return sorted_genres
