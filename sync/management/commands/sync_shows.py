# sync/management/commands/sync_shows.py

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import make_aware
from plexapi.server import PlexServer

from sync.models.episode import Episode
from sync.models.person import Person
from sync.models.role import Role
from sync.models.show import Show
from sync.models.studio import Studio
from utils.genre_utils import get_or_create_genres
from utils.logger_utils import setup_logging
from utils.trailer_utils import TrailerFetcher

logger = setup_logging(__name__)


class Command(BaseCommand):
    help = "Sync Plex TV shows, episodes, and roles to the local database"

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
            shows = plex.library.section("TV Shows").all()
            logger.info(f"Found {len(shows)} shows in Plex.")

            existing_shows = {show.plex_key: show for show in Show.objects.all()}
            existing_episodes = {
                episode.plex_key: episode for episode in Episode.objects.all()
            }
            existing_people = {
                f"{person.first_name} {person.last_name}": person
                for person in Person.objects.all()
            }

            for plex_show in shows:
                self.process_show(
                    plex_show, existing_shows, existing_episodes, existing_people
                )

            logger.info("Show, episode, and role sync completed successfully.")

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while syncing: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")

    def process_show(
        self, plex_show, existing_shows, existing_episodes, existing_people
    ):
        try:
            show_data = self.extract_show_data(plex_show)
            plex_key = show_data["plex_key"]
            genres = ", ".join([g.tag for g in plex_show.genres])

            studio_name = plex_show.studio
            if studio_name:
                studio, _ = Studio.objects.get_or_create(name=studio_name)
                show_data["studio"] = studio

            with transaction.atomic():
                show, created = Show.objects.update_or_create(
                    plex_key=plex_key, defaults=show_data
                )

                if created:
                    existing_shows[plex_key] = show
                    logger.info(f"Created new show: {show.title}")
                else:
                    logger.debug(f"Updated existing show: {show.title}")

                genre_objects = get_or_create_genres(genres)
                show.genres.set(genre_objects)

                self.process_roles(plex_show, show, existing_people)
                self.process_episodes(
                    plex_show, show, existing_episodes, existing_people
                )

                if created or not show.trailer_url:
                    self.fetch_show_trailer(show)

        except Exception as e:
            logger.error(f"Error processing show {plex_show.title}: {str(e)}")

    def fetch_show_trailer(self, show):
        if not show.trailer_url:
            try:
                trailer_url = self.trailer_fetcher.fetch_trailer_url(show)
                if trailer_url:
                    show.trailer_url = trailer_url
                    show.save()
                    logger.info(f"Added trailer URL for show: {show.title}")
                else:
                    logger.warning(f"No trailer found for show: {show.title}")
            except Exception as e:
                logger.error(f"Error fetching trailer for show {show.title}: {str(e)}")

    def process_roles(self, plex_show, db_show, existing_people):
        # Instead of deleting all roles, we'll update or create as needed
        tmdb_show_info = (
            self.get_tmdb_show(db_show.tmdb_id) if db_show.tmdb_id else None
        )
        self.process_role_type(
            plex_show.roles, db_show, existing_people, "ACTOR", tmdb_show_info
        )

    def process_episodes(self, plex_show, db_show, existing_episodes, existing_people):
        for plex_episode in plex_show.episodes():
            try:
                episode_data = self.extract_episode_data(plex_episode, db_show.id)
                plex_key = episode_data["plex_key"]

                if plex_key in existing_episodes:
                    episode = existing_episodes[plex_key]
                    for key, value in episode_data.items():
                        setattr(episode, key, value)
                    episode.save()
                    logger.debug(f"Updated existing episode: {episode.title}")
                else:
                    episode = Episode.objects.create(**episode_data)
                    existing_episodes[plex_key] = episode
                    logger.info(f"Created new episode: {episode.title}")

                self.process_episode_roles(plex_episode, episode, existing_people)

            except Exception as e:
                logger.error(f"Error processing episode {plex_episode.title}: {str(e)}")

    def process_episode_roles(self, plex_episode, db_episode, existing_people):
        tmdb_episode_info = (
            self.get_tmdb_episode(
                db_episode.show.tmdb_id,
                db_episode.season_number,
                db_episode.episode_number,
            )
            if db_episode.show.tmdb_id
            else None
        )

        self.process_role_type(
            plex_episode.roles,
            db_episode,
            existing_people,
            "ACTOR",
            tmdb_episode_info,
            is_episode=True,
        )

        if hasattr(plex_episode, "directors"):
            self.process_role_type(
                plex_episode.directors,
                db_episode,
                existing_people,
                "DIRECTOR",
                is_episode=True,
            )

        if hasattr(plex_episode, "writers"):
            self.process_role_type(
                plex_episode.writers,
                db_episode,
                existing_people,
                "WRITER",
                is_episode=True,
            )

    def process_role_type(
        self,
        plex_roles,
        db_object,
        existing_people,
        role_type,
        tmdb_info=None,
        is_episode=False,
    ):
        for plex_role in plex_roles:
            try:
                person = self.get_or_create_person(plex_role, existing_people)
                character_name = None

                if role_type == "ACTOR":
                    character_name = self.extract_character_name(
                        plex_role, db_object.title
                    )
                    if character_name is None and tmdb_info:
                        character_name = self.get_character_name_from_tmdb(
                            tmdb_info, person.full_name
                        )

                role_data = {
                    "person": person,
                    "role_type": role_type,
                    "character_name": character_name,
                }

                if is_episode:
                    role_data["episode"] = db_object
                    existing_role = Role.objects.filter(
                        person=person, episode=db_object, role_type=role_type
                    ).first()
                else:
                    role_data["show"] = db_object
                    existing_role = Role.objects.filter(
                        person=person, show=db_object, role_type=role_type
                    ).first()

                if existing_role:
                    for key, value in role_data.items():
                        setattr(existing_role, key, value)
                    existing_role.save()
                    logger.debug(
                        f"Updated existing {role_type.lower()} role: {person.full_name} in {db_object.title}"
                    )
                else:
                    Role.objects.create(**role_data)
                    logger.debug(
                        f"Created new {role_type.lower()} role: {person.full_name} in {db_object.title}"
                    )

            except Exception as e:
                logger.error(
                    f"Error processing {role_type.lower()} role for {plex_role.tag} in {db_object.title}: {str(e)}"
                )

    def get_or_create_person(self, plex_person, existing_persons):
        full_name = plex_person.tag.split(" as ", 1)[0]
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

    def extract_character_name(self, plex_role, title):
        logger.debug(f"Extracting character name for role: {plex_role.tag} in {title}")

        if " as " in plex_role.tag:
            actor_name, character_name = plex_role.tag.split(" as ", 1)
            logger.debug(f"Extracted character name from tag: {character_name}")
            return character_name.strip()

        logger.debug(f"Could not extract character name for {plex_role.tag} in {title}")
        return None

    def get_tmdb_show(self, tmdb_id):
        if tmdb_id in self.tmdb_cache:
            return self.tmdb_cache[tmdb_id]

        url = f"{settings.TMDB_API_URL}/tv/{tmdb_id}"
        params = {"api_key": settings.TMDB_API_KEY, "append_to_response": "credits"}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            show_info = response.json()
            self.tmdb_cache[tmdb_id] = show_info
            return show_info
        else:
            logger.error(
                f"Failed to fetch TMDB data for show ID {tmdb_id}: {response.status_code}"
            )
            return None

    def get_tmdb_episode(self, show_tmdb_id, season_number, episode_number):
        cache_key = f"{show_tmdb_id}_{season_number}_{episode_number}"
        if cache_key in self.tmdb_cache:
            return self.tmdb_cache[cache_key]

        url = f"{settings.TMDB_API_URL}/tv/{show_tmdb_id}/season/{season_number}/episode/{episode_number}"
        params = {"api_key": settings.TMDB_API_KEY, "append_to_response": "credits"}
        response = requests.get(url, params=params)
        if response.status_code == 200:
            episode_info = response.json()
            self.tmdb_cache[cache_key] = episode_info
            return episode_info
        else:
            logger.error(
                f"Failed to fetch TMDB data for episode S{season_number}E{episode_number} of show ID {show_tmdb_id}: {response.status_code}"
            )
            return None

    def get_character_name_from_tmdb(self, tmdb_info, actor_name):
        if not tmdb_info or "credits" not in tmdb_info:
            return None
        for cast in tmdb_info["credits"].get("cast", []):
            if cast["name"].lower() == actor_name.lower():
                return cast["character"]
        return None

    @staticmethod
    def split_name(full_name):
        name_parts = full_name.split(maxsplit=1)
        if len(name_parts) == 2:
            return name_parts[0], name_parts[1]
        else:
            return name_parts[0], ""

    def make_aware_if_naive(self, dt):
        return make_aware(dt) if dt and dt.tzinfo is None else dt

    def extract_show_data(self, plex_show):
        return {
            "plex_key": plex_show.ratingKey,
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
            "studio": None,  # This will be set in process_show if a studio exists
            "audience_rating": plex_show.audienceRating,
            "audience_rating_image": plex_show.audienceRatingImage,
            "originally_available_at": self.make_aware_if_naive(
                plex_show.originallyAvailableAt
            ),
            "added_at": self.make_aware_if_naive(plex_show.addedAt),
            "updated_at": self.make_aware_if_naive(plex_show.updatedAt),
            "last_viewed_at": self.make_aware_if_naive(plex_show.lastViewedAt),
        }

    def extract_episode_data(self, plex_episode, show_id):
        return {
            "plex_key": plex_episode.ratingKey,
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
            "originally_available_at": self.make_aware_if_naive(
                plex_episode.originallyAvailableAt
            ),
            "added_at": self.make_aware_if_naive(plex_episode.addedAt),
            "updated_at": self.make_aware_if_naive(plex_episode.updatedAt),
            "last_viewed_at": self.make_aware_if_naive(plex_episode.lastViewedAt),
            "view_count": plex_episode.viewCount,
            "has_commercial_marker": plex_episode.hasCommercialMarker,
            "has_intro_marker": plex_episode.hasIntroMarker,
            "has_credits_marker": plex_episode.hasCreditsMarker,
        }
