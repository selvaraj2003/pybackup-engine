import os
import yaml
from pathlib import Path

from pybackup.utils.exceptions import ConfigError


def _expand_env_vars(value):
    """
    Recursively expand environment variables like ${VAR} in config values.
    """
    if isinstance(value, dict):
        return {k: _expand_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand_env_vars(v) for v in value]
    if isinstance(value, str):
        return os.path.expandvars(value)
    return value


def load_config(config_path: str) -> dict:
    """
    Load and validate pybackup YAML configuration.

    :param config_path: Path to pybackup.yaml
    :return: Parsed configuration dictionary
    :raises ConfigError: If config is invalid or unreadable
    """
    path = Path(config_path)

    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")

    if not path.is_file():
        raise ConfigError(f"Config path is not a file: {path}")

    try:
        with path.open("r") as f:
            config = yaml.safe_load(f) or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"Invalid YAML syntax: {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Unable to read config file: {exc}") from exc

    # Expand environment variables
    config = _expand_env_vars(config)

    # Basic validation
    _validate_config(config)

    return config


def _validate_config(config: dict) -> None:
    """
    Minimal required config validation.
    """
    if "version" not in config:
        raise ConfigError("Missing required field: version")

    if "global" not in config:
        raise ConfigError("Missing required section: global")

    global_cfg = config.get("global", {})

    if "backup_root" not in global_cfg:
        raise ConfigError("global.backup_root is required")

    if "retention_days" in global_cfg:
        if not isinstance(global_cfg["retention_days"], int):
            raise ConfigError("global.retention_days must be an integer")

    # Optional engine validation (only if enabled)
    for engine in ("files", "mongodb", "postgresql", "mysql", "mssql", "systemd_files"):
        engine_cfg = config.get(engine)
        if engine_cfg and engine_cfg.get("enabled"):
            if "jobs" in engine_cfg and not isinstance(engine_cfg["jobs"], list):
                raise ConfigError(f"{engine}.jobs must be a list")
