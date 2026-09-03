"""Centralized logging configuration."""
import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logging once for the application."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(handler)
    root.setLevel(level)
