"""
Custom exception hierarchy for pybackup.

All pybackup-specific errors inherit from PyBackupError.
This allows clean exception handling and consistent CLI output.
"""


class PyBackupError(Exception):
    """
    Base exception for all pybackup errors.

    Catch this if you want to handle *any* pybackup-related failure
    in one place (CLI, cron, systemd).
    """
    pass


class ConfigError(PyBackupError):
    """
    Raised when configuration is invalid or cannot be loaded.

    Examples:
    - YAML syntax errors
    - Missing required fields
    - Invalid values (wrong types, unsupported options)
    """
    pass


class EngineError(PyBackupError):
    """
    Raised by backup engines when a backup operation fails.

    Examples:
    - Database dump command fails
    - Source directory does not exist
    - Permission denied
    """
    pass


class BackupError(PyBackupError):
    """
    Raised when a backup run fails at a higher level.

    Examples:
    - One or more backup jobs fail
    - Partial backup completion
    - Verification failure
    """
    pass


class SecurityError(PyBackupError):
    """
    Raised when a security-related issue occurs.

    Examples:
    - Missing required environment variables (passwords)
    - Invalid credentials
    - Unsafe permissions detected
    """
    pass


class ManifestError(PyBackupError):
    """
    Raised when backup manifest creation or parsing fails.

    Examples:
    - Unable to write manifest file
    - Invalid manifest format
    - Checksum mismatch in manifest
    """
    pass


class VerificationError(PyBackupError):
    """
    Raised when backup verification fails.

    Examples:
    - Checksum mismatch
    - Missing backup files
    - Corrupted archive
    - Incomplete backup detected
    """
    pass