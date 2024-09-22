from django.test import TestCase

from sync.models.show import Show


class ShowModelTests(TestCase):
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

    def test_show_creation(self):
        self.assertEqual(self.show.title, "Stranger Things")
        self.assertEqual(self.show.year, 2016)

    def test_str_method(self):
        self.assertEqual(str(self.show), "Stranger Things (2016)")
