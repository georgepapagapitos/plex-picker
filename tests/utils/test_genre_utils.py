# tests/utils/test_genre_utils.py

from unittest.mock import patch

from django.db import IntegrityError
from django.test import TestCase

from sync.models.genre import Genre
from utils.genre_utils import get_or_create_genres


class TestGenreUtils(TestCase):
    def setUp(self):
        # Create some initial genres
        Genre.objects.create(name="Action")
        Genre.objects.create(name="Comedy")

    def test_get_existing_genres(self):
        genres = get_or_create_genres("Action, Comedy")
        self.assertEqual(len(genres), 2)
        genre_names = set(genre.name for genre in genres)
        self.assertEqual(genre_names, {"Action", "Comedy"})

    def test_create_new_genre(self):
        genres = get_or_create_genres("Drama")
        self.assertEqual(len(genres), 1)
        self.assertEqual(genres[0].name, "Drama")

    def test_mixed_existing_and_new_genres(self):
        genres = get_or_create_genres("Action, Drama, Sci-Fi")
        self.assertEqual(len(genres), 3)
        self.assertEqual(set(g.name for g in genres), {"Action", "Drama", "Sci-Fi"})

    def test_duplicate_genres_in_input(self):
        genres = get_or_create_genres("Action, Comedy, Action, Comedy")
        self.assertEqual(len(genres), 2)
        self.assertEqual(set(g.name for g in genres), {"Action", "Comedy"})

    def test_empty_input(self):
        genres = get_or_create_genres("")
        self.assertEqual(len(genres), 0)

    def test_whitespace_handling(self):
        genres = get_or_create_genres(" Action ,  Comedy  , Drama ")
        self.assertEqual(len(genres), 3)
        self.assertEqual(set(g.name for g in genres), {"Action", "Comedy", "Drama"})

    @patch("utils.genre_utils.logger")
    def test_logging(self, mock_logger):
        get_or_create_genres("Action, Drama")
        mock_logger.debug.assert_called()
        mock_logger.info.assert_called_with("Created new genre: Drama")

    def test_integrity_error_handling(self):
        # Simulate an IntegrityError
        with patch(
            "sync.models.genre.Genre.objects.get_or_create"
        ) as mock_get_or_create:
            mock_get_or_create.side_effect = IntegrityError("Duplicate entry")
            genres = get_or_create_genres("Action")
            self.assertEqual(len(genres), 0)

    def test_case_sensitivity(self):
        genres = get_or_create_genres("action, COMEDY, Drama")
        self.assertEqual(len(genres), 3)
        self.assertEqual(set(g.name for g in genres), {"action", "COMEDY", "Drama"})

    def test_non_ascii_characters(self):
        genres = get_or_create_genres("Sci-Fi, Animé, 电影")
        self.assertEqual(len(genres), 3)
        self.assertEqual(set(g.name for g in genres), {"Sci-Fi", "Animé", "电影"})
