# Generated by Django 5.1.1 on 2024-09-21 01:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('sync', '0004_movie_imdb_rating_movie_rotten_tomatoes_rating'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='movie',
            name='imdb_rating',
        ),
        migrations.RemoveField(
            model_name='movie',
            name='rating',
        ),
    ]
