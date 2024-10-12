# picker/views/random_movie_view.py

from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.views import View

from picker.forms import RandomMovieForm
from picker.helpers.movie_helpers import get_random_movies
from sync.models import Movie
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


class RandomMovieView(View):
    template_name = "random_movie/random_movie.html"
    error_template_name = "error.html"
    partial_template_name = "random_movie/partials/_random_movie_grid.html"

    def get(self, request: HttpRequest):
        try:
            form = RandomMovieForm(request.GET or None)
            logger.debug(
                f"Form initialized with genres: {form.fields['genre'].choices}"
            )

            if form.is_reset():
                return HttpResponseRedirect(reverse("random_movie"))

            (
                selected_genres,
                count,
                selected_rating,
                selected_duration,
                selected_min_year,
                selected_max_year,
                randomize,
                movie_ids,
            ) = self.get_parameters(request, form)

            if randomize or not movie_ids:
                movies = self.filter_movies(
                    selected_genres,
                    selected_rating,
                    selected_duration,
                    selected_min_year,
                    selected_max_year,
                )

                if movies.exists():
                    selected_movies = get_random_movies(movies, count)
                    movie_ids = ",".join(str(movie.id) for movie in selected_movies)
                    self.limit_summary(selected_movies, 100)
                    return self.redirect_with_params(
                        selected_genres,
                        count,
                        movie_ids,
                        selected_rating,
                        selected_duration,
                        selected_min_year,
                        selected_max_year,
                    )
                else:
                    logger.warning("No movies found matching the criteria")
                    selected_movies = []
            else:
                selected_movies = self.get_movies_from_ids(movie_ids)
                self.limit_summary(selected_movies, 200)

            if self.is_ajax(request):
                return self.render_ajax_response(selected_movies)

            context = self.get_context(
                form,
                selected_movies,
                selected_genres,
                count,
                movie_ids,
                selected_rating,
                selected_duration,
                selected_min_year,
                selected_max_year,
            )
            logger.debug(f"Rendering template with {len(selected_movies)} movies")
            return render(request, self.template_name, context)

        except Exception as e:
            return self.handle_exception(request, e)

    def get_parameters(self, request, form):
        selected_genres = [genre for genre in request.GET.getlist("genre") if genre]
        count = max(1, min(int(form.data.get("count", 1)), 4))
        selected_rating = form.data.get("min_rotten_tomatoes_rating", "")
        selected_duration = form.data.get("max_duration", "")
        selected_min_year = form.data.get("min_year", "")
        selected_max_year = form.data.get("max_year", "")
        randomize = request.GET.get("randomize", "").lower() == "true"
        movie_ids = request.GET.get("movies", "")
        return (
            selected_genres,
            count,
            selected_rating,
            selected_duration,
            selected_min_year,
            selected_max_year,
            randomize,
            movie_ids,
        )

    def filter_movies(
        self,
        selected_genres,
        selected_rating,
        selected_duration,
        selected_min_year,
        selected_max_year,
    ):
        movies = Movie.objects.filter(
            (Q(optimized_poster__isnull=False) | Q(poster_url__isnull=False))
            & (Q(optimized_art__isnull=False) | Q(art__isnull=False))
        )

        # Instead of excluding movies, we'll add a safe poster URL
        for movie in movies:
            movie.safe_poster_url = self.get_safe_poster_url(movie)

        if selected_genres:
            movies = (
                movies.filter(genres__name__in=selected_genres)
                .annotate(num_genres=Count("genres"))
                .filter(num_genres=len(selected_genres))
            )

        if selected_rating:
            try:
                min_rating = float(selected_rating)
                movies = movies.filter(rotten_tomatoes_rating__gte=min_rating)
            except ValueError:
                logger.warning(f"Invalid rating value: {selected_rating}")

        if selected_duration.isdigit():
            movies = movies.filter(duration__lte=int(selected_duration) * 60 * 1000)

        if selected_min_year.isdigit():
            movies = movies.filter(year__gte=int(selected_min_year))

        if selected_max_year.isdigit():
            movies = movies.filter(year__lte=int(selected_max_year))

        logger.debug(f"Number of movies after filtering: {movies.count()}")
        return movies

    def limit_summary(self, movies, limit):
        for movie in movies:
            if len(movie.summary) > limit:
                movie.summary = movie.summary[:limit] + "..."

    def redirect_with_params(
        self,
        selected_genres,
        count,
        movie_ids,
        selected_rating,
        selected_duration,
        selected_min_year,
        selected_max_year,
    ):
        genres_param = "&".join([f"genre={genre}" for genre in selected_genres])
        return HttpResponseRedirect(
            f"{reverse('random_movie')}?{genres_param}&count={count}&movies={movie_ids}"
            f"&min_rotten_tomatoes_rating={selected_rating}&max_duration={selected_duration}"
            f"&min_year={selected_min_year}&max_year={selected_max_year}"
        )

    def get_movies_from_ids(self, movie_ids):
        movie_id_list = [int(id) for id in movie_ids.split(",") if id.isdigit()]
        selected_movies = list(Movie.objects.filter(id__in=movie_id_list))
        for movie in selected_movies:
            movie.safe_poster_url = self.get_safe_poster_url(movie)
        logger.debug(f"Movies retrieved from IDs: {[m.title for m in selected_movies]}")
        return selected_movies

    def is_ajax(self, request):
        return request.headers.get("X-Requested-With") == "XMLHttpRequest"

    def render_ajax_response(self, selected_movies):
        html = render_to_string(self.partial_template_name, {"movies": selected_movies})
        return JsonResponse({"html": html})

    def get_context(
        self,
        form,
        selected_movies,
        selected_genres,
        count,
        movie_ids,
        selected_rating,
        selected_duration,
        selected_min_year,
        selected_max_year,
    ):
        return {
            "form": form,
            "movies": selected_movies,
            "selected_genres": selected_genres,
            "count": count,
            "movie_ids": movie_ids,
            "min_rotten_tomatoes_rating": selected_rating,
            "max_duration": selected_duration,
            "min_year": selected_min_year,
            "max_year": selected_max_year,
        }

    def handle_exception(self, request, exception):
        logger.error(f"Error fetching random movie: {str(exception)}")
        if self.is_ajax(request):
            return JsonResponse({"error": str(exception)}, status=500)
        return render(request, self.error_template_name, {"error": str(exception)})

    def get_safe_poster_url(self, movie):
        if movie.optimized_poster:
            try:
                return movie.optimized_poster.url
            except Exception as e:
                logger.warning(
                    f"Error accessing optimized poster for movie {movie.id}: {str(e)}"
                )
        return movie.poster_url
