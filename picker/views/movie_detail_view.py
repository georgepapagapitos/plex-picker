# picker/views/movie_detail_view.py

from django.core.exceptions import ObjectDoesNotExist
from django.core.files.storage import default_storage
from django.db.models import Prefetch
from django.http import Http404
from django.views.generic import DetailView

from sync.models import Movie, Role
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


class MovieDetailView(DetailView):
    model = Movie
    template_name = "movie_detail.html"
    context_object_name = "movie"
    pk_url_kwarg = "movie_id"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response_kwargs = {}

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related(
                Prefetch(
                    "roles",
                    queryset=Role.objects.filter(role_type="ACTOR")
                    .select_related("person")
                    .order_by("order"),
                    to_attr="actor_roles",
                )
            )
        )

    def get_object(self, queryset=None):
        try:
            return super().get_object(queryset)
        except ObjectDoesNotExist:
            logger.error(
                f"Movie with ID {self.kwargs.get(self.pk_url_kwarg)} not found"
            )
            raise Http404(
                f"Movie with ID {self.kwargs.get(self.pk_url_kwarg)} not found"
            )
        except Exception as e:
            logger.error(
                f"Error retrieving movie with ID {self.kwargs.get(self.pk_url_kwarg)}: {str(e)}"
            )
            raise

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        movie = self.object

        if movie:
            # Capture the parameters for redirection
            context.update(
                {
                    "random_movies": self.request.GET.get("movies", ""),
                    "genre": self.request.GET.get("genre", ""),
                    "count": self.request.GET.get("count", 1),
                    "min_rating": self.request.GET.get(
                        "min_rotten_tomatoes_rating", ""
                    ),
                    "max_duration": self.request.GET.get("max_duration", ""),
                }
            )

            # Check if optimized_art exists
            try:
                optimized_art = movie.optimized_art
                if optimized_art and optimized_art.name:
                    if default_storage.exists(optimized_art.name):
                        context["optimized_art_url"] = optimized_art.url
                    else:
                        logger.warning(
                            f"Optimized art file not found for movie ID: {movie.id}"
                        )
                        context["optimized_art_url"] = None
                else:
                    context["optimized_art_url"] = None
            except ObjectDoesNotExist:
                logger.warning(f"No optimized art attribute for movie ID: {movie.id}")
                context["optimized_art_url"] = None

            # Check if optimized_art exists
            context["optimized_art_url"] = self.get_safe_image_url(movie.optimized_art)

            # Check if optimized_poster exists
            context["optimized_poster_url"] = self.get_safe_image_url(
                movie.optimized_poster
            )

            # Get actors with their photo URLs
            try:
                context["actors_with_photos"] = movie.actor_roles[:10]
            except Exception as e:
                logger.error(
                    f"Error retrieving actors for movie ID {movie.id}: {str(e)}"
                )
                context["actors_with_photos"] = []

            context.update(
                {
                    "formatted_actors": movie.formatted_actors(limit=5),
                    "imdb_url": getattr(movie, "imdb_url", None),
                    "tmdb_url": getattr(movie, "tmdb_url", None),
                    "trakt_url": getattr(movie, "trakt_url", None),
                }
            )

        return context

    def render_to_response(self, context, **response_kwargs):
        response_kwargs.update(self.response_kwargs)
        return super().render_to_response(context, **response_kwargs)

    def get_safe_image_url(self, image_field):
        if image_field and image_field.name:
            try:
                return image_field.url
            except Exception as e:
                logger.warning(f"Error accessing image URL: {str(e)}")
        return None
