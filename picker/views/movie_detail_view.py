# picker/views/movie_detail_view.py

from typing import Any, Dict

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from sync.models.movie import Movie
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


def movie_detail_view(request: HttpRequest, movie_id: int) -> HttpResponse:
    try:
        movie: Movie = get_object_or_404(Movie, pk=movie_id)

        # Capture the parameters for redirection
        random_movies = request.GET.get("movies", "")
        genre = request.GET.get("genre", "")
        count = request.GET.get("count", 1)
        min_rating = request.GET.get("min_rotten_tomatoes_rating", "")
        max_duration = request.GET.get("max_duration", "")

        context: Dict[str, Any] = {
            "media": movie,
            "formatted_actors": movie.formatted_actors(limit=5),
            "random_movies": random_movies,
            "genre": genre,
            "count": count,
            "min_rating": min_rating,
            "max_duration": max_duration,
        }
        return render(request, "movie_detail.html", context)
    except Exception as e:
        logger.error(f"Error fetching movie with ID {movie_id}: {e}")
        return render(
            request,
            "error.html",
            {"error_code": 404, "error_message": "The requested movie was not found."},
        )
