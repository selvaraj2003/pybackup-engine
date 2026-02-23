#!/usr/bin/env python3
"""
PyBackup CLI
============

Production-ready CLI entry point for PyBackup.
"""

import sys
import logging
from pathlib import Path

import click

from pybackup.config.loader import load_config
from pybackup.utils.exceptions import PyBackupError
from pybackup.utils.logger import setup_logging

from pybackup.engine.files import FilesBackupEngine
from pybackup.engine.mongo import MongoBackupEngine
from pybackup.engine.postgres import PostgresBackupEngine
from pybackup.engine.mysql import MySQLBackupEngine
from pybackup.engine.mssql import MSSQLBackupEngine
from pybackup.engine.verify import BackupVerifier


# ============================================================
# MAIN CLI GROUP
# ============================================================
@click.group()
@click.version_option("0.1.0", prog_name="PyBackup")
def main():
    """
    PyBackup – Production-ready backup CLI tool
    """
    pass


# ============================================================
# RUN BACKUPS
# ============================================================
@main.command()
@click.option(
    "--config",
    "-c",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to pybackup YAML configuration file",
)
def run(config: Path):
    """
    Run backup jobs defined in configuration
    """
    try:
        cfg = load_config(str(config))

        # Setup logging FIRST
        setup_logging(cfg["global"].get("log_level", "INFO"))
        logger = logging.getLogger("pybackup")

        logger.info("Starting PyBackup")
        logger.info("Using config: %s", config)

        if cfg.get("files", {}).get("enabled"):
            FilesBackupEngine(cfg["files"], logger).run()

        if cfg.get("mongodb", {}).get("enabled"):
            MongoBackupEngine(cfg["mongodb"], logger).run()

        if cfg.get("postgresql", {}).get("enabled"):
            PostgresBackupEngine(cfg["postgresql"], logger).run()

        if cfg.get("mysql", {}).get("enabled"):
            MySQLBackupEngine(cfg["mysql"], logger).run()

        if cfg.get("mssql", {}).get("enabled"):
            MSSQLBackupEngine(cfg["mssql"], logger).run()

        logger.info("All backup jobs completed successfully")

    except PyBackupError as exc:
        click.secho(f"Backup failed: {exc}", fg="red")
        sys.exit(1)

    except Exception as exc:
        click.secho(f"Unexpected error: {exc}", fg="red")
        sys.exit(2)


# ============================================================
# VERIFY BACKUPS
# ============================================================
@main.command()
@click.option(
    "--config",
    "-c",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to pybackup YAML configuration file",
)
def verify(config: Path):
    """
    Verify backup integrity
    """
    try:
        cfg = load_config(str(config))
        setup_logging(cfg["global"].get("log_level", "INFO"))
        logger = logging.getLogger("pybackup")

        BackupVerifier(cfg, logger).run()
        logger.info("Backup verification completed successfully")

    except PyBackupError as exc:
        click.secho(f"Verification failed: {exc}", fg="red")
        sys.exit(1)


# ============================================================
# CONFIG CHECK
# ============================================================
@main.command(name="config-check")
@click.option(
    "--config",
    "-c",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to pybackup YAML configuration file",
)
def config_check(config: Path):
    """
    Validate pybackup configuration
    """
    try:
        load_config(str(config))
        click.secho("Configuration is valid ✔", fg="green")

    except Exception as exc:
        click.secho(f"Invalid configuration: {exc}", fg="red")
        sys.exit(1)


# ============================================================
# ENTRY POINT
# ============================================================
if __name__ == "__main__":
    main()