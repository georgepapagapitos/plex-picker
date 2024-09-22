# picker/helpers/random_movie_helpers.py

from typing import List

from django.db.models import Q

from sync.models import Movie
from utils.logger_utils import setup_logging
from utils.trailer_utils import get_tmdb_trailer_url, get_youtube_trailer_url

logger = setup_logging(__name__)


def get_unique_genres() -> List[str]:
    genres = Movie.objects.values_list("genres", flat=True).distinct()
    unique_genres = sorted(
        set(genre.strip() for genre in ",".join(genres).split(",") if genre.strip())
    )
    logger.debug(f"Unique genres: {unique_genres}")
    return unique_genres


def get_filtered_movies(genre: str) -> Q:
    query = Q(genres__icontains=genre) if genre else Q()
    logger.debug(f"Filter query: {query}")
    return query


def get_random_movies(queryset, count: int) -> List[Movie]:
    movies = list(queryset.order_by("?")[:count])
    logger.debug(f"Random movies selected: {[m.title for m in movies]}")
    return movies


def fetch_trailer_url(movie: Movie) -> str:
    if not movie.trailer_url:
        movie.trailer_url = get_tmdb_trailer_url(
            movie.tmdb_id
        ) or get_youtube_trailer_url(movie.title)
        movie.save(update_fields=["trailer_url"])
    logger.debug(f"Trailer URL for {movie.title}: {movie.trailer_url}")
    return movie.trailer_url
