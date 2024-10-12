# apps/sync/tests/test_show_model.py

from django.test import TestCase
from sync.models import Genre, Show


class ShowModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.action = Genre.objects.create(name="Action")
        cls.sci_fi = Genre.objects.create(name="Science Fiction")
        cls.drama = Genre.objects.create(name="Drama")
        cls.show = Show.objects.create(
            title="Stranger Things",
            summary="A group of kids uncover supernatural mysteries.",
            year=2016,
            duration=50 * 60 * 1000,
            poster_url="http://example.com/stranger_things.jpg",
            plex_key=1,
            tmdb_id=654321,
            rotten_tomatoes_rating=95,
        )
        cls.show.genres.add(cls.action, cls.sci_fi, cls.drama)

    def test_show_creation(self):
        self.assertEqual(self.show.title, "Stranger Things")
        self.assertEqual(self.show.year, 2016)

    def test_str_method(self):
        self.assertEqual(str(self.show), "Stranger Things (2016)")

    def test_show_genres(self):
        self.assertEqual(self.show.genres.count(), 3)
        self.assertIn(self.action, self.show.genres.all())
        self.assertIn(self.sci_fi, self.show.genres.all())
        self.assertIn(self.drama, self.show.genres.all())

    def test_formatted_duration(self):
        self.assertEqual(self.show.formatted_duration(), "50m")

    def test_formatted_genres(self):
        expected_genres = "Action, Science Fiction, Drama"
        self.assertEqual(self.show.formatted_genres(), expected_genres)
