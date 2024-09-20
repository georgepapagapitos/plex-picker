import logging

from django.conf import settings
from django.shortcuts import render
from plexapi.server import PlexServer

from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


def fetch_plex_content(request):
    plex = PlexServer(settings.PLEX_URL, settings.PLEX_TOKEN)

    movies = plex.library.section("Movies").all()
    shows = plex.library.section("TV Shows").all()

    context = {"movies": movies, "shows": shows}

    return render(request, "picker/index.html", context)
