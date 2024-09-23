from django.forms import ValidationError
from django.test import TestCase

from sync.models.episode import Episode
from sync.models.show import Show


class EpisodeModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create a show for the episode
        cls.show = Show.objects.create(
            title="Stranger Things",
            summary="A group of kids uncover supernatural mysteries.",
            year=2016,
            duration=50 * 60 * 1000,  # 50 minutes in milliseconds
            poster_url="http://example.com/stranger_things.jpg",
            plex_key=1,
            tmdb_id=654321,
            rotten_tomatoes_rating=95,
        )

        # Create an episode with duration in milliseconds
        cls.episode = Episode.objects.create(
            show=cls.show,
            title="Chapter One: Stranger Things",
            summary="The disappearance of a young boy unleashes a series of supernatural events.",
            season_number=1,
            episode_number=1,
            duration=50 * 60 * 1000,  # 50 minutes in milliseconds
            plex_key=2,
            tmdb_id=123,
            rotten_tomatoes_rating=90,
        )

    def test_episode_creation(self):
        self.assertEqual(self.episode.title, "Chapter One: Stranger Things")
        self.assertEqual(self.episode.season_number, 1)
        self.assertEqual(self.episode.episode_number, 1)
        self.assertEqual(self.episode.show.title, "Stranger Things")

    def test_str_method(self):
        expected_str = "Stranger Things - S01E01: Chapter One: Stranger Things"
        self.assertEqual(str(self.episode), expected_str)

    def test_formatted_duration(self):
        self.assertEqual(
            self.episode.formatted_duration(), "50m"
        )  # Should be formatted correctly

    def test_show_association(self):
        self.assertEqual(self.episode.show, self.show)
        self.assertEqual(self.episode.show.title, "Stranger Things")

    def test_clean_method(self):
        # Test that validation works correctly
        self.episode.rotten_tomatoes_rating = 105  # Invalid rating
        with self.assertRaises(ValidationError):
            self.episode.clean()

        self.episode.rotten_tomatoes_rating = 90  # Valid rating
        self.episode.season_number = 0  # Invalid season number
        with self.assertRaises(ValidationError):
            self.episode.clean()

        self.episode.season_number = 1  # Valid season number
        self.episode.episode_number = 0  # Invalid episode number
        with self.assertRaises(ValidationError):
            self.episode.clean()
