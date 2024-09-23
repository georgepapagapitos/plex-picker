from unittest.mock import patch

import requests
from django.test import TestCase

from sync.models.movie import Movie
from utils.trailer_utils import fetch_trailer_url, get_tmdb_trailer_url


class TestTrailerUtils(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.movie1 = Movie.objects.create(
            title="Movie 1", genres="Action, Comedy", tmdb_id=1, plex_key="plex_key_1"
        )
        cls.movie2 = Movie.objects.create(
            title="Movie 2", genres="Action", tmdb_id=2, plex_key="plex_key_2"
        )

    def test_fetch_trailer_url_existing(self):
        self.movie1.trailer_url = "http://existing_trailer.com"
        self.movie1.save()

        trailer_url = fetch_trailer_url(self.movie1)
        self.assertEqual(trailer_url, "http://existing_trailer.com")
        self.assertEqual(self.movie1.trailer_url, "http://existing_trailer.com")

    def test_fetch_trailer_url_new(self):
        self.movie2.trailer_url = None
        self.movie2.tmdb_id = 123
        self.movie2.save()

        with patch("utils.trailer_utils.get_tmdb_trailer_url") as mock_tmdb:
            mock_tmdb.return_value = "https://tmdb_trailer.com"
            trailer_url = fetch_trailer_url(self.movie2)

        self.assertEqual(trailer_url, "https://tmdb_trailer.com")
        self.assertEqual(self.movie2.trailer_url, "https://tmdb_trailer.com")

    @patch("utils.trailer_utils.requests.get")
    def test_get_tmdb_trailer_url_success(self, mock_get):
        # Arrange
        mock_response = {
            "results": [
                {"type": "Trailer", "key": "video_id"},
            ]
        }
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        # Act
        trailer_url = get_tmdb_trailer_url(123)

        # Assert
        self.assertEqual(trailer_url, "https://www.youtube.com/embed/video_id")

    @patch("utils.trailer_utils.requests.get")
    def test_get_tmdb_trailer_url_no_trailer(self, mock_get):
        # Arrange
        mock_response = {"results": []}
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.status_code = 200

        # Act
        trailer_url = get_tmdb_trailer_url(123)

        # Assert
        self.assertIsNone(trailer_url)

    @patch("utils.trailer_utils.requests.get")
    def test_get_tmdb_trailer_url_failure(self, mock_get):
        # Arrange
        mock_get.side_effect = requests.RequestException("Network error")

        # Act
        trailer_url = get_tmdb_trailer_url(123)

        # Assert
        self.assertIsNone(trailer_url)
