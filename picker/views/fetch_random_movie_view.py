from django.http import HttpRequest, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from picker.forms import RandomMovieForm
from picker.helpers.movie_helpers import get_filtered_movies, get_random_movies
from sync.models import Movie
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


def fetch_random_movie(request: HttpRequest):
    try:
        # Initialize the form with GET data; genres are fetched in the form itself
        form = RandomMovieForm(request.GET or None)
        logger.debug(f"Form initialized with genres: {form.fields['genre'].choices}")

        # Get parameters with default values
        selected_genre = form.data.get("genre", "")
        count = max(1, min(int(form.data.get("count", 1)), 4))  # Limit count to max 4
        selected_rating = form.data.get("min_rotten_tomatoes_rating", "")
        selected_duration = form.data.get("max_duration", "")
        randomize = request.GET.get("randomize", "").lower() == "true"
        movie_ids = request.GET.get("movies", "")

        if randomize or not movie_ids:
            # If randomizing or no movie IDs provided, filter and select movies
            movies = Movie.objects.filter(get_filtered_movies(selected_genre))

            # Filter by the minimum rotten tomatoes rating if specified
            if selected_rating.isdigit():
                movies = movies.filter(rotten_tomatoes_rating__gte=int(selected_rating))

            # Filter by the maximum duration if specified
            if selected_duration.isdigit():
                movies = movies.filter(duration__lte=int(selected_duration) * 60 * 1000)

            logger.debug(f"Number of movies after filtering: {movies.count()}")

            if movies.exists():
                selected_movies = get_random_movies(movies, count)
                movie_ids = ",".join(str(movie.id) for movie in selected_movies)

                # Redirect to the same view with selected movie IDs in the URL
                return HttpResponseRedirect(
                    f"{reverse('fetch_random_movie')}?genre={selected_genre}&count={count}&movies={movie_ids}&min_rotten_tomatoes_rating={selected_rating}&max_duration={selected_duration}"
                )
            else:
                logger.warning("No movies found matching the criteria")
                selected_movies = []
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
            "min_rotten_tomatoes_rating": selected_rating,
            "max_duration": selected_duration,
        }
        return render(request, "random_movie.html", context)

    except Exception as e:
        # Log any exceptions that occur during processing
        logger.error(f"Error fetching random movie: {str(e)}")
        return render(request, "error.html", {"error": str(e)})
