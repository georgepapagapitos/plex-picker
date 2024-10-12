# sync/helpers/movie_links.py

import requests
from django.conf import settings


def get_tmdb_id_from_movie(movie):
    return movie.tmdb_id


def fetch_movie_links_from_tmdb_id(tmdb_id):
    if not tmdb_id:
        return None, None, None

    tmdb_url = f"https://www.themoviedb.org/movie/{tmdb_id}"
    trakt_api_url = f"https://api.trakt.tv/search/tmdb/{tmdb_id}?type=movie"

    try:
        headers = {
            "Content-Type": "application/json",
            "trakt-api-version": "2",
            "trakt-api-key": settings.TRAKT_CLIENT_ID,
        }
        response = requests.get(trakt_api_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            if data:
                trakt_id = data[0]["movie"]["ids"]["slug"]
                imdb_id = data[0]["movie"]["ids"].get("imdb")
                trakt_url = f"https://trakt.tv/movies/{trakt_id}"
                imdb_url = f"https://www.imdb.com/title/{imdb_id}" if imdb_id else None
                return tmdb_url, trakt_url, imdb_url
    except requests.RequestException as e:
        print(f"Error fetching Trakt data: {e}")

    return tmdb_url, None, None


def fetch_movie_links(movie):
    tmdb_id = get_tmdb_id_from_movie(movie)
    return fetch_movie_links_from_tmdb_id(tmdb_id)
