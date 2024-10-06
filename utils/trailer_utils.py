# utils/trailer_utils.py

from typing import Optional

import googleapiclient.discovery
import requests

from sync.models.movie import Movie
from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


class TrailerFetcher:
    def __init__(
        self,
        tmdb_api_url,
        tmdb_api_key,
        youtube_api_key,
    ):
        self.tmdb_api_url = tmdb_api_url
        self.tmdb_api_key = tmdb_api_key
        self.youtube_api_key = youtube_api_key
        self._youtube = None

    @property
    def youtube(self):
        if self._youtube is None:
            self._youtube = googleapiclient.discovery.build(
                "youtube", "v3", developerKey=self.youtube_api_key
            )
        return self._youtube

    def get_tmdb_trailer_url(self, movie_id: int) -> Optional[str]:
        try:
            response = requests.get(
                f"{self.tmdb_api_url}/movie/{movie_id}/videos",
                params={"api_key": self.tmdb_api_key},
                timeout=10,  # Add a timeout
            )
            response.raise_for_status()
            data = response.json()
            for video in data.get("results", []):
                if video["type"] == "Trailer" and video["site"].lower() == "youtube":
                    return f"https://www.youtube.com/embed/{video['key']}"
        except requests.RequestException as e:
            logger.error(f"TMDB API request failed for movie ID {movie_id}: {str(e)}")
        return None

    def get_youtube_trailer_url(self, movie_title: str) -> Optional[str]:
        try:
            request = self.youtube.search().list(
                q=f"{movie_title} official trailer",
                part="id,snippet",
                type="video",
                videoCategoryId="1",  # 1 is the category for movies & entertainment
                maxResults=5,  # Limit the number of results
            )
            response = request.execute()
            for item in response.get("items", []):
                if "trailer" in item["snippet"]["title"].lower():
                    return f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        except Exception as e:
            logger.error(f"YouTube API request failed for {movie_title}: {str(e)}")
        return None

    def fetch_trailer_url(self, movie: Movie) -> Optional[str]:
        if not movie.trailer_url:
            logger.debug(
                f"Fetching trailer URL for {movie.title} (TMDB ID: {movie.tmdb_id})"
            )
            if movie.tmdb_id:
                movie.trailer_url = self.get_tmdb_trailer_url(movie.tmdb_id)
            if not movie.trailer_url:
                movie.trailer_url = self.get_youtube_trailer_url(movie.title)
            if movie.trailer_url:
                logger.debug(f"Trailer URL found: {movie.trailer_url}")
                movie.save(update_fields=["trailer_url"])
            else:
                logger.warning(f"No trailer URL found for {movie.title}.")
        else:
            logger.debug(
                f"Existing trailer URL found for {movie.title}: {movie.trailer_url}"
            )
        return movie.trailer_url
