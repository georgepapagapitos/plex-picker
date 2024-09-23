# picker/views/fetch_random_movie_view.py

from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from picker.forms import RandomMovieForm
from picker.helpers.genre_helpers import get_unique_genres
from picker.helpers.movie_helpers import get_filtered_movies, get_random_movies
from sync.models import Movie
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


def fetch_random_movie(request: HttpRequest):
    try:
        # Retrieve the list of unique genres
        genres = get_unique_genres()
        logger.debug(
            f"Retrieved genres: {genres}"
        )  # Log to check if genres are being retrieved correctly

        # Initialize the form with GET data and available genres
        form = RandomMovieForm(request.GET or None, genres=genres)
        logger.debug(f"Form initialized with genres: {genres}")
        logger.debug(
            f"Form genre choices after initialization: {form.fields['genre'].choices}"
        )
        logger.debug(f"Request method: {request.method}")
        logger.debug(f"GET parameters: {request.GET}")

        selected_genre = form.data.get("genre", "")
        count = int(form.data.get("count", 1))
        randomize = request.GET.get("randomize", "").lower() == "true"
        movie_ids = request.GET.get("movies", "")

        logger.debug(
            f"Input parameters: genre={selected_genre}, count={count}, randomize={randomize}, movie_ids={movie_ids}"
        )

        if randomize or not movie_ids:
            # If randomizing or no movie IDs provided, filter and select movies
            movies = Movie.objects.filter(get_filtered_movies(selected_genre))
            logger.debug(f"Number of movies after filtering: {movies.count()}")

            if movies.exists():
                # Ensure the requested count does not exceed the available movies
                count = max(1, min(count, 4))
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

        # Prepare the context for rendering the template
        context = {
            "form": form,
            "movies": selected_movies,
            "selected_genre": selected_genre,
            "count": count,
            "movie_ids": movie_ids,
        }
        return render(request, "random_movie.html", context)

    except Exception as e:
        # Log any exceptions that occur during processing
        logger.error(f"Error fetching random movie: {str(e)}")
        return render(request, "error.html", {"error": str(e)})
