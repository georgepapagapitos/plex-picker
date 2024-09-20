import logging
import random

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from picker.utils.trailer_utils import get_tmdb_trailer_url, get_youtube_trailer_url
from sync.models import Movie

logger = logging.getLogger(__name__)


def fetch_random_movie(request):
    try:
        selected_genre = request.GET.get("genre", "")
        count = int(request.GET.get("count", 1))
        randomize = request.GET.get("randomize", "false")
        movie_ids = request.GET.get("movies", "")

        genres = sorted(
            set(
                genre.strip()
                for movie in Movie.objects.all()
                for genre in movie.genres.split(",")
                if genre.strip()
            )
        )

        if randomize.lower() == "true" or not movie_ids:
            if selected_genre:
                movies = Movie.objects.filter(genres__icontains=selected_genre)
            else:
                movies = Movie.objects.all()

            if movies.exists():
                selected_movies = random.sample(
                    list(movies), min(count, movies.count())
                )
                movie_ids = ",".join(str(movie.id) for movie in selected_movies)

                # Redirect to the same view with selected movie IDs in the URL
                base_url = reverse("fetch_random_movie")
                url = f"{base_url}?genre={selected_genre}&count={count}&movies={movie_ids}"
                return HttpResponseRedirect(url)
            else:
                selected_movies = []
        else:
            # Retrieve movies from URL parameters
            movie_id_list = [int(id) for id in movie_ids.split(",") if id.isdigit()]
            selected_movies = list(Movie.objects.filter(id__in=movie_id_list))

        # Fetch and save trailer URLs
        for movie in selected_movies:
            if not movie.trailer_url:
                trailer_url = get_tmdb_trailer_url(movie.tmdb_id)
                if not trailer_url:
                    trailer_url = get_youtube_trailer_url(movie.title)
                movie.trailer_url = trailer_url
                movie.save()

        context = {
            "movies": selected_movies,
            "genres": genres,
            "selected_genre": selected_genre,
            "count": count,
            "movie_ids": movie_ids,
        }
        return render(request, "picker/random_movie.html", context)

    except Exception as e:
        logger.error(f"Error fetching random movie: {str(e)}")
        return render(request, "error.html", {"error": str(e)})
