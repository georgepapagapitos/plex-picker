# plexpicker/settings/test.py

from .base import *

DEBUG = False

# Use a faster test runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# Use in-memory database for testing
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

# Disable password hashing to speed up tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
