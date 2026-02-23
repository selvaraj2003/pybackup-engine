import hashlib
from pathlib import Path

from pybackup.utils.logger import setup_logging
from pybackup.utils.exceptions import VerificationError


class BackupVerifier:
    """
    Backup verification engine.
    Performs checksum verification to ensure backup integrity.
    """

    def __init__(self, algorithm: str = "sha256", chunk_size: int = 8192):
        self.algorithm = algorithm
        self.chunk_size = chunk_size
        self.logger = setup_logging("backup-verify")

    def verify_file(self, file_path: str, expected_checksum: str) -> bool:
        """
        Verify a file against an expected checksum.

        :param file_path: Path to backup file
        :param expected_checksum: Expected hash value
        :return: True if valid
        """
        path = Path(file_path)

        if not path.exists():
            raise VerificationError(f"Backup file not found: {path}")

        self.logger.info(f"Verifying backup checksum → {path}")

        actual_checksum = self._calculate_checksum(path)

        if actual_checksum != expected_checksum:
            self.logger.error("Checksum mismatch detected")
            raise VerificationError(
                "Backup verification failed",
                details={
                    "expected": expected_checksum,
                    "actual": actual_checksum,
                },
            )

        self.logger.info("Backup verification successful")
        return True

    def generate_checksum(self, file_path: str) -> str:
        """
        Generate checksum for a backup file.

        :param file_path: Path to backup file
        :return: checksum string
        """
        path = Path(file_path)

        if not path.exists():
            raise VerificationError(f"File not found: {path}")

        checksum = self._calculate_checksum(path)
        self.logger.debug(f"Generated checksum for {path}: {checksum}")
        return checksum

    def _calculate_checksum(self, path: Path) -> str:
        """
        Calculate checksum using streaming read (safe for large files).
        """
        try:
            hasher = hashlib.new(self.algorithm)

            with path.open("rb") as f:
                while chunk := f.read(self.chunk_size):
                    hasher.update(chunk)

            return hasher.hexdigest()

        except Exception as exc:
            raise VerificationError(
                "Checksum calculation failed",
                details=str(exc),
            )