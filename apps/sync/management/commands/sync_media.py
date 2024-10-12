# apps/sync/management/commands/sync_media.py

import random
import time
import traceback
from functools import wraps

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import OperationalError, transaction
from django.utils.timezone import make_aware
from plexapi.server import PlexServer

from apps.sync.helpers import fetch_movie_links
from apps.sync.models import Episode, Genre, Movie, Person, Role, Show, Studio
from utils.logger_utils import setup_logging
from utils.trailer_utils import TrailerFetcher

logger = setup_logging(__name__)


def retry_on_db_lock(max_attempts=5, delay=0.1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    if "database is locked" in str(e) and attempt < max_attempts - 1:
                        sleep_time = delay * (2**attempt) + random.uniform(0, 0.1)
                        logger.warning(
                            f"Database locked. Retrying in {sleep_time:.2f} seconds..."
                        )
                        time.sleep(sleep_time)
                    else:
                        raise

        return wrapper

    return decorator


class Command(BaseCommand):
    help = "Sync Plex movies and TV shows to the local database"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.plex = PlexServer(settings.PLEX_URL, settings.PLEX_TOKEN)
        self.existing_studios = {}
        self.trailer_fetcher = TrailerFetcher(
            tmdb_api_url=settings.TMDB_API_URL,
            tmdb_api_key=settings.TMDB_API_KEY,
            youtube_api_key=settings.YOUTUBE_API_KEY,
        )

    def handle(self, *args, **kwargs):
        try:
            self.preload_existing_data()
            self.sync_movies()
            self.sync_shows()
            logger.info("Media sync completed successfully.")
        except Exception as e:
            logger.error(f"Error syncing media: {str(e)}")

    def preload_existing_data(self):
        self.existing_studios = {studio.name: studio for studio in Studio.objects.all()}
        logger.info(f"Preloaded {len(self.existing_studios)} studios")

    @retry_on_db_lock()
    def sync_movies(self):
        movies = self.plex.library.section("Movies").all()
        logger.info(f"Found {len(movies)} movies in Plex.")

        for index, plex_movie in enumerate(movies, 1):
            try:
                logger.debug(
                    f"Processing movie {index}/{len(movies)}: {plex_movie.title}"
                )
                self.process_movie(plex_movie)
            except Exception as e:
                logger.error(f"Error processing movie {plex_movie.title}: {str(e)}")

        logger.info(f"Synced {Movie.objects.count()} movies to the database.")

    @retry_on_db_lock()
    def sync_shows(self):
        shows = self.plex.library.section("TV Shows").all()
        logger.info(f"Found {len(shows)} shows in Plex.")

        for index, plex_show in enumerate(shows, 1):
            try:
                logger.debug(f"Processing show {index}/{len(shows)}: {plex_show.title}")
                self.process_show(plex_show)
            except Exception as e:
                logger.error(f"Error processing show {plex_show.title}: {str(e)}")

        logger.info(f"Synced {Show.objects.count()} shows to the database.")

    @retry_on_db_lock()
    def process_genres(self, plex_media, content_object):
        try:
            genre_objects = []
            for genre in plex_media.genres:
                genre_obj, created = Genre.objects.get_or_create(name=genre.tag)
                genre_objects.append(genre_obj)
            content_object.genres.set(genre_objects)
            logger.debug(f"Processed {len(genre_objects)} genres for {content_object}")
        except Exception as e:
            logger.error(f"Error processing genres for {content_object}: {str(e)}")
            logger.error(traceback.format_exc())

    @retry_on_db_lock()
    def process_roles(self, plex_media, content_object):
        try:
            roles_count = 0
            for order, plex_role in enumerate(plex_media.roles):
                person = self.get_or_create_person(plex_role)
                character_name = self.extract_character_name(
                    plex_role, plex_media.title
                )

                role_data = {
                    "character_name": character_name,
                    "role_type": "ACTOR",
                    "order": order,
                }

                if isinstance(content_object, Movie):
                    role_data["movie"] = content_object
                elif isinstance(content_object, Show):
                    role_data["show"] = content_object
                elif isinstance(content_object, Episode):
                    role_data["episode"] = content_object
                else:
                    raise ValueError(
                        f"Unsupported content object type: {type(content_object)}"
                    )

                Role.objects.update_or_create(
                    person=person,
                    **{k: v for k, v in role_data.items() if k != "character_name"},
                    defaults={"character_name": character_name},
                )
                roles_count += 1
            logger.debug(f"Processed {roles_count} roles for {content_object}")
        except Exception as e:
            logger.error(f"Error processing roles for {content_object}: {str(e)}")
            logger.error(traceback.format_exc())

    @retry_on_db_lock()
    def get_or_create_person(self, plex_person):
        full_name = plex_person.tag.split(" as ", 1)[0]
        first_name, last_name = self.split_name(full_name)

        person, created = Person.objects.get_or_create(
            first_name=first_name,
            last_name=last_name,
            defaults={"photo_url": getattr(plex_person, "thumb", None)},
        )

        if not created and person.photo_url != getattr(plex_person, "thumb", None):
            person.photo_url = getattr(plex_person, "thumb", None)
            person.save()

        return person

    @staticmethod
    def extract_character_name(plex_role, title):
        if " as " in plex_role.tag:
            _, character_name = plex_role.tag.split(" as ", 1)
            return character_name.strip()
        return None

    @transaction.atomic
    @retry_on_db_lock()
    def process_movie(self, plex_movie):
        movie_data = self.extract_movie_data(plex_movie)
        movie, created = Movie.objects.update_or_create(
            plex_key=movie_data["plex_key"], defaults=movie_data
        )
        self.process_genres(plex_movie, movie)
        self.process_roles(plex_movie, movie)

        # Fetch and update movie links
        tmdb_url, trakt_url, imdb_url = fetch_movie_links(movie)
        movie.tmdb_url = tmdb_url
        movie.trakt_url = trakt_url
        movie.imdb_url = imdb_url
        movie.save()

        if created or not movie.trailer_url:
            try:
                trailer_url = self.trailer_fetcher.fetch_trailer_url(movie)
                if trailer_url:
                    movie.trailer_url = trailer_url
                    movie.save()
                    logger.info(f"Added trailer URL for movie: {movie.title}")
                else:
                    logger.warning(f"No trailer found for movie: {movie.title}")
            except Exception as e:
                logger.error(
                    f"Error fetching trailer for movie {movie.title}: {str(e)}"
                )

    @transaction.atomic
    @retry_on_db_lock()
    def process_show(self, plex_show):
        show_data = self.extract_show_data(plex_show)
        show, created = Show.objects.update_or_create(
            plex_key=show_data["plex_key"], defaults=show_data
        )
        self.process_genres(plex_show, show)
        self.process_roles(plex_show, show)

        # if created or not show.trailer_url:
        #     try:
        #         trailer_url = self.trailer_fetcher.fetch_trailer_url(show)
        #         if trailer_url:
        #             show.trailer_url = trailer_url
        #             show.save()
        #             logger.info(f"Added trailer URL for show: {show.title}")
        #         else:
        #             logger.warning(f"No trailer found for show: {show.title}")
        #     except Exception as e:
        #         logger.error(f"Error fetching trailer for show {show.title}: {str(e)}")

        for plex_episode in plex_show.episodes():
            self.process_episode(plex_episode, show)

    @retry_on_db_lock()
    def process_episode(self, plex_episode, show):
        episode_data = self.extract_episode_data(plex_episode, show.id)
        episode, created = Episode.objects.update_or_create(
            plex_key=episode_data["plex_key"], defaults=episode_data
        )
        self.process_roles(plex_episode, episode)

    @staticmethod
    def split_name(full_name):
        name_parts = full_name.split(maxsplit=1)
        return (
            (name_parts[0], name_parts[1])
            if len(name_parts) == 2
            else (name_parts[0], "")
        )

    @retry_on_db_lock()
    def get_or_create_studio(self, studio_name):
        if not studio_name:
            return None
        if studio_name in self.existing_studios:
            return self.existing_studios[studio_name]
        studio, created = Studio.objects.get_or_create(name=studio_name)
        self.existing_studios[studio_name] = studio
        return studio

    def extract_movie_data(self, plex_movie):
        studio = self.get_or_create_studio(plex_movie.studio)
        return {
            "plex_key": str(plex_movie.ratingKey),
            "title": plex_movie.title,
            "summary": plex_movie.summary,
            "year": plex_movie.year,
            "duration": plex_movie.duration,
            "poster_url": plex_movie.posterUrl,
            "tmdb_id": next(
                (
                    int(guid.id.split("/")[-1])
                    for guid in plex_movie.guids
                    if guid.id.startswith("tmdb://")
                ),
                None,
            ),
            "content_rating": plex_movie.contentRating,
            "studio": studio,
            "originally_available_at": (
                make_aware(plex_movie.originallyAvailableAt)
                if plex_movie.originallyAvailableAt
                else None
            ),
            "added_at": make_aware(plex_movie.addedAt) if plex_movie.addedAt else None,
            "updated_at": (
                make_aware(plex_movie.updatedAt) if plex_movie.updatedAt else None
            ),
            "original_title": plex_movie.originalTitle,
            "originally_available_at": plex_movie.originallyAvailableAt,
            "rotten_tomatoes_rating": (
                plex_movie.audienceRating * 10 if plex_movie.audienceRating else None
            ),
            "art": f"{settings.PLEX_URL}{plex_movie.art}?X-Plex-Token={settings.PLEX_TOKEN}",
            "tagline": plex_movie.tagline,
            "audience_rating": plex_movie.audienceRating,
            "audience_rating_image": plex_movie.audienceRatingImage,
            "view_count": plex_movie.viewCount,
            "added_at": make_aware(plex_movie.addedAt),
            "updated_at": make_aware(plex_movie.updatedAt),
            "last_viewed_at": (
                make_aware(plex_movie.lastViewedAt) if plex_movie.lastViewedAt else None
            ),
            "guid": plex_movie.guid,
        }

    def extract_show_data(self, plex_show):
        studio = self.get_or_create_studio(plex_show.studio)
        return {
            "plex_key": str(plex_show.ratingKey),
            "title": plex_show.title,
            "summary": plex_show.summary,
            "year": plex_show.year,
            "duration": plex_show.duration,
            "poster_url": plex_show.posterUrl,
            "tmdb_id": next(
                (
                    int(guid.id.split("/")[-1])
                    for guid in plex_show.guids
                    if guid.id.startswith("tmdb://")
                ),
                None,
            ),
            "rotten_tomatoes_rating": (
                plex_show.audienceRating * 10 if plex_show.audienceRating else None
            ),
            "content_rating": plex_show.contentRating,
            "art": f"{settings.PLEX_URL}{plex_show.art}?X-Plex-Token={settings.PLEX_TOKEN}",
            "tagline": plex_show.tagline,
            "studio": studio,
            "audience_rating": plex_show.audienceRating,
            "audience_rating_image": plex_show.audienceRatingImage,
            "added_at": make_aware(plex_show.addedAt) if plex_show.addedAt else None,
            "updated_at": (
                make_aware(plex_show.updatedAt) if plex_show.updatedAt else None
            ),
            "added_at": make_aware(plex_show.addedAt) if plex_show.addedAt else None,
            "updated_at": (
                make_aware(plex_show.updatedAt) if plex_show.updatedAt else None
            ),
            "last_viewed_at": (
                make_aware(plex_show.lastViewedAt) if plex_show.lastViewedAt else None
            ),
        }

    def extract_episode_data(self, plex_episode, show_id):
        return {
            "plex_key": str(plex_episode.ratingKey),
            "show_id": show_id,
            "title": plex_episode.title,
            "summary": plex_episode.summary,
            "season_number": plex_episode.seasonNumber,
            "episode_number": plex_episode.index,
            "duration": plex_episode.duration,
            "tmdb_id": next(
                (
                    int(guid.id.split("/")[-1])
                    for guid in plex_episode.guids
                    if guid.id.startswith("tmdb://")
                ),
                None,
            ),
            "rotten_tomatoes_rating": (
                plex_episode.audienceRating * 10
                if plex_episode.audienceRating
                else None
            ),
            "audience_rating": plex_episode.audienceRating,
            "audience_rating_image": plex_episode.audienceRatingImage,
            "originally_available_at": (
                make_aware(plex_episode.originallyAvailableAt)
                if plex_episode.originallyAvailableAt
                else None
            ),
            "added_at": (
                make_aware(plex_episode.addedAt) if plex_episode.addedAt else None
            ),
            "updated_at": (
                make_aware(plex_episode.updatedAt) if plex_episode.updatedAt else None
            ),
            "last_viewed_at": (
                make_aware(plex_episode.lastViewedAt)
                if plex_episode.lastViewedAt
                else None
            ),
            "view_count": plex_episode.viewCount,
            "has_commercial_marker": plex_episode.hasCommercialMarker,
            "has_intro_marker": plex_episode.hasIntroMarker,
            "has_credits_marker": plex_episode.hasCreditsMarker,
        }
