import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from plexapi.server import PlexServer

from sync.models import Movie  # Import your Movie model

# Set up logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Sync Plex movies to the local database"

    def handle(self, *args, **kwargs):
        try:
            # Connect to Plex server
            plex = PlexServer(settings.PLEX_URL, settings.PLEX_TOKEN)

            # Fetch the movie library section
            movies = plex.library.section("Movies").all()

            logger.info(f"Found {len(movies)} movies in Plex.")

            for plex_movie in movies:
                # Extract metadata
                title = plex_movie.title
                summary = plex_movie.summary
                year = plex_movie.year
                duration = plex_movie.duration
                rating = plex_movie.rating
                poster_url = plex_movie.posterUrl
                genres = ", ".join([g.tag for g in plex_movie.genres])
                plex_key = plex_movie.ratingKey

                tmdb_id = None
                for guid in plex_movie.guids:
                    if guid.id.startswith("tmdb://"):
                        tmdb_id = int(guid.id.split("/")[-1])
                        break

                # Check if the movie already exists in the database
                movie, created = Movie.objects.update_or_create(
                    plex_key=plex_key,
                    defaults={
                        "title": title,
                        "summary": summary,
                        "year": year,
                        "duration": duration,
                        "rating": rating,
                        "poster_url": poster_url,
                        "genres": genres,
                        "tmdb_id": tmdb_id,
                    },
                )

                if created:
                    logger.info(f"Added new movie: {title}")
                else:
                    logger.info(f"Updated existing movie: {title}")

            logger.info("Movie sync completed successfully.")
        except Exception as e:
            logger.error(f"Error syncing movies: {str(e)}")
