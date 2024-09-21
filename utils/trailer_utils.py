# trailer_utils.py
import googleapiclient.discovery
import requests
from django.conf import settings

from utils.logger_utils import setup_logging

# Set up logging
logger = setup_logging(__name__)


def get_tmdb_trailer_url(movie_id):
    try:
        response = requests.get(
            f"{settings.TMDB_API_URL}/movie/{movie_id}/videos",
            params={"api_key": settings.TMDB_API_KEY},
        )
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()

        for video in data.get("results", []):
            if video["type"] == "Trailer":
                return f"https://www.youtube.com/embed/{video['key']}"

    except requests.RequestException as e:
        logger.error(f"TMDB API request failed: {str(e)}")

    return None


def get_youtube_trailer_url(movie_title):
    try:
        youtube = googleapiclient.discovery.build(
            "youtube",
            "v3",
            developerKey=settings.YOUTUBE_API_KEY,
        )

        request = youtube.search().list(
            q=f"{movie_title} trailer",
            part="id,snippet",
            type="video",
            videoCategoryId="1",  # 1 is the category for movies & entertainment
        )
        response = request.execute()

        for item in response.get("items", []):
            if "trailer" in item["snippet"]["title"].lower():
                return f"https://www.youtube.com/watch?v={item['id']['videoId']}"

    except Exception as e:
        logger.error(f"YouTube API request failed: {str(e)}")

    return None
