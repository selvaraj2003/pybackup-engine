import subprocess
import datetime
from pathlib import Path

from pybackup.engine.base import BaseBackupEngine
from pybackup.utils.logger import setup_logging
from pybackup.utils.exceptions import BackupError


class MySQLBackupEngine(BaseBackupEngine):
    """
    MySQL Backup Engine
    Uses native mysqldump utility
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.logger = setup_logging("mysql-backup")

        mysql_cfg = config.get("mysql", {})

        self.host = mysql_cfg.get("host", "localhost")
        self.port = mysql_cfg.get("port", 3306)
        self.database = mysql_cfg.get("database")
        self.username = mysql_cfg.get("username")
        self.password = mysql_cfg.get("password")
        self.output_dir = mysql_cfg.get("output", "/var/backups/mysql")
        self.single_transaction = mysql_cfg.get("single_transaction", True)
        self.compress = mysql_cfg.get("compress", True)

        if not self.database:
            raise BackupError("MySQL database name is required")

        if not self.username:
            raise BackupError("MySQL username is required")

    def run(self):
        """
        Execute MySQL database backup
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(self.output_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{self.database}_{timestamp}.sql"
        backup_file = backup_dir / filename

        dump_cmd = [
            "mysqldump",
            "-h", self.host,
            "-P", str(self.port),
            "-u", self.username,
            self.database,
        ]

        if self.single_transaction:
            dump_cmd.append("--single-transaction")

        if self.password:
            dump_cmd.insert(3, f"-p{self.password}")

        self.logger.info(f"Starting MySQL backup → {backup_file}")

        try:
            with backup_file.open("w") as sql_file:
                result = subprocess.run(
                    dump_cmd,
                    stdout=sql_file,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=True,
                )

            if self.compress:
                self._compress_backup(backup_file)

            self.logger.info("MySQL backup completed successfully")

        except subprocess.CalledProcessError as exc:
            self.logger.error(exc.stderr)
            raise BackupError(
                "MySQL backup failed",
                details=exc.stderr,
            )

    def _compress_backup(self, file_path: Path):
        """
        Compress SQL dump using gzip
        """
        gzip_cmd = ["gzip", "-f", str(file_path)]

        self.logger.info(f"Compressing backup → {file_path}.gz")

        try:
            subprocess.run(
                gzip_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            raise BackupError(
                "MySQL backup compression failed",
                details=exc.stderr,
            )