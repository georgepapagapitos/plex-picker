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
        # Create an instance of SearchForm
        search_form = SearchForm(request.GET or None)

        # Fetch all movies and TV shows from the local database
        movies = Movie.objects.all()
        shows = Show.objects.all()

        # Apply search filter if the form is valid and the query is not empty
        if search_form.is_valid() and search_form.cleaned_data["query"].strip():
            query = search_form.cleaned_data["query"]
            query_parts = query.split()

            # Create Q objects for various search conditions
            title_query = Q(title__icontains=query)
            actor_query = Q()

            # Handle full name and partial name searches
            if len(query_parts) > 1:
                # For multi-word queries, search for full name matches
                actor_query |= Q(actors__first_name__icontains=query_parts[0]) & Q(
                    actors__last_name__icontains=query_parts[-1]
                )

            # Always include partial name matches
            for part in query_parts:
                actor_query |= Q(actors__first_name__icontains=part) | Q(
                    actors__last_name__icontains=part
                )

            # Combine title and actor queries
            combined_query = title_query | actor_query

            movies = movies.filter(combined_query).distinct()
            shows = shows.filter(combined_query).distinct()

        movies = movies.order_by("title")
        shows = shows.order_by("title")

        # Set default page sizes
        movies_per_page = 20
        shows_per_page = 20

        # Pagination
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

        # Create context dictionary to pass data to the template
        context = {
            "movies_page": movies_page,
            "shows_page": shows_page,
            "search_form": search_form,
        }

        # Check if the request is an AJAX request
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

        # Render the 'plex_content.html' template with the fetched context
        return render(request, "plex_content.html", context)

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
