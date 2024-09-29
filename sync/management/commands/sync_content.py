# sync/management/commands/sync_content.py

from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import BaseCommand

from utils.logger_utils import setup_logging

logger = setup_logging(__name__)
LOCK_EXPIRE = 60 * 5  # Lock expires in 5 minutes


class Command(BaseCommand):
    help = "Sync Plex movies and TV shows with database locking"

    def add_arguments(self, parser):
        parser.add_argument(
            "--movies-only",
            action="store_true",
            help="Sync only movies",
        )
        parser.add_argument(
            "--shows-only",
            action="store_true",
            help="Sync only TV shows",
        )

    def handle(self, *args, **options):
        movies_only = options["movies_only"]
        shows_only = options["shows_only"]

        if movies_only and shows_only:
            logger.warning(
                "Both --movies-only and --shows-only flags are set. This will result in no sync operation."
            )
            return

        if movies_only:
            logger.info("Starting sync for movies only.")
        elif shows_only:
            logger.info("Starting sync for shows only.")
        else:
            logger.info("Starting combined sync for movies and shows.")

        try:
            tasks = []
            if not shows_only:
                tasks.append(("Sync Movies", "sync_movies"))
            if not movies_only:
                tasks.append(("Sync Shows", "sync_shows"))

            if not tasks:
                logger.warning(
                    "No sync tasks selected. Please run without --movies-only or --shows-only, or use the individual sync commands."
                )
                return

            for task_name, task_command in tasks:
                self.run_task_with_lock(
                    task_name, task_command, movies_only, shows_only
                )

            if movies_only:
                logger.info("Sync for movies completed.")
            elif shows_only:
                logger.info("Sync for shows completed.")
            else:
                logger.info("Combined sync for movies and shows completed.")

        except Exception as e:
            if movies_only:
                logger.error(f"Error during movies sync: {str(e)}")
            elif shows_only:
                logger.error(f"Error during shows sync: {str(e)}")
            else:
                logger.error(f"Error during combined sync: {str(e)}")

    def run_task_with_lock(self, task_name, task_command, movies_only, shows_only):
        lock_id = f"lock_{task_command}"
        acquire_lock = lambda: cache.add(lock_id, "true", LOCK_EXPIRE)
        release_lock = lambda: cache.delete(lock_id)
        got_lock = acquire_lock()

        if got_lock:
            try:
                logger.info(f"Starting {task_name}")
                call_command(task_command)
                if (movies_only and task_command == "sync_movies") or (
                    shows_only and task_command == "sync_shows"
                ):
                    logger.info(f"{task_name} completed successfully.")
                elif not movies_only and not shows_only:
                    logger.info(f"{task_name} completed successfully.")
            finally:
                release_lock()
        else:
            logger.warning(
                f"{task_name} is already being run by another process. Skipping."
            )
