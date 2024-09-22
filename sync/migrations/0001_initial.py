# Generated by Django 5.1.1 on 2024-09-22 17:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Movie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('summary', models.TextField(blank=True, null=True)),
                ('year', models.IntegerField(blank=True, null=True)),
                ('duration', models.IntegerField(blank=True, null=True)),
                ('poster_url', models.URLField(blank=True, null=True)),
                ('genres', models.TextField(blank=True, null=True)),
                ('plex_key', models.CharField(max_length=255, unique=True)),
                ('trailer_url', models.URLField(blank=True, null=True)),
                ('tmdb_id', models.PositiveIntegerField(blank=True, null=True)),
                ('rotten_tomatoes_rating', models.FloatField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Show',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('summary', models.TextField(blank=True, null=True)),
                ('year', models.IntegerField(blank=True, null=True)),
                ('duration', models.IntegerField(blank=True, null=True)),
                ('poster_url', models.URLField(blank=True, null=True)),
                ('genres', models.CharField(blank=True, max_length=255, null=True)),
                ('plex_key', models.IntegerField(unique=True)),
                ('tmdb_id', models.IntegerField(blank=True, null=True)),
                ('rotten_tomatoes_rating', models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Episode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('summary', models.TextField(blank=True, null=True)),
                ('season_number', models.IntegerField()),
                ('episode_number', models.IntegerField()),
                ('duration', models.IntegerField(blank=True, null=True)),
                ('plex_key', models.IntegerField(unique=True)),
                ('tmdb_id', models.IntegerField(blank=True, null=True)),
                ('rotten_tomatoes_rating', models.IntegerField(blank=True, null=True)),
                ('show', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='episodes', to='sync.show')),
            ],
        ),
    ]
