import subprocess
import datetime
from pathlib import Path

from pybackup.engine.base import BaseBackupEngine
from pybackup.utils.logger import setup_logging
from pybackup.utils.exceptions import BackupError


class PostgresBackupEngine(BaseBackupEngine):
    """
    PostgreSQL Backup Engine
    Uses native pg_dump utility
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.logger = setup_logging("postgres-backup")

        pg_cfg = config.get("postgresql", {})

        self.host = pg_cfg.get("host", "localhost")
        self.port = pg_cfg.get("port", 5432)
        self.database = pg_cfg.get("database")
        self.username = pg_cfg.get("username")
        self.password = pg_cfg.get("password")   # ENV already expanded
        self.output_dir = pg_cfg.get("output", "/var/backups/postgres")
        self.format = pg_cfg.get("format", "custom")  # plain | custom | directory
        self.compress = pg_cfg.get("compress", True)

        if not self.database:
            raise BackupError("PostgreSQL database name is required")

        if not self.username:
            raise BackupError("PostgreSQL username is required")

    def run(self):
        """
        Execute PostgreSQL backup
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(self.output_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)

        ext = self._get_extension()
        backup_file = backup_dir / f"{self.database}_{timestamp}.{ext}"

        dump_cmd = [
            "pg_dump",
            "-h", self.host,
            "-p", str(self.port),
            "-U", self.username,
            "-d", self.database,
        ]

        # Backup format
        if self.format == "custom":
            dump_cmd.extend(["-F", "c"])
        elif self.format == "directory":
            dump_cmd.extend(["-F", "d"])
        else:
            dump_cmd.extend(["-F", "p"])

        self.logger.info(f"Starting PostgreSQL backup → {backup_file}")

        try:
            env = self._build_env()

            if self.format == "directory":
                subprocess.run(
                    dump_cmd + ["-f", str(backup_file)],
                    env=env,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True,
                )
            else:
                with backup_file.open("wb") as out:
                    subprocess.run(
                        dump_cmd,
                        env=env,
                        stdout=out,
                        stderr=subprocess.PIPE,
                        check=True,
                    )

            if self.compress and self.format == "plain":
                self._compress_backup(backup_file)

            self.logger.info("PostgreSQL backup completed successfully")

        except subprocess.CalledProcessError as exc:
            self.logger.error(exc.stderr)
            raise BackupError(
                "PostgreSQL backup failed",
                details=exc.stderr,
            )

    def _build_env(self):
        """
        Build environment variables securely
        """
        env = dict(**dict())
        if self.password:
            env["PGPASSWORD"] = self.password
        return env

    def _get_extension(self) -> str:
        """
        Decide backup file extension
        """
        if self.format == "custom":
            return "dump"
        if self.format == "directory":
            return "dir"
        return "sql"

    def _compress_backup(self, file_path: Path):
        """
        Compress SQL dump using gzip
        """
        self.logger.info(f"Compressing backup → {file_path}.gz")

        try:
            subprocess.run(
                ["gzip", "-f", str(file_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            raise BackupError(
                "PostgreSQL backup compression failed",
                details=exc.stderr,
            )