# sync/management/commands/optimize_existing_media.py


from django.core.management.base import BaseCommand

from sync.models import Movie, Show


class Command(BaseCommand):
    help = "Optimize existing movie and show posters and art"

    def handle(self, *args, **options):
        for movie in Movie.objects.all():
            movie.optimize_images()
            self.stdout.write(
                self.style.SUCCESS(f"Optimized images for movie: {movie.title}")
            )

        for show in Show.objects.all():
            show.optimize_images()
            self.stdout.write(
                self.style.SUCCESS(f"Optimized images for show: {show.title}")
            )
