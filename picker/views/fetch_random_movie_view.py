from typing import List

from django.db.models import Q, QuerySet
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from sync.models import Movie
from utils.logger_utils import setup_logging
from utils.trailer_utils import get_tmdb_trailer_url, get_youtube_trailer_url

logger = setup_logging(__name__)


def get_unique_genres() -> List[str]:
    # Retrieve distinct genres from the Movie model and return a sorted list
    genres = Movie.objects.values_list("genres", flat=True).distinct()
    unique_genres = sorted(
        set(genre.strip() for genre in ",".join(genres).split(",") if genre.strip())
    )
    logger.debug(f"Unique genres: {unique_genres}")
    return unique_genres


def get_filtered_movies(genre: str) -> Q:
    # Construct a query to filter movies by genre, or return an empty query if no genre is specified
    query = Q(genres__icontains=genre) if genre else Q()
    logger.debug(f"Filter query: {query}")
    return query


def get_random_movies(queryset: QuerySet, count: int) -> List[Movie]:
    # Select a random subset of movies from the given queryset
    movies = list(queryset.order_by("?")[:count])
    logger.debug(f"Random movies selected: {[m.title for m in movies]}")
    return movies


def fetch_trailer_url(movie: Movie) -> str:
    # Fetch and save the trailer URL for a movie if it doesn't already exist
    if not movie.trailer_url:
        movie.trailer_url = get_tmdb_trailer_url(
            movie.tmdb_id
        ) or get_youtube_trailer_url(movie.title)
        movie.save(update_fields=["trailer_url"])
    logger.debug(f"Trailer URL for {movie.title}: {movie.trailer_url}")
    return movie.trailer_url


def fetch_random_movie(request):
    try:
        # Extract query parameters from the request
        selected_genre = request.GET.get("genre", "")
        count = int(request.GET.get("count", 1))
        randomize = request.GET.get("randomize", "").lower() == "true"
        movie_ids = request.GET.get("movies", "")

        logger.debug(
            f"Input parameters: genre={selected_genre}, count={count}, randomize={randomize}, movie_ids={movie_ids}"
        )

        # Retrieve the list of unique genres
        genres = get_unique_genres()

        if randomize or not movie_ids:
            # If randomizing or no movie IDs provided, filter and select movies
            movies = Movie.objects.filter(get_filtered_movies(selected_genre))
            logger.debug(f"Number of movies after filtering: {movies.count()}")

            if movies.exists():
                # Ensure the requested count does not exceed the available movies
                count = max(1, min(count, 3))
                selected_movies = get_random_movies(movies, count)
                movie_ids = ",".join(str(movie.id) for movie in selected_movies)
                logger.debug(f"Selected movie IDs: {movie_ids}")

                # Redirect to the same view with selected movie IDs in the URL
                return HttpResponseRedirect(
                    f"{reverse('fetch_random_movie')}?genre={selected_genre}&count={count}&movies={movie_ids}"
                )
            else:
                selected_movies = []
                logger.warning("No movies found matching the criteria")
        else:
            # If movie IDs are provided, retrieve movies from those IDs
            movie_id_list = [int(id) for id in movie_ids.split(",") if id.isdigit()]
            selected_movies = list(Movie.objects.filter(id__in=movie_id_list))
            logger.debug(
                f"Movies retrieved from IDs: {[m.title for m in selected_movies]}"
            )

        # Fetch and save trailer URLs for the selected movies
        for movie in selected_movies:
            fetch_trailer_url(movie)

        # Prepare the context for rendering the template
        context = {
            "movies": selected_movies,
            "genres": genres,
            "selected_genre": selected_genre,
            "count": count,
            "movie_ids": movie_ids,
        }
        return render(request, "random_movie.html", context)

    except Exception as e:
        # Log any exceptions that occur during processing
        logger.error(f"Error fetching random movie: {str(e)}")
        return render(request, "error.html", {"error": str(e)})
