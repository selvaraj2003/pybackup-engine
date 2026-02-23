import json
import datetime
from pathlib import Path
from typing import List, Dict, Any

from pybackup.utils.logger import setup_logging
from pybackup.utils.exceptions import ManifestError


class BackupManifest:
    """
    Backup Manifest Engine

    Creates and manages manifest files that describe:
    - backup metadata
    - files produced
    - checksums
    - engine details
    """

    def __init__(self, output_dir: str, format: str = "json"):
        self.output_dir = Path(output_dir)
        self.format = format.lower()
        self.logger = setup_logging("backup-manifest")

        if self.format not in ("json",):
            raise ManifestError(f"Unsupported manifest format: {self.format}")

        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create(
        self,
        engine: str,
        job_name: str,
        files: List[Dict[str, Any]],
        extra: Dict[str, Any] | None = None,
    ) -> Path:
        """
        Create a backup manifest file.

        :param engine: Backup engine name (files, mongo, postgres, etc.)
        :param job_name: Job identifier from YAML
        :param files: List of backed-up files with metadata
        :param extra: Optional engine-specific metadata
        :return: Path to manifest file
        """
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"

        manifest = {
            "version": 1,
            "engine": engine,
            "job": job_name,
            "created_at": timestamp,
            "files": files,
            "extra": extra or {},
        }

        manifest_path = self._manifest_path(engine, job_name)

        try:
            with manifest_path.open("w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            self.logger.info(f"Manifest created → {manifest_path}")
            return manifest_path

        except OSError as exc:
            raise ManifestError(
                "Failed to write manifest file",
                details=str(exc),
            )

    def load(self, manifest_path: str | Path) -> Dict[str, Any]:
        """
        Load an existing manifest file.

        :param manifest_path: Path to manifest
        :return: Manifest dictionary
        """
        path = Path(manifest_path)

        if not path.exists():
            raise ManifestError(f"Manifest not found: {path}")

        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise ManifestError(
                "Failed to read manifest file",
                details=str(exc),
            )

    def _manifest_path(self, engine: str, job_name: str) -> Path:
        """
        Generate manifest filename.
        """
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{engine}_{job_name}_{timestamp}.manifest.json"
        return self.output_dir / filename