# sync/management/commands/sync_content.py

import concurrent.futures

from django.core.management.base import BaseCommand

from sync.management.commands.sync_movies import Command as SyncMoviesCommand
from sync.management.commands.sync_shows import Command as SyncShowsCommand
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


class Command(BaseCommand):
    # python manage.py sync_content

    help = "Sync Plex movies and TV shows in parallel"

    def handle(self, *args, **kwargs):
        logger.info("Starting combined sync for movies and shows.")
        try:
            # Create the movie and show sync command objects
            sync_movies_command = SyncMoviesCommand()
            sync_shows_command = SyncShowsCommand()

            # Define the tasks to run in parallel
            tasks = {
                "Sync Movies": sync_movies_command.handle,
                "Sync Shows": sync_shows_command.handle,
            }

            # Use ThreadPoolExecutor to run tasks in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                # Submit tasks to the executor
                futures = {executor.submit(task): name for name, task in tasks.items()}

                for future in concurrent.futures.as_completed(futures):
                    task_name = futures[future]
                    try:
                        # Wait for each future to complete and log the result
                        future.result()
                        logger.info(f"{task_name} completed successfully.")
                    except Exception as exc:
                        logger.error(f"{task_name} generated an exception: {exc}")

            logger.info("Combined sync for movies and shows completed.")

        except Exception as e:
            logger.error(f"Error during combined sync: {str(e)}")
