# test_trailer_utils.py
import unittest
from unittest.mock import MagicMock, patch

import requests
from django.conf import settings

from utils.trailer_utils import get_tmdb_trailer_url, get_youtube_trailer_url


class TestTrailerUtils(unittest.TestCase):

    @patch("utils.trailer_utils.requests.get")
    def test_get_tmdb_trailer_url_success(self, mock_get):
        # Mock the response from TMDB
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [{"type": "Trailer", "key": "trailer_key"}]
        }
        mock_response.raise_for_status = MagicMock()  # No exception raised
        mock_get.return_value = mock_response

        result = get_tmdb_trailer_url(123)
        self.assertEqual(result, "https://www.youtube.com/embed/trailer_key")
        mock_get.assert_called_once()

    @patch("utils.trailer_utils.requests.get")
    def test_get_tmdb_trailer_url_no_trailer(self, mock_get):
        # Mock the response with no trailers
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()  # No exception raised
        mock_get.return_value = mock_response

        result = get_tmdb_trailer_url(123)
        self.assertIsNone(result)
        mock_get.assert_called_once()

    @patch("utils.trailer_utils.requests.get")
    def test_get_tmdb_trailer_url_request_exception(self, mock_get):
        # Mock a request exception
        mock_get.side_effect = requests.RequestException("Network error")

        result = get_tmdb_trailer_url(123)
        self.assertIsNone(result)
        mock_get.assert_called_once()

    @patch("googleapiclient.discovery.build")
    def test_get_youtube_trailer_url_success(self, mock_build):
        # Mock the YouTube API client
        mock_youtube = MagicMock()

        # Create a mock request that has an `execute` method
        mock_request = MagicMock()
        mock_request.execute.return_value = {
            "items": [
                {"id": {"videoId": "video_id"}, "snippet": {"title": "Movie Trailer"}}
            ]
        }

        # Set up the mock chain: mock_youtube.search().list() returns mock_request
        mock_youtube.search.return_value.list.return_value = mock_request

        # Configure the build mock to return our mock_youtube
        mock_build.return_value = mock_youtube

        result = get_youtube_trailer_url("Movie Title")

        # Debugging output
        print(f"Result: {result}")
        print(f"Called with: {mock_build.call_args}")

        self.assertEqual(result, "https://www.youtube.com/watch?v=video_id")
        mock_build.assert_called_once_with(
            "youtube", "v3", developerKey=settings.YOUTUBE_API_KEY
        )

    @patch("googleapiclient.discovery.build")
    def test_get_youtube_trailer_url_no_trailer(self, mock_build):
        # Mock the response with no trailers
        mock_youtube = MagicMock()
        mock_request = MagicMock()
        mock_request.execute.return_value = {"items": []}
        mock_youtube.search.return_value = mock_request
        mock_build.return_value = mock_youtube

        result = get_youtube_trailer_url("Movie Title")
        self.assertIsNone(result)
        mock_build.assert_called_once()

    @patch("googleapiclient.discovery.build")
    def test_get_youtube_trailer_url_exception(self, mock_build):
        # Mock an exception during YouTube API call
        mock_build.side_effect = Exception("API error")

        result = get_youtube_trailer_url("Movie Title")
        self.assertIsNone(result)
        mock_build.assert_called_once()
