import os
import subprocess
import datetime
from pathlib import Path

from pybackup.engine.base import BaseBackupEngine
from pybackup.utils.logger import setup_logging
from pybackup.utils.exceptions import BackupError


class MongoBackupEngine(BaseBackupEngine):
    """
    MongoDB Backup Engine using mongodump
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.logger = setup_logging("mongo-backup")

        mongo_cfg = config.get("mongo", {})
        self.host = mongo_cfg.get("host", "localhost")
        self.port = mongo_cfg.get("port", 27017)
        self.username = mongo_cfg.get("username")
        self.password = mongo_cfg.get("password")
        self.auth_db = mongo_cfg.get("auth_db", "admin")
        self.database = mongo_cfg.get("database")  # optional
        self.output_dir = mongo_cfg.get("output_dir", "/var/backups/mongo")

    def run(self):
        """
        Execute MongoDB backup
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Path(self.output_dir) / f"mongo_backup_{timestamp}"
        backup_path.mkdir(parents=True, exist_ok=True)

        command = [
            "mongodump",
            "--host", self.host,
            "--port", str(self.port),
            "--out", str(backup_path)
        ]

        if self.username and self.password:
            command.extend([
                "--username", self.username,
                "--password", self.password,
                "--authenticationDatabase", self.auth_db
            ])

        if self.database:
            command.extend(["--db", self.database])

        self.logger.info(f"Starting MongoDB backup → {backup_path}")

        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )

            self.logger.info("MongoDB backup completed successfully")
            self.logger.debug(result.stdout)

        except subprocess.CalledProcessError as exc:
            self.logger.error(exc.stderr)
            raise BackupError(
                "MongoDB backup failed",
                details=exc.stderr
            )