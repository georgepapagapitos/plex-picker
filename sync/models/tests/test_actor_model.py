# sync/models/tests/test_actor_model.py

from django.db import IntegrityError
from django.test import TestCase

from sync.models import Actor, Movie, Show


class ActorModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.actor = Actor.objects.create(
            first_name="John",
            last_name="Doe",
            photo_url="http://example.com/photo.jpg",
            tmdb_id=12345,
        )

    def test_actor_creation(self):
        self.assertEqual(str(self.actor), "John Doe")
        self.assertEqual(self.actor.full_name, "John Doe")

    def test_actor_with_only_first_name(self):
        actor = Actor.objects.create(first_name="Madonna")
        self.assertEqual(str(actor), "Madonna ")
        self.assertEqual(actor.full_name, "Madonna ")

    def test_actor_with_only_last_name(self):
        actor = Actor.objects.create(last_name="Cher")
        self.assertEqual(str(actor), " Cher")
        self.assertEqual(actor.full_name, " Cher")

    def test_actor_photo_url_optional(self):
        actor = Actor.objects.create(first_name="Jane", last_name="Smith")
        self.assertIsNone(actor.photo_url)

    def test_actor_tmdb_id_unique(self):
        with self.assertRaises(IntegrityError):
            Actor.objects.create(
                first_name="Jane", last_name="Doe", tmdb_id=12345  # Same as self.actor
            )

    def test_actor_movie_relationship(self):
        movie = Movie.objects.create(title="Test Movie", year=2023)
        self.actor.movies.add(movie)
        self.assertIn(movie, self.actor.movies.all())

    def test_actor_show_relationship(self):
        show = Show.objects.create(title="Test Show", year=2023)
        self.actor.shows.add(show)
        self.assertIn(show, self.actor.shows.all())

    def test_actor_ordering(self):
        Actor.objects.create(first_name="Alice", last_name="Smith", tmdb_id=54321)
        Actor.objects.create(first_name="Bob", last_name="Johnson", tmdb_id=67890)
        actors = Actor.objects.all()
        self.assertEqual(actors[0].last_name, "Doe")  # Our setUp actor
        self.assertEqual(actors[1].last_name, "Johnson")
        self.assertEqual(actors[2].last_name, "Smith")

    def test_actor_without_tmdb_id(self):
        actor = Actor.objects.create(first_name="No", last_name="TMDB")
        self.assertIsNone(actor.tmdb_id)

    def test_actor_update(self):
        self.actor.first_name = "Johnny"
        self.actor.save()
        updated_actor = Actor.objects.get(id=self.actor.id)
        self.assertEqual(updated_actor.first_name, "Johnny")
