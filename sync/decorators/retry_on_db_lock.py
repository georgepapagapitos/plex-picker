# sync/decorators/retry_on_db_lock.py

import random
import time
from functools import wraps

from django.db import OperationalError

from utils.logger_utils import setup_logging

logger = setup_logging(__name__)


def retry_on_db_lock(max_attempts=5, delay=0.1):
    """
    Decorator to retry a function if a database lock is encountered.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except OperationalError as e:
                    if "database is locked" in str(e) and attempt < max_attempts - 1:
                        sleep_time = delay * (2**attempt) + random.uniform(0, 0.1)
                        logger.warning(
                            f"Database locked. Retrying in {sleep_time:.2f} seconds..."
                        )
                        time.sleep(sleep_time)
                    else:
                        raise

        return wrapper

    return decorator
