# tests/utils/test_trailer_utils.py

import unittest
from unittest.mock import MagicMock, patch

import requests
from django.conf import settings
from django.test import TestCase, override_settings

from sync.models.genre import Genre
from sync.models.movie import Movie
from utils.trailer_utils import TrailerFetcher


@override_settings(
    TMDB_API_URL="http://test.tmdb.api",
    TMDB_API_KEY="test_tmdb_key",
    YOUTUBE_API_KEY="test_youtube_key",
)
class TestTrailerFetcher(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create Genre instances
        action = Genre.objects.create(name="Action")
        comedy = Genre.objects.create(name="Comedy")
        cls.movie1 = Movie.objects.create(
            title="Movie 1",
            tmdb_id=1,
            plex_key="action_1",
        )
        cls.movie2 = Movie.objects.create(
            title="Movie 2",
            tmdb_id=2,
            plex_key="comedy_1",
        )
        cls.movie1.genres.add(action)
        cls.movie2.genres.add(comedy)

    def setUp(self):
        self.trailer_fetcher = TrailerFetcher(
            tmdb_api_url=settings.TMDB_API_URL,
            tmdb_api_key=settings.TMDB_API_KEY,
            youtube_api_key=settings.YOUTUBE_API_KEY,
        )

    @patch("utils.trailer_utils.requests.get")
    def test_get_tmdb_trailer_url_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{"type": "Trailer", "site": "YouTube", "key": "abc123"}]
        }
        mock_get.return_value = mock_response

        trailer_url = self.trailer_fetcher.get_tmdb_trailer_url(1)
        self.assertEqual(trailer_url, "https://www.youtube.com/embed/abc123")
        mock_get.assert_called_once_with(
            "http://test.tmdb.api/movie/1/videos",
            params={"api_key": "test_tmdb_key"},
            timeout=10,
        )

    @patch("utils.trailer_utils.requests.get")
    def test_get_tmdb_trailer_url_failure(self, mock_get):
        mock_get.side_effect = requests.RequestException("API Error")

        trailer_url = self.trailer_fetcher.get_tmdb_trailer_url(1)
        self.assertIsNone(trailer_url)

    @patch("utils.trailer_utils.googleapiclient.discovery.build")
    def test_get_youtube_trailer_url_success(self, mock_build):
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_search = MagicMock()
        mock_youtube.search.return_value.list.return_value = mock_search
        mock_search.execute.return_value = {
            "items": [
                {
                    "id": {"videoId": "xyz789"},
                    "snippet": {"title": "Movie Title Official Trailer"},
                }
            ]
        }

        trailer_url = self.trailer_fetcher.get_youtube_trailer_url("Movie Title")
        self.assertEqual(trailer_url, "https://www.youtube.com/watch?v=xyz789")
        mock_youtube.search.assert_called_once()
        mock_search.execute.assert_called_once()

    @patch("utils.trailer_utils.googleapiclient.discovery.build")
    def test_get_youtube_trailer_url_failure(self, mock_build):
        mock_youtube = MagicMock()
        mock_build.return_value = mock_youtube
        mock_search = MagicMock()
        mock_youtube.search.return_value.list.return_value = mock_search
        mock_search.execute.side_effect = Exception("API Error")

        trailer_url = self.trailer_fetcher.get_youtube_trailer_url("Movie Title")
        self.assertIsNone(trailer_url)
        mock_youtube.search.assert_called_once()
        mock_search.execute.assert_called_once()

    @patch.object(TrailerFetcher, "get_tmdb_trailer_url")
    @patch.object(TrailerFetcher, "get_youtube_trailer_url")
    def test_fetch_trailer_url_tmdb_success(self, mock_youtube, mock_tmdb):
        mock_tmdb.return_value = "https://www.youtube.com/embed/abc123"
        mock_youtube.return_value = None

        trailer_url = self.trailer_fetcher.fetch_trailer_url(self.movie1)
        self.assertEqual(trailer_url, "https://www.youtube.com/embed/abc123")
        self.assertEqual(
            self.movie1.trailer_url, "https://www.youtube.com/embed/abc123"
        )
        mock_tmdb.assert_called_once_with(1)
        mock_youtube.assert_not_called()

    @patch.object(TrailerFetcher, "get_tmdb_trailer_url")
    @patch.object(TrailerFetcher, "get_youtube_trailer_url")
    def test_fetch_trailer_url_youtube_fallback(self, mock_youtube, mock_tmdb):
        mock_tmdb.return_value = None
        mock_youtube.return_value = "https://www.youtube.com/watch?v=xyz789"

        trailer_url = self.trailer_fetcher.fetch_trailer_url(self.movie1)
        self.assertEqual(trailer_url, "https://www.youtube.com/watch?v=xyz789")
        self.assertEqual(
            self.movie1.trailer_url, "https://www.youtube.com/watch?v=xyz789"
        )
        mock_tmdb.assert_called_once_with(1)
        mock_youtube.assert_called_once_with("Movie 1")

    @patch.object(TrailerFetcher, "get_tmdb_trailer_url")
    @patch.object(TrailerFetcher, "get_youtube_trailer_url")
    def test_fetch_trailer_url_no_trailer_found(self, mock_youtube, mock_tmdb):
        mock_tmdb.return_value = None
        mock_youtube.return_value = None

        trailer_url = self.trailer_fetcher.fetch_trailer_url(self.movie1)
        self.assertIsNone(trailer_url)
        self.assertIsNone(self.movie1.trailer_url)
        mock_tmdb.assert_called_once_with(1)
        mock_youtube.assert_called_once_with("Movie 1")

    def test_fetch_trailer_url_existing_url(self):
        self.movie1.trailer_url = "https://www.youtube.com/watch?v=existing123"
        self.movie1.save()

        trailer_url = self.trailer_fetcher.fetch_trailer_url(self.movie1)
        self.assertEqual(trailer_url, "https://www.youtube.com/watch?v=existing123")
