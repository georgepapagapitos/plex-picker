# picker/helpers/movie_helpers.py

from typing import List

from django.db.models import Q

from sync.models import Movie
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


def get_filtered_movies(genre: str) -> Q:
    logger.debug(f"Creating filter query for genre: {genre}")
    query = Q(genres__name=genre) if genre else Q()
    logger.debug(f"Filter query created: {query}")
    return query


def get_random_movies(queryset, count: int) -> List[Movie]:
    logger.debug(f"Selecting {count} random movies from the queryset.")
    movies = list(queryset.order_by("?")[:count])
    logger.debug(f"Random movies selected: {[m.title for m in movies]}")
    return movies
