# Generated by Django 5.1.1 on 2024-09-29 04:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sync", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="movie",
            name="content_rating",
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
