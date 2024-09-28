# utils/tests/test_trailer_utils.py

from unittest.mock import MagicMock, patch

from django.test import TestCase, override_settings

from sync.models.genre import Genre
from sync.models.movie import Movie
from utils.trailer_utils import trailer_fetcher


@override_settings(
    TMDB_API_URL="http://test.tmdb.api",
    TMDB_API_KEY="test_tmdb_key",
    YOUTUBE_API_KEY="test_youtube_key",
)
class TestTrailerUtils(TestCase):
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
        Movie.objects.filter(title="Movie 1").first().genres.add(action)
        Movie.objects.filter(title="Movie 2").first().genres.add(comedy)

    def setUp(self):
        # Use the singleton instance for each test
        self.trailer_fetcher = trailer_fetcher

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

    # ... (rest of the test methods remain the same)
