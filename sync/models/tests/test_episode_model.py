from django.test import TestCase

from sync.models.episode import Episode
from sync.models.show import Show


class EpisodeModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.show = Show.objects.create(
            title="Stranger Things",
            summary="A group of kids uncover supernatural mysteries.",
            year=2016,
            duration=50,
            poster_url="http://example.com/stranger_things.jpg",
            genres="Drama, Fantasy",
            plex_key=1,
            tmdb_id=654321,
            rotten_tomatoes_rating=95,
        )
        cls.episode = Episode.objects.create(
            show=cls.show,
            title="Chapter One: Stranger Things",
            summary="The disappearance of a young boy unleashes a series of supernatural events.",
            season_number=1,
            episode_number=1,
            duration=50,
            plex_key=1,
            tmdb_id=123,
            rotten_tomatoes_rating=90,
        )

    def test_episode_creation(self):
        self.assertEqual(self.episode.title, "Chapter One: Stranger Things")
        self.assertEqual(self.episode.season_number, 1)
        self.assertEqual(self.episode.show.title, "Stranger Things")

    def test_str_method(self):
        self.assertEqual(
            str(self.episode), "Stranger Things - S1E1: Chapter One: Stranger Things"
        )
