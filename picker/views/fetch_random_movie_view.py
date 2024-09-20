import random
from typing import List

from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from sync.models import Movie
from utils.logger_utils import setup_logging
from utils.trailer_utils import get_tmdb_trailer_url, get_youtube_trailer_url

logger = setup_logging(__name__)


def get_unique_genres() -> List[str]:
    genres = sorted(
        set(
            genre.strip()
            for movie in Movie.objects.all()
            for genre in movie.genres.split(",")
            if genre.strip()
        )
    )
    logger.debug(f"Unique genres: {genres}")
    return genres


def get_filtered_movies(genre: str) -> Q:
    query = Q(genres__icontains=genre) if genre else Q()
    logger.debug(f"Filter query: {query}")
    return query


def get_random_movies(queryset, count: int) -> List[Movie]:
    movies = list(queryset.order_by("?")[:count])
    logger.debug(f"Random movies selected: {[m.title for m in movies]}")
    return movies


def fetch_trailer_url(movie: Movie) -> str:
    if not movie.trailer_url:
        trailer_url = get_tmdb_trailer_url(movie.tmdb_id) or get_youtube_trailer_url(
            movie.title
        )
        movie.trailer_url = trailer_url
        movie.save(update_fields=["trailer_url"])
    logger.debug(f"Trailer URL for {movie.title}: {movie.trailer_url}")
    return movie.trailer_url


def fetch_random_movie(request):
    try:
        selected_genre = request.GET.get("genre", "")
        count = int(request.GET.get("count", 1))
        randomize = request.GET.get("randomize", "").lower() == "true"
        movie_ids = request.GET.get("movies", "")

        logger.debug(
            f"Input parameters: genre={selected_genre}, count={count}, randomize={randomize}, movie_ids={movie_ids}"
        )

        genres = get_unique_genres()

        if randomize or not movie_ids:
            movies = Movie.objects.filter(get_filtered_movies(selected_genre))
            logger.debug(f"Number of movies after filtering: {movies.count()}")

            if movies.exists():
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
            # Retrieve movies from URL parameters
            movie_id_list = [int(id) for id in movie_ids.split(",") if id.isdigit()]
            selected_movies = list(Movie.objects.filter(id__in=movie_id_list))
            logger.debug(
                f"Movies retrieved from IDs: {[m.title for m in selected_movies]}"
            )

        # Fetch and save trailer URLs
        for movie in selected_movies:
            fetch_trailer_url(movie)

        context = {
            "movies": selected_movies,
            "genres": genres,
            "selected_genre": selected_genre,
            "count": count,
            "movie_ids": movie_ids,
        }
        return render(request, "picker/random_movie.html", context)

    except Exception as e:
        logger.error(f"Error fetching random movie: {str(e)}")
        return render(request, "error.html", {"error": str(e)})
