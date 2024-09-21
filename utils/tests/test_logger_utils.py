import logging
import unittest
from io import StringIO

from utils.logger_utils import ColoredFormatter, LogColors, setup_logging


class BaseLoggingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.logger = logging.getLogger("test")
        cls.logger.setLevel(logging.DEBUG)
        cls.formatter = ColoredFormatter("%(levelname)s - %(message)s")

    def setUp(self):
        self.stream = StringIO()
        self.handler = logging.StreamHandler(self.stream)
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)

    def tearDown(self):
        self.logger.removeHandler(self.handler)
        self.stream.close()


class TestColoredFormatter(BaseLoggingTest):
    def test_debug_color(self):
        self.logger.debug("Debug message")
        self.assertIn(
            f"{LogColors.OKBLUE}Debug message{LogColors.ENDC}", self.stream.getvalue()
        )

    def test_info_color(self):
        self.logger.info("Info message")
        self.assertIn(
            f"{LogColors.OKGREEN}Info message{LogColors.ENDC}", self.stream.getvalue()
        )

    def test_warning_color(self):
        self.logger.warning("Warning message")
        self.assertIn(
            f"{LogColors.WARNING}Warning message{LogColors.ENDC}",
            self.stream.getvalue(),
        )

    def test_error_color(self):
        self.logger.error("Error message")
        self.assertIn(
            f"{LogColors.FAIL}Error message{LogColors.ENDC}", self.stream.getvalue()
        )


class TestSetupLogging(unittest.TestCase):
    def test_setup_logging(self):
        logger = setup_logging("test_logger")
        self.assertEqual(logger.name, "test_logger")
        self.assertEqual(logger.level, logging.DEBUG)
        self.assertEqual(len(logger.handlers), 1)
        self.assertIsInstance(logger.handlers[0], logging.StreamHandler)
        self.assertIsInstance(logger.handlers[0].formatter, ColoredFormatter)

    def test_setup_logging_custom_level(self):
        logger = setup_logging("test_logger", level=logging.ERROR)
        self.assertEqual(logger.level, logging.ERROR)
