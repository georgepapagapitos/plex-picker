import logging
import sys
from typing import Optional


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
    COLORS = {
        "DEBUG": LogColors.OKBLUE,
        "INFO": LogColors.OKGREEN,
        "WARNING": LogColors.WARNING,
        "ERROR": LogColors.FAIL,
        "CRITICAL": LogColors.FAIL + LogColors.BOLD,
    }

    def format(self, record):
        level_color = self.COLORS.get(record.levelname, "")
        record.msg = f"{level_color}{record.msg}{LogColors.ENDC}"
        return super().format(record)


def setup_logging(
    name: str,
    level: int = logging.DEBUG,
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    use_color: bool = True,
    log_file: Optional[str] = None,
) -> logging.Logger:
    """
    Set up a logger with customizable options.

    Args:
    name (str): The name of the logger.
    level (int): The logging level (default: logging.DEBUG).
    format_string (str): The format string for log messages.
    use_color (bool): Whether to use colored output (default: True).
    log_file (Optional[str]): Path to a log file, if file logging is desired.

    Returns:
    logging.Logger: A configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove any existing handlers to avoid duplicate logging
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if use_color:
        formatter = ColoredFormatter(format_string)
    else:
        formatter = logging.Formatter(format_string)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Create file handler if log_file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(format_string))
        logger.addHandler(file_handler)

    return logger


# Usage example:
# logger = setup_logging("my_app", level=logging.INFO, log_file="app.log")
# logger.info("This is an info message")
# logger.warning("This is a warning message")
