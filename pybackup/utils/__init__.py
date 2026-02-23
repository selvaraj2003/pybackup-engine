"""
Utility helpers shared across pybackup.

This package contains reusable, framework-independent utilities such as:
- custom exceptions
- logging helpers
- time/date helpers
- checksum utilities (future)
"""

from .exceptions import (
    PyBackupError,
    ConfigError,
    BackupError,
    EngineError,
)

__all__ = [
    "PyBackupError",
    "ConfigError",
    "BackupError",
    "EngineError",
]
