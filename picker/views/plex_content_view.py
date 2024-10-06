# picker/views/plex_content_view.py

import json

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.core.serializers import serialize
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET

from picker.forms.search_form import SearchForm
from sync.models import Movie, Show
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


@never_cache
@require_GET
def plex_content_view(request: HttpRequest) -> HttpResponse:
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

        movies_per_page = 10
        shows_per_page = 10
        movie_page_number = request.GET.get("movie_page", 1)
        show_page_number = request.GET.get("show_page", 1)

        movie_paginator = Paginator(movies, movies_per_page)
        show_paginator = Paginator(shows, shows_per_page)

        try:
            movies_page = movie_paginator.page(movie_page_number)
        except PageNotAnInteger:
            movies_page = movie_paginator.page(1)
        except EmptyPage:
            movies_page = movie_paginator.page(movie_paginator.num_pages)

        try:
            shows_page = show_paginator.page(show_page_number)
        except PageNotAnInteger:
            shows_page = show_paginator.page(1)
        except EmptyPage:
            shows_page = show_paginator.page(show_paginator.num_pages)

        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        context = {
            "movies_page": movies_page,
            "shows_page": shows_page,
            "search_form": search_form,
            "movie_total_pages": movie_paginator.num_pages,
            "show_total_pages": show_paginator.num_pages,
        }

        if is_ajax:
            response_data = {
                "movies": json.loads(serialize("json", movies_page)),
                "shows": json.loads(serialize("json", shows_page)),
                "movie_page": movies_page.number,
                "show_page": shows_page.number,
                "movie_total_pages": movie_paginator.num_pages,
                "show_total_pages": show_paginator.num_pages,
                "query": search_form.data.get("query", ""),
            }
            return JsonResponse(response_data)
        else:
            return render(request, "plex_content/plex_content.html", context)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"error": str(e)}, status=500)
        return render(
            request,
            "error.html",
            {
                "error_code": "Unexpected Error",
                "error_message": "An unexpected error occurred. Please try again later.",
            },
        )
