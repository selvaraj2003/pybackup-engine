"""
Security helpers for pybackup.

Responsibilities:
- Secure password retrieval
- Environment variable expansion
- Prevent secrets from being logged or stored
"""

import os
from typing import Optional

from pybackup.utils.exceptions import SecurityError


def get_secret(
    value: Optional[str],
    *,
    required: bool = False,
    name: str = "SECRET",
) -> Optional[str]:
    """
    Resolve secrets securely.

    Supports:
    - Plain values
    - Environment variable names
    - ${ENV_VAR} expansion

    Examples:
    - "mypassword"
    - "MYSQL_PASSWORD"
    - "${MYSQL_PASSWORD}"

    :param value: Raw config value
    :param required: Whether secret is mandatory
    :param name: Logical secret name (for errors)
    :return: Resolved secret or None
    """

    if not value:
        if required:
            raise SecurityError(f"{name} is required but not provided")
        return None

    # Expand ${VAR} syntax
    resolved = os.path.expandvars(value)

    # If still looks like an env var name, resolve it
    if resolved == value and value.isupper():
        resolved = os.environ.get(value)

    if not resolved:
        if required:
            raise SecurityError(
                f"{name} could not be resolved from environment"
            )
        return None

    return resolved


def mask_secret(secret: Optional[str], show_last: int = 2) -> str:
    """
    Mask secrets for logging.

    Example:
    password123 → ********23

    :param secret: Secret value
    :param show_last: Visible characters at end
    """

    if not secret:
        return "******"

    if len(secret) <= show_last:
        return "*" * len(secret)

    return "*" * (len(secret) - show_last) + secret[-show_last:]
