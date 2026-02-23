"""
File and configuration backup engine.

Responsibilities:
- Backup directories and files
- Support exclude patterns
- Optional compression
"""

import shutil
import fnmatch
import logging
from pathlib import Path

from pybackup.engine.base import BaseBackupEngine
from pybackup.utils.exceptions import BackupError

logger = logging.getLogger(__name__)


class FilesBackupEngine(BaseBackupEngine):
    """
    Backup engine for filesystem paths (configs, app data, etc.)
    """

    def run(self) -> None:
        """
        Execute file backup job.
        """
        source = self.config.get("source")
        if not source:
            raise BackupError("Missing required 'source' path")

        source_path = Path(source)
        if not source_path.exists():
            raise BackupError(f"Source path does not exist: {source_path}")

        exclude_patterns = self.config.get("exclude", [])
        compress = self.global_config.get("compress", False)

        output_dir = self.get_job_output_dir()
        self.ensure_dir(output_dir)

        logger.info(
            "[%s] Backing up files from %s → %s",
            self.name,
            source_path,
            output_dir,
        )

        try:
            if compress:
                self._backup_compressed(source_path, output_dir, exclude_patterns)
            else:
                self._backup_copy(source_path, output_dir, exclude_patterns)
        except Exception as exc:
            raise BackupError(f"File backup failed: {exc}") from exc

    # -------------------------
    # Internal helpers
    # -------------------------

    def _backup_copy(
        self,
        source: Path,
        destination: Path,
        exclude_patterns: list[str],
    ) -> None:
        """
        Copy files recursively with exclusions.
        """
        for item in source.rglob("*"):
            relative_path = item.relative_to(source)

            if self._is_excluded(relative_path, exclude_patterns):
                logger.debug("[%s] Excluded %s", self.name, relative_path)
                continue

            target = destination / relative_path

            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)

    def _backup_compressed(
        self,
        source: Path,
        destination: Path,
        exclude_patterns: list[str],
    ) -> None:
        """
        Create compressed tar.gz archive.
        """
        archive_path = destination.with_suffix(".tar.gz")

        logger.info("[%s] Creating archive %s", self.name, archive_path)

        def _exclude_filter(tarinfo):
            rel = Path(tarinfo.name)
            if self._is_excluded(rel, exclude_patterns):
                return None
            return tarinfo

        shutil.make_archive(
            base_name=str(destination),
            format="gztar",
            root_dir=source,
            filter=_exclude_filter,
        )

    def _is_excluded(self, path: Path, patterns: list[str]) -> bool:
        """
        Check if path matches exclude patterns.
        """
        for pattern in patterns:
            if fnmatch.fnmatch(path.name, pattern):
                return True
        return False