"""
RANSOMGUARD – Backup Manager
Creates timestamped, permission-restricted backup snapshots.

On Windows the backup folder is:
  • Hidden via FILE_ATTRIBUTE_HIDDEN
  • Write-protected via icacls (denies Delete to standard users)
  • r"Timestamped subfolders: C:\RansomGuard_Backup\2024-01-15_14-30-22\\"
"""

import os
import shutil
import subprocess
import threading
from datetime import datetime
from typing import List

from config import BACKUP_ROOT, WATCH_PATHS, BACKUP_MAX_SIZE_MB
from rg_logger import get_logger

logger = get_logger("BackupManager")

_backup_lock = threading.Lock()


def _make_hidden_restricted(path: str):
    """Attempt to hide and restrict the backup directory (Windows)."""
    try:
        # Hide the folder
        subprocess.run(
            ["attrib", "+H", "+S", path],
            check=False, capture_output=True,
        )
        # Deny Delete permission to everyone except SYSTEM / Administrators
        subprocess.run(
            ["icacls", path, "/deny", "Everyone:(D,DC)", "/T"],
            check=False, capture_output=True,
        )
        logger.info(f"Backup folder secured: {path}")
    except Exception as e:
        logger.warning(f"Could not apply folder restrictions (non-Windows?): {e}")


def _folder_size_mb(path: str) -> float:
    total = 0
    for dirpath, _, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(dirpath, f))
            except OSError:
                pass
    return total / (1024 * 1024)


def create_snapshot(watch_paths: List[str] = None) -> str:
    """
    Copy files from WATCH_PATHS into a new timestamped backup folder.
    Returns the path of the created snapshot, or "" on failure.
    """
    with _backup_lock:
        try:
            paths = watch_paths or WATCH_PATHS
            ts    = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            dest  = os.path.join(BACKUP_ROOT, ts)

            os.makedirs(dest, exist_ok=True)
            _make_hidden_restricted(BACKUP_ROOT)

            copied = 0
            skipped = 0

            for src_root in paths:
                if not os.path.exists(src_root):
                    continue

                # Mirror directory structure
                for dirpath, dirs, files in os.walk(src_root):
                    # Skip our own backup directory to prevent recursion
                    if BACKUP_ROOT.lower() in dirpath.lower():
                        continue

                    rel = os.path.relpath(dirpath, os.path.dirname(src_root))
                    target_dir = os.path.join(dest, rel)
                    os.makedirs(target_dir, exist_ok=True)

                    for fname in files:
                        src_file = os.path.join(dirpath, fname)
                        dst_file = os.path.join(target_dir, fname)

                        # Size guard
                        if _folder_size_mb(dest) > BACKUP_MAX_SIZE_MB:
                            logger.warning("Backup size limit reached — partial snapshot saved.")
                            skipped += 1
                            continue

                        try:
                            shutil.copy2(src_file, dst_file)
                            copied += 1
                        except (PermissionError, OSError) as e:
                            logger.debug(f"Skipped {src_file}: {e}")
                            skipped += 1

            logger.info(
                f"Snapshot created: {dest} | "
                f"files copied={copied} skipped={skipped} | "
                f"size={_folder_size_mb(dest):.1f} MB"
            )
            return dest

        except Exception as e:
            logger.error(f"Backup failed: {e}")
            return ""


def list_snapshots() -> List[str]:
    """Return list of existing snapshot folder paths."""
    if not os.path.exists(BACKUP_ROOT):
        return []
    return sorted(
        [os.path.join(BACKUP_ROOT, d) for d in os.listdir(BACKUP_ROOT)
         if os.path.isdir(os.path.join(BACKUP_ROOT, d))],
        reverse=True,
    )
