# apps/sync/tests/test_genre_model.py

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from sync.models.genre import Genre


class GenreModelTest(TestCase):
    def test_genre_creation(self):
        genre = Genre.objects.create(name="Action")
        self.assertEqual(str(genre), "Action")

    def test_genre_unique_constraint(self):
        Genre.objects.create(name="Comedy")
        with self.assertRaises(IntegrityError):
            Genre.objects.create(name="Comedy")

    def test_genre_max_length(self):
        long_name = "A" * 101
        with self.assertRaises(ValidationError):
            genre = Genre(name=long_name)
            genre.full_clean()
