from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from plexapi.server import PlexServer

from sync.models.actor import Actor
from sync.models.movie import Movie
from utils.genre_utils import get_or_create_genres
from utils.logger_utils import setup_logging
from utils.trailer_utils import TrailerFetcher

logger = setup_logging(__name__)


class Command(BaseCommand):
    help = "Sync Plex movies and actors to the local database"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trailer_fetcher = TrailerFetcher(
            tmdb_api_url=settings.TMDB_API_URL,
            tmdb_api_key=settings.TMDB_API_KEY,
            youtube_api_key=settings.YOUTUBE_API_KEY,
        )

    def handle(self, *args, **kwargs):
        try:
            plex = PlexServer(settings.PLEX_URL, settings.PLEX_TOKEN)
            movies = plex.library.section("Movies").all()
            logger.info(f"Found {len(movies)} movies in Plex.")

            existing_movies = {movie.plex_key: movie for movie in Movie.objects.all()}
            existing_actors = {
                f"{actor.first_name} {actor.last_name}": actor
                for actor in Actor.objects.all()
            }

            for plex_movie in movies:
                self.process_movie(plex_movie, existing_movies, existing_actors)

            logger.info("Movie and actor sync completed successfully.")
        except Exception as e:
            logger.error(f"Error syncing movies: {str(e)}")

    def process_movie(self, plex_movie, existing_movies, existing_actors):
        try:
            movie_data = self.extract_movie_data(plex_movie)
            plex_key = movie_data["plex_key"]
            genres = ", ".join([g.tag for g in plex_movie.genres])

            with transaction.atomic():
                movie, created = Movie.objects.update_or_create(
                    plex_key=plex_key, defaults=movie_data
                )

                genre_objects = get_or_create_genres(genres)
                movie.genres.set(genre_objects)

                self.process_actors(plex_movie, movie, existing_actors)

                if created:
                    logger.info(f"Added new movie: {movie.title}")
                    self.trailer_fetcher.fetch_trailer_url(movie)
                else:
                    logger.debug(f"Updated existing movie: {movie.title}")
                    if not movie.trailer_url:
                        self.trailer_fetcher.fetch_trailer_url(movie)

        except Exception as e:
            logger.error(f"Error processing movie '{plex_movie.title}': {str(e)}")

    def process_actors(self, plex_movie, db_movie, existing_actors):
        movie_actors = []
        for role in plex_movie.roles:
            first_name, last_name = self.split_name(role.tag)
            full_name = f"{first_name} {last_name}"

            if full_name in existing_actors:
                actor = existing_actors[full_name]
                if actor.photo_url != role.thumb:
                    actor.photo_url = role.thumb
                    actor.save()
            else:
                actor = Actor.objects.create(
                    first_name=first_name, last_name=last_name, photo_url=role.thumb
                )
                existing_actors[full_name] = actor

            movie_actors.append(actor)

        db_movie.actors.set(movie_actors)

    @staticmethod
    def split_name(full_name):
        name_parts = full_name.split(maxsplit=1)
        if len(name_parts) == 2:
            return name_parts[0], name_parts[1]
        else:
            return (
                name_parts[0],
                "",
            )  # If only one name is provided, assume it's the first name

    def extract_movie_data(self, plex_movie):
        return {
            "title": plex_movie.title,
            "summary": plex_movie.summary,
            "year": plex_movie.year,
            "duration": plex_movie.duration,
            "poster_url": plex_movie.posterUrl,
            "plex_key": plex_movie.ratingKey,
            "rotten_tomatoes_rating": (
                plex_movie.audienceRating * 10 if plex_movie.audienceRating else None
            ),
            "tmdb_id": next(
                (
                    int(guid.id.split("/")[-1])
                    for guid in plex_movie.guids
                    if guid.id.startswith("tmdb://")
                ),
                None,
            ),
            "content_rating": plex_movie.contentRating,
        }
