import logging

from django.conf import settings
from django.shortcuts import render
from plexapi.server import PlexServer

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def fetch_plex_content(request):
    plex = PlexServer(settings.PLEX_URL, settings.PLEX_TOKEN)

    movies = plex.library.section("Movies").all()
    shows = plex.library.section("TV Shows").all()

    context = {"movies": movies, "shows": shows}

    return render(request, "picker/index.html", context)
