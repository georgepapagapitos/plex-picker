import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from plexapi.server import PlexServer

from sync.models.episode import Episode
from sync.models.show import Show
from utils.genre_utils import get_or_create_genres
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


class Command(BaseCommand):
    help = "Sync Plex TV shows and episodes to the local database"

    def handle(self, *args, **kwargs):
        try:
            plex = PlexServer(settings.PLEX_URL, settings.PLEX_TOKEN)
            shows = plex.library.section("TV Shows").all()
            logger.info(f"Found {len(shows)} shows in Plex.")

            existing_shows = {show.plex_key: show for show in Show.objects.all()}
            existing_episodes = {
                episode.plex_key: episode for episode in Episode.objects.all()
            }

            shows_to_create, shows_to_update, episodes_to_create, episodes_to_update = (
                [],
                [],
                [],
                [],
            )

            for plex_show in shows:
                show_data = self.extract_show_data(plex_show)
                plex_key = show_data["plex_key"]
                genres = ", ".join([g.tag for g in plex_show.genres])

                existing_show = existing_shows.get(plex_key)

                if existing_show:
                    shows_to_update.append(show_data)
                    logger.debug(f"Updating existing show: {show_data['title']}")
                else:
                    shows_to_create.append(show_data)
                    logger.info(f"Found new show: {show_data['title']}")

                try:
                    with transaction.atomic():
                        if existing_show:
                            for key, value in show_data.items():
                                setattr(existing_show, key, value)
                            existing_show.save()
                        else:
                            new_show, created = Show.objects.get_or_create(
                                plex_key=plex_key, defaults=show_data
                            )
                            if created:
                                logger.info(f"Created new show: {new_show.title}")
                            else:
                                logger.warning(f"Show already exists: {new_show.title}")

                    genre_objects = get_or_create_genres(genres)
                    if existing_show:
                        existing_show.genres.set(genre_objects)
                    else:
                        new_show.genres.set(genre_objects)

                    for plex_episode in plex_show.episodes():
                        episode_data = self.extract_episode_data(
                            plex_episode,
                            new_show.id if not existing_show else existing_show.id,
                        )
                        existing_episode = existing_episodes.get(
                            episode_data["plex_key"]
                        )

                        if existing_episode:
                            episode_data["id"] = existing_episode.id
                            episodes_to_update.append(episode_data)
                            logger.debug(
                                f"Updating existing episode: {episode_data['title']}"
                            )
                        else:
                            episodes_to_create.append(episode_data)
                            logger.info(f"Found new episode: {episode_data['title']}")

                except IntegrityError as e:
                    logger.error(
                        f"IntegrityError for show {show_data['title']}: {str(e)}"
                    )
                    continue

            with transaction.atomic():
                if shows_to_update:
                    Show.objects.bulk_update(
                        [Show(**data) for data in shows_to_update],
                        [
                            "title",
                            "summary",
                            "year",
                            "duration",
                            "poster_url",
                            "tmdb_id",
                            "rotten_tomatoes_rating",
                        ],
                    )
                if episodes_to_create:
                    Episode.objects.bulk_create(
                        [Episode(**data) for data in episodes_to_create]
                    )
                if episodes_to_update:
                    Episode.objects.bulk_update(
                        [Episode(**data) for data in episodes_to_update],
                        [
                            "title",
                            "summary",
                            "season_number",
                            "episode_number",
                            "duration",
                            "tmdb_id",
                            "rotten_tomatoes_rating",
                        ],
                    )

            logger.info("Show and episode sync completed successfully.")

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error while syncing: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")

    def process_show(self, plex_show, existing_shows, existing_episodes):
        try:
            show_data = self.extract_show_data(plex_show)
            plex_key = show_data["plex_key"]
            genres = ", ".join([g.tag for g in plex_show.genres])

            existing_show = existing_shows.get(plex_key)

            with transaction.atomic():
                if existing_show:
                    self.update_show(existing_show, show_data)
                else:
                    new_show = self.create_show(show_data)

                genre_objects = get_or_create_genres(genres)
                if existing_show:
                    existing_show.genres.set(genre_objects)
                else:
                    new_show.genres.set(genre_objects)

                self.process_episodes(
                    plex_show, existing_show or new_show, existing_episodes
                )

        except IntegrityError as e:
            logger.error(f"IntegrityError for show {show_data['title']}: {str(e)}")
        except Exception as e:
            logger.error(f"Error processing show {plex_show.title}: {str(e)}")

    def update_show(self, existing_show, show_data):
        for key, value in show_data.items():
            setattr(existing_show, key, value)
        existing_show.save()
        logger.debug(f"Updated existing show: {show_data['title']}")

    def create_show(self, show_data):
        new_show, created = Show.objects.get_or_create(
            plex_key=show_data["plex_key"], defaults=show_data
        )
        if created:
            logger.info(f"Created new show: {new_show.title}")
        else:
            logger.warning(f"Show already exists: {new_show.title}")
        return new_show

    def process_episodes(self, plex_show, db_show, existing_episodes):
        episodes_to_create = []
        episodes_to_update = []

        for plex_episode in plex_show.episodes():
            episode_data = self.extract_episode_data(plex_episode, db_show.id)
            existing_episode = existing_episodes.get(episode_data["plex_key"])

            if existing_episode:
                episode_data["id"] = existing_episode.id
                episodes_to_update.append(Episode(**episode_data))
                logger.debug(f"Updating existing episode: {episode_data['title']}")
            else:
                episodes_to_create.append(Episode(**episode_data))
                logger.info(f"Found new episode: {episode_data['title']}")

        with transaction.atomic():
            if episodes_to_create:
                Episode.objects.bulk_create(episodes_to_create)
            if episodes_to_update:
                Episode.objects.bulk_update(
                    episodes_to_update,
                    [
                        "title",
                        "summary",
                        "season_number",
                        "episode_number",
                        "duration",
                        "tmdb_id",
                        "rotten_tomatoes_rating",
                    ],
                )

    def extract_show_data(self, plex_show):
        retries = 3
        for attempt in range(retries):
            try:
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
                        plex_show.audienceRating * 10
                        if plex_show.audienceRating
                        else None
                    ),
                }
            except requests.exceptions.RequestException as e:
                logger.warning(
                    f"Error fetching show data (attempt {attempt + 1}): {str(e)}"
                )
                time.sleep(2)
        logger.error(f"Failed to fetch show data after {retries} attempts.")
        return {}

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
        }
