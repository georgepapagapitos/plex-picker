import time

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from plexapi.server import PlexServer

from sync.models.episode import Episode
from sync.models.show import Show
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


class Command(BaseCommand):
    # python manage.py sync_shows

    help = "Sync Plex TV shows and episodes to the local database"

    def handle(self, *args, **kwargs):
        try:
            # Connect to Plex server
            plex = PlexServer(settings.PLEX_URL, settings.PLEX_TOKEN)

            # Fetch the TV library section
            shows = plex.library.section("TV Shows").all()
            logger.info(f"Found {len(shows)} shows in Plex.")

            # Preload existing shows and episodes into dictionaries
            existing_shows = {show.plex_key: show for show in Show.objects.all()}
            existing_episodes = {
                episode.plex_key: episode for episode in Episode.objects.all()
            }

            shows_to_create = []
            shows_to_update = []
            episodes_to_create = []
            episodes_to_update = []

            for plex_show in shows:
                show_data = self.extract_show_data(plex_show)
                plex_key = show_data["plex_key"]

                if plex_key in existing_shows:
                    shows_to_update.append(show_data)
                    logger.debug(f"Found existing show in DB: {show_data['title']}")
                    show_id = existing_shows[plex_key].id  # Retrieve existing show ID
                else:
                    shows_to_create.append(show_data)
                    logger.info(f"Found new show: {show_data['title']}")
                    show_id = None  # Initially set to None

                # Ensure show is created or updated
                with transaction.atomic():
                    if show_id is None:  # If show is new, it needs to be created
                        new_show = Show(**show_data)
                        new_show.save()
                        show_id = new_show.id  # Get the ID of the newly created show
                        logger.info(f"Created new show: {new_show.title}")
                    else:
                        # Update the existing show
                        existing_show = existing_shows[plex_key]
                        for key, value in show_data.items():
                            setattr(existing_show, key, value)
                        existing_show.save()
                        logger.debug(f"Updated existing show: {existing_show.title}")

                # Now process episodes
                for plex_episode in plex_show.episodes():
                    episode_plex_key = plex_episode.ratingKey
                    existing_episode = existing_episodes.get(episode_plex_key)

                    episode_data = self.extract_episode_data(plex_episode, show_id)

                    if existing_episode:
                        episode_data["id"] = existing_episode.id
                        episodes_to_update.append(episode_data)
                        logger.debug(
                            f"Found existing episode in DB: {episode_data['title']} (S{episode_data['season_number']}E{episode_data['episode_number']})"
                        )
                    else:
                        episodes_to_create.append(episode_data)
                        logger.info(
                            f"Found new episode: {episode_data['title']} (S{episode_data['season_number']}E{episode_data['episode_number']})"
                        )

            # Perform bulk updates for shows and episodes
            with transaction.atomic():
                if shows_to_create:
                    Show.objects.bulk_create([Show(**data) for data in shows_to_create])
                for show_data in shows_to_update:
                    Show.objects.filter(id=show_data["id"]).update(**show_data)

                if episodes_to_create:
                    Episode.objects.bulk_create(
                        [Episode(**data) for data in episodes_to_create]
                    )
                for episode_data in episodes_to_update:
                    Episode.objects.filter(id=episode_data["id"]).update(**episode_data)

            logger.info("Show and episode sync completed successfully.")

        except Exception as e:
            logger.error(f"Error syncing shows and episodes: {str(e)}")

    def extract_show_data(self, plex_show):
        """Extract relevant show data from plex_show with retry logic."""
        retries = 3
        for attempt in range(retries):
            try:
                return {
                    "id": (
                        Show.objects.filter(plex_key=plex_show.ratingKey).first().id
                        if Show.objects.filter(plex_key=plex_show.ratingKey).exists()
                        else None
                    ),
                    "plex_key": plex_show.ratingKey,
                    "title": plex_show.title,
                    "summary": plex_show.summary,
                    "year": plex_show.year,
                    "duration": plex_show.duration,
                    "poster_url": plex_show.posterUrl,
                    "genres": ", ".join([g.tag for g in plex_show.genres]),
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
                time.sleep(2)  # Wait before retrying
        logger.error(f"Failed to fetch show data after {retries} attempts.")
        return {}  # Return an empty dict if all attempts fail

    def extract_episode_data(self, plex_episode, show_id):
        """Extract relevant episode data from plex_episode."""
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
            # 'id' will be added in the main loop if the episode already exists
        }
