# sync/management/commands/sync_media.py

import random
import time
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
import tmdbsimple as tmdb
import trakt
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import Q
from django.utils.timezone import make_aware
from imdb import IMDb
from plexapi.media import MediaTag
from plexapi.server import PlexServer
from plexapi.video import Episode as PlexEpisode
from plexapi.video import Movie as PlexMovie
from plexapi.video import Show as PlexShow
from tvdb_api import Tvdb

from sync.decorators import retry_on_db_lock
from sync.helpers import fetch_movie_links
from sync.models import Episode, Genre, Movie, Person, Role, Show, Studio
from utils.logger_utils import setup_logging
from utils.trailer_utils import TrailerFetcher

logger = setup_logging(__name__)


class Command(BaseCommand):
    """
    Django management command to synchronize Plex media library with local database.

    This command syncs movies and TV shows from a Plex server to a local Django database.
    It handles the creation and updating of movies, shows, episodes, genres, roles, and persons.

    Usage:
        python manage.py sync_media --movies
        python manage.py sync_media --shows
        python manage.py sync_media --movies --shows

    Note:
        This command requires proper configuration of Plex server details and API keys
        in the project settings.
    """

    help = "Sync Plex movies and TV shows to the local database"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.existing_studios = {}
        self.person_cache = {}
        self.api_cache = {}
        self.trailer_fetcher = TrailerFetcher(
            tmdb_api_url=settings.TMDB_API_URL,
            tmdb_api_key=settings.TMDB_API_KEY,
            youtube_api_key=settings.YOUTUBE_API_KEY,
        )
        self.imdb = IMDb()
        logger.info("Command initialized with APIs, Plex Server, and IMDb")

    def setup_apis(self) -> None:
        """
        Set up API connections for TMDB, TVDB, Plex, and Trakt.

        This method initializes the necessary API keys and connections
        for interacting with various media databases and services.
        """
        tmdb.API_KEY = settings.TMDB_API_KEY
        self.tvdb = Tvdb(apikey=settings.TVDB_API_KEY)
        self.plex = PlexServer(settings.PLEX_URL, settings.PLEX_TOKEN)
        trakt.core.CLIENT_ID = settings.TRAKT_CLIENT_ID
        trakt.core.CLIENT_SECRET = settings.TRAKT_CLIENT_SECRET
        logger.info("APIs set up successfully")

    def add_arguments(self, parser):
        parser.add_argument(
            "--movies",
            action="store_true",
            help="Sync movies from Plex",
        )
        parser.add_argument(
            "--shows",
            action="store_true",
            help="Sync TV shows from Plex",
        )

    def handle(self, *args, **options):
        try:
            self.setup_apis()
            self.preload_existing_data()

            if not options["movies"] and not options["shows"]:
                raise CommandError("Please specify --movies, --shows, or both.")

            if options["movies"] and options["shows"]:
                logger.info("Starting full sync of movies and TV shows")
            elif options["movies"]:
                logger.info("Starting sync of movies only")
            elif options["shows"]:
                logger.info("Starting sync of TV shows only")

            if options["movies"]:
                logger.info("Beginning movie sync process")
                self.sync_movies()

            if options["shows"]:
                logger.info("Beginning TV show sync process")
                self.sync_shows()

            logger.info("Media sync completed successfully.")
        except Exception as e:
            logger.error(f"Error syncing media: {str(e)}")
            logger.error(traceback.format_exc())

    def preload_existing_data(self):
        """
        Preload existing studios to reduce database queries.
        """
        self.existing_studios = {studio.name: studio for studio in Studio.objects.all()}
        logger.info(f"Preloaded {len(self.existing_studios)} studios")

    @retry_on_db_lock()
    def sync_movies(self) -> None:
        """
        Synchronize movies from Plex to the local database.

        Retrieves all movies from the Plex server, processes them in batches,
        and updates the local database accordingly.
        """
        start_time = time.time()
        movies = self.plex.library.section("Movies").all()
        logger.info(f"Found {len(movies)} movies in Plex.")

        batch_size = 100
        for i in range(0, len(movies), batch_size):
            batch = movies[i : i + batch_size]
            try:
                self.process_movie_batch(batch)
            except Exception as e:
                logger.error(f"Error processing batch {i//batch_size + 1}: {str(e)}")
            logger.info(
                f"Processed {min(i+batch_size, len(movies))}/{len(movies)} movies"
            )

        total_time = time.time() - start_time
        logger.info(
            f"Synced {Movie.objects.count()} movies to the database in {total_time:.2f} seconds."
        )

    @retry_on_db_lock()
    def sync_shows(self):
        """
        Sync all TV shows from Plex to the local database using batch processing.

        Retrieves all TV shows from the Plex server, processes them in batches,
        and updates the local database, including associated episodes.
        """
        shows = self.plex.library.section("TV Shows").all()
        logger.info(f"Found {len(shows)} shows in Plex.")

        batch_size = 50
        for i in range(0, len(shows), batch_size):
            batch = shows[i : i + batch_size]
            self.process_show_batch(batch)
            logger.info(f"Processed {min(i+batch_size, len(shows))}/{len(shows)} shows")

        logger.info(f"Synced {Show.objects.count()} shows to the database.")

    @transaction.atomic
    @retry_on_db_lock()
    def process_movie_batch(self, plex_movies: List[PlexMovie]) -> None:
        """
        Process a batch of movies from Plex and update the local database.

        Args:
            plex_movies: A list of Plex movie objects to process.

        Raises:
            ValueError: If the input list is empty.
            Exception: For any errors during processing, which are logged.
        """
        if not plex_movies:
            logger.warning("Received empty batch of movies to process")
            raise ValueError("Empty movie batch")

        movie_data_list = []
        for plex_movie in plex_movies:
            try:
                movie_data = self.extract_movie_data(plex_movie)
                movie_data_list.append(movie_data)
            except Exception as e:
                logger.error(
                    f"Error extracting data for movie {plex_movie.title}: {str(e)}"
                )
                logger.debug(traceback.format_exc())

        try:
            # Bulk create or update movies
            Movie.objects.bulk_create(
                [Movie(**data) for data in movie_data_list], ignore_conflicts=True
            )

            for plex_movie, movie_data in zip(plex_movies, movie_data_list):
                try:
                    movie = Movie.objects.get(plex_key=movie_data["plex_key"])
                    self.process_genres(plex_movie, movie)
                    self.process_roles(plex_movie, movie)

                    # Fetch and update movie links
                    tmdb_url, trakt_url, imdb_url = fetch_movie_links(movie)
                    movie.tmdb_url = tmdb_url
                    movie.trakt_url = trakt_url
                    movie.imdb_url = imdb_url

                    try:
                        trailer_url = self.trailer_fetcher.fetch_trailer_url(movie)
                        if trailer_url:
                            movie.trailer_url = trailer_url
                            logger.info(
                                f"Added/Updated trailer URL for movie: {movie.title}"
                            )
                        else:
                            logger.warning(f"No trailer found for movie: {movie.title}")
                    except Exception as e:
                        logger.error(
                            f"Error fetching trailer for movie {movie.title}: {str(e)}"
                        )

                    movie.save()
                    logger.info(f"Successfully processed movie: {movie.title}")
                except Exception as e:
                    logger.error(f"Error processing movie {plex_movie.title}: {str(e)}")
                    logger.debug(traceback.format_exc())
        except Exception as e:
            logger.error(f"Error in bulk movie processing: {str(e)}")
            logger.debug(traceback.format_exc())
            raise

    @transaction.atomic
    @retry_on_db_lock()
    def process_show_batch(self, plex_shows: List[PlexShow]) -> None:
        """
        Process a batch of TV shows from Plex and update the local database.

        Args:
            plex_shows: A list of Plex TV show objects to process.
        """
        show_data_list = []
        for plex_show in plex_shows:
            show_data = self.extract_show_data(plex_show)
            show_data_list.append(show_data)

        # Bulk create or update shows
        Show.objects.bulk_create(
            [Show(**data) for data in show_data_list], ignore_conflicts=True
        )

        for plex_show, show_data in zip(plex_shows, show_data_list):
            show = Show.objects.get(plex_key=show_data["plex_key"])
            self.process_genres(plex_show, show)
            self.process_roles(plex_show, show)

            if not show.trailer_url:
                try:
                    trailer_url = self.trailer_fetcher.fetch_trailer_url(show)
                    if trailer_url:
                        show.trailer_url = trailer_url
                        show.save()
                except Exception as e:
                    logger.error(
                        f"Error fetching trailer for show {show.title}: {str(e)}"
                    )

            self.process_episodes(plex_show, show)

    @transaction.atomic
    @retry_on_db_lock()
    def process_episodes(self, plex_show, show):
        """
        Process all episodes for a given TV show.
        """
        episode_data_list = []
        for plex_episode in plex_show.episodes():
            episode_data = self.extract_episode_data(plex_episode, show.id)
            episode_data_list.append(episode_data)

        # Bulk create or update episodes
        Episode.objects.bulk_create(
            [Episode(**data) for data in episode_data_list], ignore_conflicts=True
        )

        for plex_episode, episode_data in zip(plex_show.episodes(), episode_data_list):
            episode = Episode.objects.get(plex_key=episode_data["plex_key"])
            self.process_roles(plex_episode, episode)

    def extract_movie_data(self, plex_movie: PlexMovie) -> Dict[str, Any]:
        """
        Extract relevant data from a Plex movie object.

        Args:
            plex_movie: A Plex movie object containing raw movie data.

        Returns:
            A dictionary containing extracted and formatted movie data,
            ready for database insertion or update.
        """
        studio = self.get_or_create_studio(plex_movie.studio)

        # Initialize tmdb_id and imdb_id
        tmdb_id = None
        imdb_id = None

        # Extract tmdb_id and imdb_id from guids
        for guid in plex_movie.guids:
            if guid.id.startswith("tmdb://"):
                tmdb_id = int(guid.id.split("/")[-1])
            elif guid.id.startswith("imdb://"):
                imdb_id = guid.id.split("/")[-1]

        return {
            "plex_key": str(plex_movie.ratingKey),
            "title": plex_movie.title,
            "summary": plex_movie.summary,
            "year": plex_movie.year,
            "duration": plex_movie.duration,
            "poster_url": plex_movie.posterUrl,
            "tmdb_id": tmdb_id,
            "imdb_id": imdb_id,
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
            "rotten_tomatoes_rating": (
                plex_movie.audienceRating * 10 if plex_movie.audienceRating else None
            ),
            "art": f"{settings.PLEX_URL}{plex_movie.art}?X-Plex-Token={settings.PLEX_TOKEN}",
            "tagline": plex_movie.tagline,
            "audience_rating": plex_movie.audienceRating,
            "audience_rating_image": plex_movie.audienceRatingImage,
            "view_count": plex_movie.viewCount,
            "last_viewed_at": (
                make_aware(plex_movie.lastViewedAt) if plex_movie.lastViewedAt else None
            ),
            "guid": plex_movie.guid,
        }

    def extract_show_data(self, plex_show: PlexShow) -> Dict[str, Any]:
        """
        Extract relevant data from a Plex TV show object.

        Args:
            plex_show: A Plex TV show object containing raw show data.

        Returns:
            A dictionary containing extracted and formatted show data,
            ready for database insertion or update.
        """
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

    def extract_episode_data(
        self, plex_episode: PlexEpisode, show_id: int
    ) -> Dict[str, Any]:
        """
        Extract relevant data from a Plex episode object.

        Args:
            plex_episode: A Plex episode object containing raw episode data.
            show_id: The database ID of the associated TV show.

        Returns:
            A dictionary containing extracted and formatted episode data,
            ready for database insertion or update.
        """
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

    @retry_on_db_lock()
    def process_genres(
        self,
        plex_media: Union[
            PlexMovie,
            PlexShow,
            PlexEpisode,
        ],
        content_object: Union[Movie, Show, Episode],
    ) -> None:
        """
        Process genres for a given Plex media object and associate them with the content object.

        Args:
            plex_media: The Plex media object containing genre information.
            content_object: The database object to associate genres with.
        """
        try:
            genre_objects = []
            for genre in plex_media.genres:
                genre_obj, created = Genre.objects.get_or_create(name=genre.tag)
                if created:
                    logger.debug(f"Created new genre: {genre.tag}")
                genre_objects.append(genre_obj)
            content_object.genres.set(genre_objects)
            logger.debug(f"Processed {len(genre_objects)} genres for {content_object}")
        except Exception as e:
            logger.error(f"Error processing genres for {content_object}: {str(e)}")
            logger.error(traceback.format_exc())

    @transaction.atomic
    @retry_on_db_lock()
    def process_roles(
        self,
        plex_media: Union[PlexMovie, PlexShow, PlexEpisode],
        content_object: Union[Movie, Show, Episode],
    ) -> None:
        """
        Process roles for a given Plex media object and associate them with the content object.

        Args:
            plex_media: The Plex media object containing role information.
            content_object: The database object to associate roles with.

        Raises:
            ValueError: If the content_object is not of a recognized type.
        """
        role_data_list = []
        person_data_list = []

        # Determine the content type
        if isinstance(content_object, Movie):
            content_type = "movie"
        elif isinstance(content_object, Show):
            content_type = "show"
        elif isinstance(content_object, Episode):
            content_type = "episode"
        else:
            raise ValueError(f"Unknown content object type: {type(content_object)}")

        role_types = {
            "actors": "ACTOR",
            "directors": "DIRECTOR",
            "producers": "PRODUCER",
            "writers": "WRITER",
            "cinematographers": "CINEMATOGRAPHER",
            "composers": "COMPOSER",
            "editors": "EDITOR",
        }

        for plex_role_type, db_role_type in role_types.items():
            plex_roles = getattr(plex_media, plex_role_type, [])
            for plex_order, plex_role in enumerate(plex_roles):
                person_data = self.get_person_data(plex_role, content_type)
                person_data_list.append(person_data)

                character_name = self.get_character_name(plex_role, content_object)

                role_data = {
                    "person_name": f"{person_data['first_name']} {person_data['last_name']}",
                    "role_type": db_role_type,
                    "order": plex_order if db_role_type == "ACTOR" else 0,
                    "character_name": character_name,
                }

                if isinstance(content_object, Movie):
                    role_data["movie_id"] = content_object.id
                elif isinstance(content_object, Show):
                    role_data["show_id"] = content_object.id
                elif isinstance(content_object, Episode):
                    role_data["episode_id"] = content_object.id

                role_data_list.append(role_data)

        # Bulk create/update persons
        self.bulk_create_or_update_persons(person_data_list)

        # Bulk create/update roles
        self.bulk_create_or_update_roles(role_data_list)

    def get_person_data(self, plex_person: MediaTag, content_type) -> Dict[str, Any]:
        """
        Retrieve or construct person data from a Plex person object.

        This method extracts person information from a Plex MediaTag object,
        checks the local cache, and fetches additional data from external APIs if necessary.

        Args:
            plex_person (MediaTag): A Plex MediaTag object representing a person.
            content_type (str): The type of content the person is associated with ('movie', 'show', or 'episode').

        Returns:
            Dict[str, Any]: A dictionary containing person data including name, IDs, and photo URL.

        Note:
            This method caches results to minimize repeated API calls.
        """
        full_name = plex_person.tag.split(" as ", 1)[0]
        first_name, last_name = self.split_name(full_name)

        person_data = {
            "first_name": first_name,
            "last_name": last_name,
            "photo_url": getattr(plex_person, "thumb", None),
            "birth_date": None,
            "death_date": None,
        }

        # Check cache first
        cache_key = f"person_{first_name}_{last_name}"
        cached_data = self.person_cache.get(cache_key)
        if cached_data:
            return {**person_data, **cached_data}

        # Check for Plex-provided IDs
        for guid in getattr(plex_person, "guids", []):
            if guid.id.startswith("tmdb://"):
                person_data["tmdb_id"] = int(guid.id.split("/")[-1])
            elif guid.id.startswith("imdb://"):
                person_data["imdb_id"] = guid.id.split("/")[-1]
            elif guid.id.startswith("tvdb://"):
                person_data["tvdb_id"] = int(guid.id.split("/")[-1])

        # Fetch missing data from external sources
        apis_to_try = ["tmdb", "imdb", "tvdb"]
        if content_type == "movie":
            apis_to_try = ["tmdb", "imdb"]
        elif content_type in ["show", "episode"]:
            apis_to_try = ["tvdb", "imdb"]

        # Fetch missing IDs from external sources
        for api in apis_to_try:
            if api == "tmdb" and not person_data.get("tmdb_id"):
                tmdb_info = self.get_person_tmdb_info(full_name)
                if tmdb_info:
                    person_data.update(tmdb_info)
                    if all(
                        person_data.get(key)
                        for key in [
                            "tmdb_id",
                            "imdb_id",
                            "birth_date",
                            "death_date",
                        ]
                    ):
                        break
            elif api == "imdb" and not person_data.get("imdb_id"):
                imdb_info = self.get_person_imdb_info(full_name)
                if imdb_info:
                    person_data.update(imdb_info)
                    if all(
                        person_data.get(key)
                        for key in [
                            "imdb_id",
                            "birth_date",
                            "death_date",
                        ]
                    ):
                        break
            elif api == "tvdb" and not person_data.get("tvdb_id"):
                tvdb_info = self.get_person_tvdb_info(full_name)
                if tvdb_info:
                    person_data.update(tvdb_info)
                    if all(
                        person_data.get(key)
                        for key in [
                            "tvdb_id",
                            "birth_date",
                            "death_date",
                        ]
                    ):
                        break

        person_data.pop("name", None)

        # Cache the result
        self.person_cache[cache_key] = person_data

        return person_data

    def bulk_create_or_update_persons(
        self, person_data_list: List[Dict[str, Any]]
    ) -> None:
        """
        Bulk create or update Person objects with error handling for unique constraints.

        Args:
            person_data_list: List of dictionaries containing person data.

        Raises:
            Exception: If there's an error during the bulk creation/update process.
        """
        if not person_data_list:
            logger.warning("Received empty list of persons to process")
            return

        try:
            existing_persons = Person.objects.filter(
                Q(first_name__in=[p["first_name"] for p in person_data_list])
                & Q(last_name__in=[p["last_name"] for p in person_data_list])
                | Q(
                    imdb_id__in=[
                        p.get("imdb_id") for p in person_data_list if p.get("imdb_id")
                    ]
                )
            )
            existing_persons_dict = {
                (p.first_name, p.last_name): p for p in existing_persons
            }
            existing_imdb_ids = {p.imdb_id: p for p in existing_persons if p.imdb_id}

            persons_to_create = []
            persons_to_update = []

            for person_data in person_data_list:
                full_name = (person_data["first_name"], person_data["last_name"])
                imdb_id = person_data.get("imdb_id")

                if full_name in existing_persons_dict:
                    person = existing_persons_dict[full_name]
                    for key, value in person_data.items():
                        if value is not None:
                            setattr(person, key, value)
                    persons_to_update.append(person)
                elif imdb_id and imdb_id in existing_imdb_ids:
                    person = existing_imdb_ids[imdb_id]
                    logger.warning(
                        f"Found person with matching IMDb ID but different name. Updating: {person}"
                    )
                    for key, value in person_data.items():
                        if value is not None:
                            setattr(person, key, value)
                    persons_to_update.append(person)
                else:
                    persons_to_create.append(Person(**person_data))

            # Bulk create new persons
            Person.objects.bulk_create(persons_to_create, ignore_conflicts=True)
            logger.info(f"Created {len(persons_to_create)} new persons")

            # Bulk update existing persons
            Person.objects.bulk_update(
                persons_to_update, fields=person_data_list[0].keys()
            )
            logger.info(f"Updated {len(persons_to_update)} existing persons")

        except Exception as e:
            logger.error(f"Error in bulk person creation/update: {str(e)}")
            logger.debug(traceback.format_exc())
            raise

    @transaction.atomic
    def bulk_create_or_update_roles(
        self, role_data_list: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        Efficiently bulk create or update Role objects.

        Args:
            role_data_list (List[Dict]): List of role data dictionaries.

        Returns:
            Tuple[int, int]: Number of roles created and updated.
        """
        if not role_data_list:
            return 0, 0

        # Extract unique person names from role data
        person_names = set()
        for role_data in role_data_list:
            person_name = role_data["person_name"]
            if isinstance(person_name, list):
                # If person_name is a list, join it into a string
                person_name = " ".join(person_name)
            names = (person_name.split(maxsplit=1) + [""])[:2]
            person_names.add(tuple(names))

        first_names, last_names = zip(*person_names)

        # Fetch all relevant persons in one query
        persons = {
            (p.first_name, p.last_name): p
            for p in Person.objects.filter(
                Q(first_name__in=first_names) & Q(last_name__in=last_names)
            )
        }

        # Prepare data for bulk operations
        roles_to_create = []
        existing_role_filter = Q()

        for role_data in role_data_list:
            person_name = role_data["person_name"]
            if isinstance(person_name, list):
                person_name = " ".join(person_name)
            first_name, last_name = (person_name.split(maxsplit=1) + [""])[:2]
            person = persons.get((first_name, last_name))

            if not person:
                # Create person if not exists
                person = Person(first_name=first_name, last_name=last_name)
                person.save()
                persons[(first_name, last_name)] = person

            role = Role(
                person=person,
                role_type=role_data["role_type"],
                order=role_data["order"],
                character_name=role_data["character_name"],
                movie_id=role_data.get("movie_id"),
                show_id=role_data.get("show_id"),
                episode_id=role_data.get("episode_id"),
            )
            roles_to_create.append(role)

            # Build filter for existing roles
            role_filter = Q(
                person=person,
                role_type=role_data["role_type"],
                movie_id=role_data.get("movie_id"),
                show_id=role_data.get("show_id"),
                episode_id=role_data.get("episode_id"),
            )
            existing_role_filter |= role_filter

        # Fetch existing roles
        existing_roles = {}
        for r in Role.objects.filter(existing_role_filter):
            key = (
                r.person_id,
                r.role_type,
                r.movie_id if r.movie_id is not None else None,
                r.show_id if r.show_id is not None else None,
                r.episode_id if r.episode_id is not None else None,
            )
            existing_roles[key] = r

        # Separate roles to create and update
        roles_to_update = []
        final_roles_to_create = []
        for role in roles_to_create:
            key = (
                role.person_id,
                role.role_type,
                role.movie_id if role.movie_id is not None else None,
                role.show_id if role.show_id is not None else None,
                role.episode_id if role.episode_id is not None else None,
            )
            if key in existing_roles:
                existing_role = existing_roles[key]
                existing_role.order = role.order
                existing_role.character_name = role.character_name
                roles_to_update.append(existing_role)
            else:
                final_roles_to_create.append(role)

        # Perform bulk create and update
        created = len(
            Role.objects.bulk_create(final_roles_to_create, ignore_conflicts=True)
        )
        updated = len(roles_to_update)
        if roles_to_update:
            Role.objects.bulk_update(roles_to_update, ["order", "character_name"])

        return created, updated

    def get_person_tmdb_info(self, full_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch person information from TMDB API.

        Args:
            full_name: The full name of the person to search for.

        Returns:
            A dictionary containing person information from TMDB, or None if not found.
        """
        cache_key = f"tmdb_{full_name}"
        if cache_key in self.api_cache:
            return self.api_cache[cache_key]

        max_retries = 3
        for attempt in range(max_retries):
            try:
                search = tmdb.Search()
                response = search.person(query=full_name)
                if response["results"]:
                    person_id = response["results"][0]["id"]
                    person_details = tmdb.People(person_id).info()
                    result = {
                        "tmdb_id": person_id,
                        "imdb_id": person_details.get("imdb_id"),
                        "photo_url": (
                            f"https://image.tmdb.org/t/p/w185{person_details.get('profile_path')}"
                            if person_details.get("profile_path")
                            else None
                        ),
                        "birth_date": self.parse_date(person_details.get("birthday")),
                        "death_date": self.parse_date(person_details.get("deathday")),
                    }
                    self.api_cache[cache_key] = result
                    return result
            except (requests.exceptions.RequestException, tmdb.APIKeyError) as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"TMDB API error for {full_name}, attempt {attempt + 1}: {str(e)}"
                    )
                    time.sleep(2**attempt)  # Exponential backoff
                else:
                    logger.error(
                        f"Failed to fetch person info from TMDB for {full_name} after {max_retries} attempts: {str(e)}"
                    )
            except Exception as e:
                logger.error(
                    f"Unexpected error fetching person info from TMDB for {full_name}: {str(e)}"
                )
                break

        return None

    def get_person_imdb_info(self, full_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch person information from IMDb API.

        Args:
            full_name: The full name of the person to search for.

        Returns:
            A dictionary containing person information from IMDb, or None if not found.
        """
        cache_key = f"imdb_{full_name}"
        if cache_key in self.api_cache:
            return self.api_cache[cache_key]

        max_retries = 3
        base_delay = 1  # Start with a 1-second delay

        for attempt in range(max_retries):
            try:
                people = self.imdb.search_person(full_name)
                if people:
                    person = people[0]
                    self.imdb.update(person)
                    result = {
                        "imdb_id": person.personID,
                        "name": person["name"],
                        "birth_date": self.parse_date(person.get("birth date")),
                        "death_date": self.parse_date(person.get("death date")),
                        "photo_url": person.get("headshot"),
                    }
                    self.api_cache[cache_key] = result
                    return result
            except Exception as e:
                logger.error(
                    f"Error fetching person info from IMDb for {full_name} on attempt {attempt + 1}: {str(e)}"
                )

            if attempt < max_retries - 1:
                delay = base_delay * (2**attempt) + random.uniform(0, 1)
                logger.info(f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)

        logger.error(
            f"Failed to fetch IMDb info for {full_name} after {max_retries} attempts"
        )
        return None

    def get_person_tvdb_info(self, full_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch person information from TVDB API.

        Args:
            full_name: The full name of the person to search for.

        Returns:
            A dictionary containing person information from TVDB, or None if not found.
        """
        cache_key = f"tvdb_{full_name}"
        if cache_key in self.api_cache:
            return self.api_cache[cache_key]

        try:
            results = self.tvdb.search(full_name)
            if results:
                # Filter results to find a person
                person = next((r for r in results if r.get("type") == "person"), None)
                if person:
                    person_id = person["id"]
                    # Fetch detailed person info
                    person_details = self.tvdb.get_person(person_id)
                    result = {
                        "tvdb_id": person_id,
                        "photo_url": person_details.get("image"),
                        "birth_date": self.parse_date(person_details.get("birthday")),
                        "death_date": self.parse_date(person_details.get("deathday")),
                    }
                    self.api_cache[cache_key] = result
                    return result
                else:
                    logger.warning(f"No person found in TVDB results for {full_name}")
            else:
                logger.info(f"No TVDB results found for {full_name}")
        except Exception as e:
            logger.error(
                f"Error fetching person info from TVDB for {full_name}: {str(e)}"
            )

        return None

    def get_character_name(
        self,
        plex_role: MediaTag,
        content_object: Union[Movie, Show, Episode],
    ) -> Optional[str]:
        """
        Get the character name for a given role, trying multiple sources.

        This method attempts to retrieve the character name from various sources,
        including the Plex metadata and external APIs (TMDB, TVDB, IMDb).

        Args:
            plex_role (MediaTag): The Plex role object containing actor information.
            content_object (Union[Movie, Show, Episode]): The database content object
                corresponding to the Plex media.

        Returns:
            Optional[str]: The character name if found, None otherwise.

        Note:
            This method may make external API calls, which could affect performance.
        """
        character_name = self.extract_character_name(plex_role)

        if not character_name:
            if isinstance(content_object, Movie):
                character_name = self.get_character_name_from_tmdb(
                    plex_role, content_object
                )
                if not character_name:
                    character_name = self.get_character_name_from_imdb(
                        plex_role, content_object
                    )
            elif isinstance(content_object, (Show, Episode)):
                character_name = self.get_character_name_from_tvdb(
                    plex_role, content_object
                )
                if not character_name:
                    character_name = self.get_character_name_from_imdb(
                        plex_role, content_object
                    )

        logger.debug(f"Got character name: {character_name} for role: {plex_role.tag}")
        return character_name

    def get_character_name_from_imdb(self, plex_role, content_object):
        """
        Fetch character name from IMDb for a movie or TV show role.
        """
        try:
            if isinstance(content_object, Movie):
                imdb_movie = self.imdb.search_movie(content_object.title)[0]
                self.imdb.update(imdb_movie, info=["full credits"])
                for person in imdb_movie["cast"]:
                    if person["name"].lower() == plex_role.tag.lower():
                        return person.currentRole
            elif isinstance(content_object, (Show, Episode)):
                imdb_show = self.imdb.search_movie(content_object.show.title)[0]
                self.imdb.update(imdb_show, info=["full credits"])
                for person in imdb_show["cast"]:
                    if person["name"].lower() == plex_role.tag.lower():
                        return person.currentRole
        except Exception as e:
            logger.error(f"Error fetching character name from IMDb: {str(e)}")
        return None

    def get_character_name_from_tmdb(self, plex_role, movie):
        """
        Fetch character name from TMDB for a movie role.
        """
        try:
            tmdb_movie = tmdb.Movies(movie.tmdb_id)
            credits = tmdb_movie.credits()
            for cast_member in credits["cast"]:
                if cast_member["name"].lower() == plex_role.tag.lower():
                    return cast_member["character"]
        except Exception as e:
            logger.error(f"Error fetching character name from TMDB: {str(e)}")
        return None

    def get_character_name_from_tvdb(self, plex_role, show_or_episode):
        """
        Fetch character name from TVDB for a TV show or episode role.
        """
        try:
            if isinstance(show_or_episode, Show):
                series = self.tvdb.get_series(show_or_episode.title)
                for actor in series.actors:
                    if actor["name"].lower() == plex_role.tag.lower():
                        return actor["role"]
            elif isinstance(show_or_episode, Episode):
                series = self.tvdb.get_series(show_or_episode.show.title)
                episode = series[show_or_episode.season_number][
                    show_or_episode.episode_number
                ]
                for actor in episode["gueststars"]:
                    if actor["name"].lower() == plex_role.tag.lower():
                        return actor["role"]
        except Exception as e:
            logger.error(f"Error fetching character name from TVDB: {str(e)}")
        return None

    def get_photo_url(self, person, content_object):
        """
        Get the photo URL for a person, trying multiple sources.
        """
        photo_url = None
        if isinstance(content_object, Movie):
            photo_url = self.get_photo_url_from_tmdb(person)
        elif isinstance(content_object, (Show, Episode)):
            photo_url = self.get_photo_url_from_tvdb(person)

        if not photo_url:
            photo_url = self.get_photo_url_from_imdb(person)

        return photo_url

    def get_photo_url_from_imdb(self, person):
        """
        Fetch photo URL from IMDb for a person.
        """
        try:
            imdb_person = self.imdb.search_person(
                f"{person.first_name} {person.last_name}"
            )[0]
            self.imdb.update(imdb_person)
            if imdb_person.get("headshot"):
                return imdb_person["full-size headshot"]
        except Exception as e:
            logger.error(f"Error fetching photo URL from IMDb: {str(e)}")
        return None

    def get_photo_url_from_tmdb(self, person):
        """
        Fetch photo URL from TMDB for a person.
        """
        try:
            search = tmdb.Search()
            response = search.person(query=f"{person.first_name} {person.last_name}")
            if response["results"]:
                person_id = response["results"][0]["id"]
                person_details = tmdb.People(person_id).info()
                if person_details["profile_path"]:
                    return f"https://image.tmdb.org/t/p/w185{person_details['profile_path']}"
        except Exception as e:
            logger.error(f"Error fetching photo URL from TMDB: {str(e)}")
        return None

    def get_photo_url_from_tvdb(self, person):
        """
        Fetch photo URL from TVDB for a person.
        """
        try:
            results = self.tvdb.search(f"{person.first_name} {person.last_name}")
            if results:
                for result in results:
                    if result["entityType"] == "person":
                        person_id = result["id"]
                        person_details = self.tvdb.get_person(person_id)
                        if person_details.get("image"):
                            return person_details["image"]
        except Exception as e:
            logger.error(f"Error fetching photo URL from TVDB: {str(e)}")
        return None

    @retry_on_db_lock()
    def get_or_create_studio(self, studio_name: Optional[str]) -> Optional[Studio]:
        """
        Get an existing studio object or create a new one if it doesn't exist.

        This method checks the local cache first, then the database, and creates a new
        Studio object if necessary.

        Args:
            studio_name (Optional[str]): The name of the studio to get or create.

        Returns:
            Optional[Studio]: The Studio object if found or created, None if studio_name is None.

        Note:
            This method is decorated with retry_on_db_lock to handle potential database locks.
        """
        if not studio_name:
            return None
        if studio_name in self.existing_studios:
            return self.existing_studios[studio_name]
        studio, created = Studio.objects.get_or_create(name=studio_name)
        if created:
            logger.debug(f"Created new studio: {studio_name}")
        self.existing_studios[studio_name] = studio
        return studio

    @staticmethod
    def split_name(full_name: str) -> Tuple[str, str]:
        """
        Split a full name into first name and last name.

        Args:
            full_name: The full name to split.

        Returns:
            A tuple containing the first name and last name.
        """
        name_parts = full_name.split(maxsplit=1)
        return (
            (name_parts[0], name_parts[1])
            if len(name_parts) == 2
            else (name_parts[0], "")
        )

    @staticmethod
    def extract_character_name(plex_role: MediaTag) -> Optional[str]:
        """
        Extract character name from Plex role information.

        Args:
            plex_role: The Plex role object containing actor information.

        Returns:
            The character name if found, None otherwise.
        """
        if " as " in plex_role.tag:
            _, character_name = plex_role.tag.split(" as ", 1)
            return character_name.strip()
        elif hasattr(plex_role, "role") and plex_role.role:
            logger.debug(f"Role attribute value: {plex_role.role}")
            return plex_role.role.strip()
        else:
            logger.debug(f"No character name found for {plex_role.tag}")
            return None

    @staticmethod
    def parse_date(date_string: Optional[str]) -> Optional[datetime.date]:
        """
        Parse a date string into a Python date object.

        Args:
            date_string: A string representation of a date (format: YYYY-MM-DD).

        Returns:
            A date object if parsing is successful, None otherwise.
        """
        if not date_string:
            return None
        try:
            return datetime.strptime(date_string, "%Y-%m-%d").date()
        except ValueError:
            logger.warning(f"Unable to parse date: {date_string}")
            return None
