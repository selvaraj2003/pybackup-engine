"""
Abstract base class for all pybackup engines.

Defines:
- Common lifecycle (prepare → run → finalize)
- Logging
- Error handling
- Retention hooks
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
import logging

from pybackup.utils.exceptions import BackupError

logger = logging.getLogger(__name__)


class BaseBackupEngine(ABC):
    """
    Base class for all backup engines.

    Concrete engines MUST implement:
    - run()
    """

    def __init__(self, name: str, config: dict, global_config: dict):
        """
        :param name: Logical job/engine name
        :param config: Engine-specific config section
        :param global_config: Global config section
        """
        self.name = name
        self.config = config
        self.global_config = global_config

        self.backup_root = Path(global_config.get("backup_root", "/backups"))
        self.timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        logger.debug(
            "Initialized %s engine name=%s backup_root=%s",
            self.__class__.__name__,
            self.name,
            self.backup_root,
        )

    # -------------------------
    # Public API
    # -------------------------

    def execute(self) -> None:
        """
        Execute the backup lifecycle with safety guarantees.
        """
        logger.info("[%s] Backup started", self.name)

        try:
            self.prepare()
            self.run()
            self.finalize()
            logger.info("[%s] Backup finished successfully", self.name)

        except BackupError:
            # Known, expected backup failure
            logger.error("[%s] Backup failed", self.name)
            raise

        except Exception as exc:
            # Unexpected crash
            logger.exception("[%s] Backup crashed", self.name)
            raise BackupError(str(exc)) from exc

    # -------------------------
    # Lifecycle hooks
    # -------------------------

    def prepare(self) -> None:
        """
        Optional pre-backup hook.
        """
        pass

    @abstractmethod
    def run(self) -> None:
        """
        Perform the actual backup.

        MUST be implemented by concrete engines.
        """
        raise NotImplementedError

    def finalize(self) -> None:
        """
        Optional post-backup hook.
        """
        pass

    # -------------------------
    # Helper utilities
    # -------------------------

    def ensure_dir(self, path: Path) -> None:
        """
        Ensure a directory exists.
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise BackupError(f"Unable to create directory {path}: {exc}") from exc

    def get_job_output_dir(self) -> Path:
        """
        Return the output directory for this job.
        """
        output = self.config.get("output")
        if not output:
            raise BackupError("Missing required 'output' path in job config")

        return Path(output) / self.name / self.timestamp