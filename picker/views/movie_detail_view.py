# picker/views/movie_details_view.py

import logging
from typing import Any, Dict

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from sync.models.movie import Movie
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


def movie_detail_view(request: HttpRequest, movie_id: int) -> HttpResponse:
    try:
        movie: Movie = get_object_or_404(Movie, pk=movie_id)

        context: Dict[str, Any] = {
            "movie": movie,
        }

        return render(request, "movie_detail.html", context)

    except Exception as e:
        logger.error(f"Error fetching movie with ID {movie_id}: {e}")
        return render(
            request,
            "error.html",
            {"error_code": 404, "error_message": "The requested movie was not found."},
        )
