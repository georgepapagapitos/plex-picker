# plexpicker/settings/development.py

import os

from .base import *

DEBUG = True

ALLOWED_HOSTS = ["*"]

INTERNAL_IPS = [
    "127.0.0.1",
]

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("DB_NAME", "default_db"),
        "USER": os.getenv("DB_USER", "default_user"),
        "PASSWORD": os.getenv("DB_PASSWORD", "default_password"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
    }
}
