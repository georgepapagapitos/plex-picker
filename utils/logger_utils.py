# utils/logger_utils.py

import logging


class LogColors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class ColoredFormatter(logging.Formatter):
    def format(self, record):
        if record.levelname == "DEBUG":
            record.msg = f"{LogColors.OKBLUE}{record.msg}{LogColors.ENDC}"
        elif record.levelname == "INFO":
            record.msg = f"{LogColors.OKGREEN}{record.msg}{LogColors.ENDC}"
        elif record.levelname == "WARNING":
            record.msg = f"{LogColors.WARNING}{record.msg}{LogColors.ENDC}"
        elif record.levelname == "ERROR":
            record.msg = f"{LogColors.FAIL}{record.msg}{LogColors.ENDC}"
        return super().format(record)


def setup_logging(name: str, level=logging.DEBUG):
    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    formatter = ColoredFormatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)
    return logger
