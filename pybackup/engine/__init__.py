"""
Backup engine package for pybackup.

Contains class-based implementations for:
- File backups
- Database backups
- Verification & manifest handling
"""

from .base import BaseBackupEngine

__all__ = ["BaseBackupEngine"]