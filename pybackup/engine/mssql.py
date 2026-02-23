import subprocess
import datetime
from pathlib import Path

from pybackup.engine.base import BaseBackupEngine
from pybackup.utils.logger import setup_logging
from pybackup.utils.exceptions import BackupError


class MSSQLBackupEngine(BaseBackupEngine):
    """
    Microsoft SQL Server Backup Engine
    Uses native BACKUP DATABASE command via sqlcmd
    """

    def __init__(self, config: dict):
        super().__init__(config)
        self.logger = setup_logging("mssql-backup")

        mssql_cfg = config.get("mssql", {})
        self.host = mssql_cfg.get("host", "localhost")
        self.port = mssql_cfg.get("port", 1433)
        self.username = mssql_cfg.get("username")
        self.password = mssql_cfg.get("password")
        self.database = mssql_cfg.get("database")
        self.output_dir = mssql_cfg.get("output_dir", "/var/backups/mssql")
        self.encrypt = mssql_cfg.get("encrypt", False)

        if not self.database:
            raise BackupError("MSSQL database name is required")

    def run(self):
        """
        Execute MSSQL database backup
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(self.output_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)

        backup_file = backup_dir / f"{self.database}_{timestamp}.bak"

        sql_query = (
            f"BACKUP DATABASE [{self.database}] "
            f"TO DISK = N'{backup_file}' "
            f"WITH INIT, COMPRESSION"
        )

        command = [
            "sqlcmd",
            "-S", f"{self.host},{self.port}",
            "-U", self.username,
            "-P", self.password,
            "-Q", sql_query,
        ]

        if self.encrypt:
            command.append("-C")

        self.logger.info(f"Starting MSSQL backup → {backup_file}")

        try:
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )

            self.logger.info("MSSQL backup completed successfully")
            self.logger.debug(result.stdout)

        except subprocess.CalledProcessError as exc:
            self.logger.error(exc.stderr)
            raise BackupError(
                "MSSQL backup failed",
                details=exc.stderr
            )