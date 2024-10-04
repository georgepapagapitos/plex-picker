# picker/views/plex_content_view.py

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET

from picker.forms.search_form import SearchForm
from sync.models import Movie, Show
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


@require_GET
def plex_content_view(request: HttpRequest) -> HttpResponse:
    try:
        search_form = SearchForm(request.GET or None)
        movies = Movie.objects.all()
        shows = Show.objects.all()

        if search_form.is_valid() and search_form.cleaned_data["query"].strip():
            query = search_form.cleaned_data["query"]
            query_parts = query.split()

            title_query = Q(title__icontains=query)
            actor_query = Q()

            if len(query_parts) > 1:
                actor_query |= Q(actors__first_name__icontains=query_parts[0]) & Q(
                    actors__last_name__icontains=query_parts[-1]
                )

            for part in query_parts:
                actor_query |= Q(actors__first_name__icontains=part) | Q(
                    actors__last_name__icontains=part
                )

            combined_query = title_query | actor_query

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

        context = {
            "movies_page": movies_page,
            "shows_page": shows_page,
            "search_form": search_form,
        }

        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            response_data = {
                "movies": [
                    {"id": movie.id, "title": movie.title, "year": movie.year}
                    for movie in movies_page
                ],
                "shows": [
                    {"id": show.id, "title": show.title, "year": show.year}
                    for show in shows_page
                ],
                "movie_page": movies_page.number,
                "show_page": shows_page.number,
                "movie_total_pages": movie_paginator.num_pages,
                "show_total_pages": show_paginator.num_pages,
                "query": search_form.data.get("query", ""),
            }
            return JsonResponse(response_data)

        return render(request, "plex_content/plex_content.html", context)

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return render(
            request,
            "error.html",
            {
                "error_code": "Unexpected Error",
                "error_message": "An unexpected error occurred. Please try again later.",
            },
        )
