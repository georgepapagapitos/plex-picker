# plexpicker/settings/test.py

from .base import *

DEBUG = False

# Use a faster test runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# Use in-memory database for testing
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Disable password hashing to speed up tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]
