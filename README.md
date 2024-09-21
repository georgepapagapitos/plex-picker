# Plex Picker

```
# create virtual environment

python -m venv venv
```

```
# activate venv

source venv/bin/activate
```

```
# install requirements

pip install -r requirements.txt
```

```
# run migrate, this creates local db.sqlite3

python manage.py migrate
```

```
# create .env and add secrets

cp .example.env .env
```

```
# run sync_movies command to populate db from "Movies" library

python manage.py sync_movies
```
- python manage.py runserver