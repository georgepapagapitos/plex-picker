# picker/views/plex_content_view.py

import json

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.serializers import serialize
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from picker.forms.search_form import SearchForm
from sync.models import Movie, Show
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


@method_decorator(never_cache, name="dispatch")
@method_decorator(require_GET, name="dispatch")
class PlexContentView(View):
    template_name = "plex_content/plex_content.html"
    error_template_name = "error.html"
    movies_per_page = 10
    shows_per_page = 10

    def get(self, request: HttpRequest) -> HttpResponse:
        try:
            search_form = SearchForm(request.GET or None)
            movies = Movie.objects.all()
            shows = Show.objects.all()

            if search_form.is_valid() and search_form.cleaned_data["query"].strip():
                query = search_form.cleaned_data["query"]
                title_query = Q(title__icontains=query)
                combined_query = title_query
                movies = movies.filter(combined_query).distinct()
                shows = shows.filter(combined_query).distinct()

            movies = movies.order_by("title")
            shows = shows.order_by("title")

            movie_page_number = request.GET.get("movie_page", 1)
            show_page_number = request.GET.get("show_page", 1)

            movie_paginator = Paginator(movies, self.movies_per_page)
            show_paginator = Paginator(shows, self.shows_per_page)

            movies_page = self.get_page(movie_paginator, movie_page_number)
            shows_page = self.get_page(show_paginator, show_page_number)

            context = {
                "movies_page": movies_page,
                "shows_page": shows_page,
                "search_form": search_form,
                "movie_total_pages": movie_paginator.num_pages,
                "show_total_pages": show_paginator.num_pages,
            }

            if self.is_ajax(request):
                return self.render_to_json_response(
                    context, movies_page, shows_page, search_form
                )
            else:
                return render(request, self.template_name, context)

        except Exception as e:
            return self.handle_exception(request, e)

    def get_page(self, paginator, page_number):
        try:
            return paginator.page(page_number)
        except PageNotAnInteger:
            return paginator.page(1)
        except EmptyPage:
            return paginator.page(paginator.num_pages)

    def is_ajax(self, request):
        return request.headers.get("X-Requested-With") == "XMLHttpRequest"

    def render_to_json_response(self, context, movies_page, shows_page, search_form):
        response_data = {
            "movies": json.loads(serialize("json", movies_page)),
            "shows": json.loads(serialize("json", shows_page)),
            "movie_page": movies_page.number,
            "show_page": shows_page.number,
            "movie_total_pages": context["movie_total_pages"],
            "show_total_pages": context["show_total_pages"],
            "query": search_form.data.get("query", ""),
        }
        return JsonResponse(response_data)

    def handle_exception(self, request, exception):
        logger.error(f"Unexpected error: {exception}")
        if self.is_ajax(request):
            return JsonResponse({"error": str(exception)}, status=500)
        return render(
            request,
            self.error_template_name,
            {
                "error_code": "Unexpected Error",
                "error_message": "An unexpected error occurred. Please try again later.",
            },
        )
