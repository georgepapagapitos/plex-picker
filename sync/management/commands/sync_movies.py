# sync/management/commands/sync_movies.py

from django.conf import settings
from django.core.management.base import BaseCommand
from plexapi.server import PlexServer

from sync.models.movie import Movie
from utils.genre_utils import get_or_create_genres
from utils.logger_utils import setup_logging
from utils.trailer_utils import fetch_trailer_url

logger = setup_logging(__name__)


class Command(BaseCommand):
    # python manage.py sync_movies

    help = "Sync Plex movies to the local database"

    def handle(self, *args, **kwargs):
        try:
            # Connect to Plex server
            plex = PlexServer(settings.PLEX_URL, settings.PLEX_TOKEN)

            # Fetch the movie library section
            movies = plex.library.section("Movies").all()

            logger.info(f"Found {len(movies)} movies in Plex.")

            for plex_movie in movies:
                # Extract movie metadata
                title = plex_movie.title
                summary = plex_movie.summary
                year = plex_movie.year
                duration = plex_movie.duration
                poster_url = plex_movie.posterUrl
                genres = ", ".join([g.tag for g in plex_movie.genres])
                plex_key = plex_movie.ratingKey

                rotten_tomatoes_rating = (
                    plex_movie.audienceRating * 10
                    if plex_movie.audienceRating
                    else None
                )

                tmdb_id = None
                for guid in plex_movie.guids:
                    if guid.id.startswith("tmdb://"):
                        tmdb_id = int(guid.id.split("/")[-1])
                        break

                # Check if the movie already exists in the database
                try:
                    movie, created = Movie.objects.update_or_create(
                        plex_key=plex_key,
                        defaults={
                            "title": title,
                            "summary": summary,
                            "year": year,
                            "duration": duration,
                            "poster_url": poster_url,
                            "tmdb_id": tmdb_id,
                            "rotten_tomatoes_rating": rotten_tomatoes_rating,
                        },
                    )

                    # Get or create genre objects
                    genre_objects = get_or_create_genres(genres)

                    # Set the genres for the movie
                    movie.genres.set(genre_objects)

                    if created:
                        logger.info(f"Added new movie: {title}")
                        fetch_trailer_url(movie)  # Fetch trailer URL for new movies
                    else:
                        logger.info(f"Updated existing movie: {title}")
                        # Update the trailer URL if it's not set
                        if not movie.trailer_url:
                            fetch_trailer_url(movie)

                except Exception as db_error:
                    logger.error(f"Error saving movie '{title}': {str(db_error)}")

            logger.info("Movie sync completed successfully.")
        except Exception as e:
            logger.error(f"Error syncing movies: {str(e)}")
