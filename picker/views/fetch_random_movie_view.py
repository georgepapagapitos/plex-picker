import logging
import random

import googleapiclient.discovery
import requests
from django.conf import settings
from django.shortcuts import render

from sync.models import Movie

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


def get_tmdb_trailer_url(movie_id):
    try:
        response = requests.get(
            f"https://api.themoviedb.org/3/movie/{movie_id}/videos",
            params={"api_key": settings.TMDB_API_KEY},
        )
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()

        for video in data.get("results", []):
            if video["type"] == "Trailer":
                return f"https://www.youtube.com/watch?v={video['key']}"

    except requests.RequestException as e:
        logger.error(f"TMDB API request failed: {str(e)}")

    return None


def get_youtube_trailer_url(movie_title):
    try:
        youtube = googleapiclient.discovery.build(
            "youtube",
            "v3",
            developerKey=settings.YOUTUBE_API_KEY,
        )

        request = youtube.search().list(
            q=f"{movie_title} trailer",
            part="id,snippet",
            type="video",
            videoCategoryId="1",  # 1 is the category for movies & entertainment
        )
        response = request.execute()

        for item in response.get("items", []):
            if "trailer" in item["snippet"]["title"].lower():
                return f"https://www.youtube.com/watch?v={item['id']['videoId']}"

    except Exception as e:
        logger.error(f"YouTube API request failed: {str(e)}")

    return None


def fetch_random_movie(request):
    try:
        # Get genre from request parameters
        selected_genre = request.GET.get("genre", None)
        count = int(request.GET.get("count", 1))  # Number of movies to display
        logger.debug(f"Selected genre: {selected_genre}")
        logger.debug(f"Number of movies to display: {count}")

        # Retrieve and sort unique genres, filtering out empty strings
        genres = sorted(
            set(
                genre.strip()
                for movie in Movie.objects.all()
                for genre in movie.genres.split(",")
                if genre.strip()
            )
        )

        # Filter movies by genre if provided, else return all movies
        if selected_genre:
            movies = Movie.objects.filter(genres__icontains=selected_genre)
            logger.debug(f"Filtered movies count: {movies.count()}")
        else:
            movies = Movie.objects.all()
            logger.debug(f"No genre selected, showing all movies: {movies.count()}")

        # Pick random movies from the filtered movies
        if movies.exists():
            selected_movies = random.sample(list(movies), min(count, movies.count()))
            logger.debug(
                f"Selected movies: {[movie.title for movie in selected_movies]}"
            )

            # Fetch and save trailer URLs
            for movie in selected_movies:
                if not movie.trailer_url:
                    trailer_url = get_tmdb_trailer_url(movie.tmdb_id)
                    if not trailer_url:
                        trailer_url = get_youtube_trailer_url(movie.title)
                    movie.trailer_url = trailer_url
                    movie.save()
        else:
            selected_movies = []
            logger.debug("No movies found after filtering")
            return render(
                request,
                "picker/random_movie.html",
                {
                    "movies": [],
                    "genres": genres,
                    "selected_genre": selected_genre,
                    "count": count,
                },
            )
    except Exception as e:
        # Log error and render error template with exception message
        logger.error(f"Error fetching random movie: {str(e)}")
        return render(request, "picker/error.html", {"error": str(e)})

    # Ensure context is passed correctly to the template
    context = {
        "movies": selected_movies,
        "genres": genres,
        "selected_genre": selected_genre,
        "count": count,
    }
    return render(request, "picker/random_movie.html", context)
