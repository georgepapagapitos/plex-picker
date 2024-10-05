# picker/views/show_detail_view.py

from typing import Any, Dict

from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render

from sync.models.show import Show
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


def show_detail_view(request: HttpRequest, show_id: int) -> HttpResponse:
    try:
        show: Show = get_object_or_404(Show, pk=show_id)

        context: Dict[str, Any] = {
            "media": show,
            "formatted_actors": show.formatted_actors(limit=5),
        }

        return render(request, "show_detail.html", context)

    except Exception as e:
        logger.error(f"Error fetching show with ID {show_id}: {e}")
        return render(
            request,
            "error.html",
            {
                "error_code": 404,
                "error_message": "The requested TV show was not found.",
            },
        )
