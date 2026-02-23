"""
Configuration package for pybackup.

Handles loading and validation of YAML configuration files.
"""

from .loader import load_config

__all__ = ["load_config"]
