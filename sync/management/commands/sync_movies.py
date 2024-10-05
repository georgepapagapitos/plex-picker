# sync/management/commands/sync_movies.py

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import make_aware
from plexapi.server import PlexServer

from sync.models.movie import Movie
from sync.models.person import Person
from sync.models.role import Role
from sync.models.studio import Studio
from utils.genre_utils import get_or_create_genres
from utils.logger_utils import setup_logging
from utils.trailer_utils import TrailerFetcher

logger = setup_logging(__name__)


class Command(BaseCommand):
    help = "Sync Plex movies, persons, and roles to the local database"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trailer_fetcher = TrailerFetcher(
            tmdb_api_url=settings.TMDB_API_URL,
            tmdb_api_key=settings.TMDB_API_KEY,
            youtube_api_key=settings.YOUTUBE_API_KEY,
        )
        self.tmdb_cache = {}

    def handle(self, *args, **kwargs):
        try:
            plex = PlexServer(settings.PLEX_URL, settings.PLEX_TOKEN)
            movies = plex.library.section("Movies").all()
            logger.info(f"Found {len(movies)} movies in Plex.")

            existing_movies = {movie.plex_key: movie for movie in Movie.objects.all()}
            existing_people = {
                f"{person.first_name} {person.last_name}": person
                for person in Person.objects.all()
            }

            for plex_movie in movies:
                self.process_movie(plex_movie, existing_movies, existing_people)

            logger.info("Movie, person, and role sync completed successfully.")
        except Exception as e:
            logger.error(f"Error syncing movies: {str(e)}")

    def process_movie(self, plex_movie, existing_movies, existing_people):
        try:
            movie_data = self.extract_movie_data(plex_movie)
            plex_key = movie_data["plex_key"]
            genres = ", ".join([g.tag for g in plex_movie.genres])

            studio_name = plex_movie.studio
            if studio_name:
                studio, _ = Studio.objects.get_or_create(name=studio_name)
                movie_data["studio"] = studio

            with transaction.atomic():
                movie, created = Movie.objects.update_or_create(
                    plex_key=plex_key, defaults=movie_data
                )

                if created:
                    existing_movies[plex_key] = movie
                    logger.info(f"Created new movie: {movie.title}")
                else:
                    logger.debug(f"Updated existing movie: {movie.title}")

                genre_objects = get_or_create_genres(genres)
                movie.genres.set(genre_objects)

                self.process_roles(plex_movie, movie, existing_people)

                if created or not movie.trailer_url:
                    self.trailer_fetcher.fetch_trailer_url(movie)

        except Exception as e:
            logger.error(f"Error processing movie '{plex_movie.title}': {str(e)}")

    def get_tmdb_movie(self, tmdb_id):
        if tmdb_id in self.tmdb_cache:
            return self.tmdb_cache[tmdb_id]

        url = f"{settings.TMDB_API_URL}/movie/{tmdb_id}"
        params = {"api_key": settings.TMDB_API_KEY, "append_to_response": "credits"}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            movie_info = response.json()
            self.tmdb_cache[tmdb_id] = movie_info
            return movie_info
        else:
            logger.error(
                f"Failed to fetch TMDB data for movie ID {tmdb_id}: {response.status_code}"
            )
            return None

    def get_character_name_from_tmdb(self, tmdb_movie_info, actor_name):
        if not tmdb_movie_info or "credits" not in tmdb_movie_info:
            return None
        for cast in tmdb_movie_info["credits"].get("cast", []):
            if cast["name"].lower() == actor_name.lower():
                return cast["character"]
        return None

    def process_roles(self, plex_movie, db_movie, existing_people):
        # Fetch TMDB movie info
        tmdb_movie_info = (
            self.get_tmdb_movie(db_movie.tmdb_id) if db_movie.tmdb_id else None
        )

        # Process actors
        self.process_role_type(
            plex_movie.roles, db_movie, existing_people, "ACTOR", tmdb_movie_info
        )

        # Process directors
        self.process_role_type(
            plex_movie.directors, db_movie, existing_people, "DIRECTOR"
        )

        # Process producers
        self.process_role_type(
            plex_movie.producers, db_movie, existing_people, "PRODUCER"
        )

        # Process writers
        self.process_role_type(plex_movie.writers, db_movie, existing_people, "WRITER")

    def process_role_type(
        self, plex_roles, db_movie, existing_people, role_type, tmdb_info=None
    ):
        for plex_role in plex_roles:
            try:
                person = self.get_or_create_person(plex_role, existing_people)
                character_name = None

                if role_type == "ACTOR":
                    character_name = self.extract_character_name(
                        plex_role, db_movie.title
                    )
                    if character_name is None and tmdb_info:
                        character_name = self.get_character_name_from_tmdb(
                            tmdb_info, person.full_name
                        )

                # Check if the role already exists
                existing_role = Role.objects.filter(
                    person=person, movie=db_movie, role_type=role_type
                ).first()

                if existing_role:
                    # Update existing role
                    existing_role.character_name = character_name
                    existing_role.save()
                    logger.debug(
                        f"Updated existing {role_type.lower()} role: {person.full_name} in {db_movie.title}"
                    )
                else:
                    # Create new role
                    Role.objects.create(
                        person=person,
                        movie=db_movie,
                        role_type=role_type,
                        character_name=character_name,
                    )
                    logger.debug(
                        f"Created new {role_type.lower()} role: {person.full_name} in {db_movie.title}"
                    )

            except Exception as e:
                logger.error(
                    f"Error processing {role_type.lower()} role for {plex_role.tag} in {db_movie.title}: {str(e)}"
                )

    def extract_character_name(self, plex_role, movie_title):
        logger.debug(
            f"Extracting character name for role: {plex_role.tag} in {movie_title}"
        )

        # Check if the 'tag' attribute contains both actor name and character name
        if " as " in plex_role.tag:
            actor_name, character_name = plex_role.tag.split(" as ", 1)
            logger.debug(f"Extracted character name from tag: {character_name}")
            return character_name.strip()

        # If we can't find a character name, return None
        logger.debug(
            f"Could not extract character name for {plex_role.tag} in {movie_title}"
        )
        return None

    def get_or_create_person(self, plex_person, existing_persons):
        # The name is stored in the 'tag' attribute
        full_name = plex_person.tag.split(" as ", 1)[
            0
        ]  # Split in case the tag includes the character name
        first_name, last_name = self.split_name(full_name)

        if full_name in existing_persons:
            person = existing_persons[full_name]
            if person.photo_url != getattr(plex_person, "thumb", None):
                person.photo_url = getattr(plex_person, "thumb", None)
                person.save()
        else:
            person = Person.objects.create(
                first_name=first_name,
                last_name=last_name,
                photo_url=getattr(plex_person, "thumb", None),
            )
            existing_persons[full_name] = person

        return person

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
        def make_aware_if_naive(dt):
            return make_aware(dt) if dt and dt.tzinfo is None else dt

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
            "art": f"{settings.PLEX_URL}{plex_movie.art}?X-Plex-Token={settings.PLEX_TOKEN}",
            "tagline": plex_movie.tagline,
            "studio": None,  # This will be set in process_movie if a studio exists
            "audience_rating": plex_movie.audienceRating,
            "audience_rating_image": plex_movie.audienceRatingImage,
            "chapter_source": plex_movie.chapterSource,
            "edition_title": plex_movie.editionTitle,
            "original_title": plex_movie.originalTitle,
            "originally_available_at": plex_movie.originallyAvailableAt,
            "rating_image": plex_movie.ratingImage,
            "view_count": plex_movie.viewCount,
            "added_at": make_aware_if_naive(plex_movie.addedAt),
            "updated_at": make_aware_if_naive(plex_movie.updatedAt),
            "last_viewed_at": make_aware_if_naive(plex_movie.lastViewedAt),
        }
