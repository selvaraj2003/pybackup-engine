"""
Central logging configuration for pybackup.

Features:
- Console + optional file logging
- Consistent format
- Log level from config
- Safe for CLI, cron, systemd
"""

import logging
import sys
from pathlib import Path
from pybackup.constants import LOG_FORMAT


def setup_logging(
    log_level: str = "INFO",
    log_file: str | None = None,
) -> None:
    """
    Configure global logging for pybackup.

    This configures the ROOT logger.
    Individual modules should use logging.getLogger(__name__).

    :param log_level: INFO, DEBUG, WARNING, ERROR
    :param log_file: Optional log file path
    """

    level = logging.getLevelName(log_level.upper())
    if not isinstance(level, int):
        level = logging.INFO

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Prevent duplicate logs (important for tests & re-runs)
    if root_logger.handlers:
        root_logger.handlers.clear()

    formatter = logging.Formatter(LOG_FORMAT)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Optional file handler
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)