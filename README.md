# Plex Picker

- python -m venv venv

- source venv/bin/activate

- pip install -r requirements.txt

- python manage.py migrate

- cp .example.env .env

- python manage.py sync_movies

- python manage.py runserver