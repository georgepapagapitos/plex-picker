# fetch_plex_content_view.py
from typing import Any, Dict

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from sync.models import Movie
from sync.models.show import Show
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


def fetch_plex_content(request: HttpRequest) -> HttpResponse:
    """
    Fetches content from the local database and renders it in a template.

    Args:
        request: The HTTP request object.

    Returns:
        Rendered HTML response with movie and TV show data, or an error page.
    """

    try:
        # Fetch all movies and TV shows from the local database
        movies = Movie.objects.all()
        shows = Show.objects.all()

        # Create context dictionary to pass data to the template
        context: Dict[str, Any] = {"movies": movies, "shows": shows}

        # Render the 'plex_content.html' template with the fetched context
        return render(request, "plex_content.html", context)

    except Exception as e:
        # Log any errors that occur
        logger.error(f"Unexpected error: {e}")
        # Render the error template for unexpected errors
        return render(
            request,
            "error.html",
            {
                "error_code": "Unexpected Error",
                "error_message": "An unexpected error occurred. Please try again later.",
            },
        )
