# picker/helpers/random_movie_helpers.py

from typing import List

from django.db.models import Q

from sync.models import Movie
from utils.logger_utils import setup_logging
from utils.trailer_utils import get_tmdb_trailer_url, get_youtube_trailer_url

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


def get_filtered_movies(genre: str) -> Q:
    logger.debug(f"Creating filter query for genre: {genre}")
    query = Q(genres__icontains=genre) if genre else Q()
    logger.debug(f"Filter query created: {query}")
    return query


def get_random_movies(queryset, count: int) -> List[Movie]:
    logger.debug(f"Selecting {count} random movies from the queryset.")
    movies = list(queryset.order_by("?")[:count])
    logger.debug(f"Random movies selected: {[m.title for m in movies]}")
    return movies


def fetch_trailer_url(movie: Movie) -> str:
    if not movie.trailer_url:
        logger.debug(
            f"Fetching trailer URL for {movie.title} (TMDB ID: {movie.tmdb_id})"
        )
        movie.trailer_url = get_tmdb_trailer_url(
            movie.tmdb_id
        ) or get_youtube_trailer_url(movie.title)
        if movie.trailer_url:
            logger.debug(f"Trailer URL found: {movie.trailer_url}")
        else:
            logger.warning(f"No trailer URL found for {movie.title}.")
        movie.save(update_fields=["trailer_url"])
    else:
        logger.debug(
            f"Existing trailer URL found for {movie.title}: {movie.trailer_url}"
        )
    return movie.trailer_url
