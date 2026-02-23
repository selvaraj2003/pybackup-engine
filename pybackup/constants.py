"""
Global constants for pybackup.

These values define defaults and limits used across the project.
"""

from pathlib import Path

# =========================
# APPLICATION METADATA
# =========================

APP_NAME = "pybackup"
DEFAULT_VERSION = "1.0.0"

# =========================
# DEFAULT PATHS
# =========================

DEFAULT_CONFIG_PATH = Path("/etc/pybackup/pybackup.yaml")
DEFAULT_ENV_FILE = Path("/etc/pybackup/pybackup.env")

DEFAULT_BACKUP_ROOT = Path("/backups")
DEFAULT_WORK_DIR = Path("/var/lib/pybackup")

DEFAULT_LOG_DIR = Path("/var/log/pybackup")
DEFAULT_LOG_FILE = DEFAULT_LOG_DIR / "pybackup.log"

# =========================
# BACKUP DEFAULTS
# =========================

DEFAULT_RETENTION_DAYS = 7
DEFAULT_COMPRESS = True
DEFAULT_VERIFY_CHECKSUM = True

# =========================
# DATABASE BACKUP DEFAULTS
# =========================

DEFAULT_MYSQL_PORT = 3306
DEFAULT_POSTGRES_PORT = 5432
DEFAULT_MONGODB_PORT = 27017
DEFAULT_MSSQL_PORT = 1433

# =========================
# FILE BACKUP DEFAULTS
# =========================

DEFAULT_EXCLUDES = [
    "*.log",
    "*.tmp",
    "*.cache",
]

# =========================
# LOGGING
# =========================

DEFAULT_LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"

# =========================
# EXIT CODES
# =========================

EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EXIT_CRASH = 2