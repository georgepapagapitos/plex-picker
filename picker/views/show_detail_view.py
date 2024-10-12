# picker/views/show_detail_view.py

from typing import Any, Dict

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.generic import DetailView

from sync.models.show import Show
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


class ShowDetailView(DetailView):
    model = Show
    template_name = "show_detail.html"
    context_object_name = "media"
    pk_url_kwarg = "show_id"

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["formatted_actors"] = self.object.formatted_actors(limit=5)
        return context

    def render_to_response(
        self, context: Dict[str, Any], **response_kwargs: Any
    ) -> HttpResponse:
        try:
            return super().render_to_response(context, **response_kwargs)
        except Exception as e:
            logger.error(
                f"Error fetching show with ID {self.kwargs.get(self.pk_url_kwarg)}: {e}"
            )
            return render(
                self.request,
                "error.html",
                {
                    "error_code": 404,
                    "error_message": "The requested TV show was not found.",
                },
            )

    def dispatch(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
        try:
            return super().dispatch(request, *args, **kwargs)
        except Exception as e:
            logger.error(
                f"Error in dispatch for show with ID {kwargs.get(self.pk_url_kwarg)}: {e}"
            )
            return render(
                request,
                "error.html",
                {
                    "error_code": 404,
                    "error_message": "The requested TV show was not found.",
                },
            )
