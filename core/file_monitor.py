"""
RANSOMGUARD – File System Monitor
Event-driven watcher using watchdog. No content scanning.
Emits structured FileEvent objects to the Behavior Analyzer.
"""

import os
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, List

try:
    from watchdog.observers import Observer
    from watchdog.events import (
        FileSystemEventHandler,
        FileMovedEvent,
        FileModifiedEvent,
        FileCreatedEvent,
        FileDeletedEvent,
    )
except ImportError:
    raise SystemExit("watchdog not installed. Run: pip install watchdog")

from config import WATCH_PATHS, SUSPICIOUS_PREFIXES, SUSPICIOUS_EXTENSIONS
from rg_logger import get_logger

logger = get_logger("FileMonitor")


@dataclass
class FileEvent:
    timestamp:      datetime
    event_type:     str          # rename | modify | create | delete | access
    src_path:       str
    dest_path:      str  = ""
    suspicious:     bool = False
    suspicious_why: str  = ""


def _check_suspicious(path: str, dest: str = "") -> tuple[bool, str]:
    """Quick metadata check for ransomware indicators."""
    reasons = []
    name = os.path.basename(dest or path).lower()
    ext  = os.path.splitext(name)[1]

    if any(name.startswith(p) for p in SUSPICIOUS_PREFIXES):
        reasons.append(f"suspicious prefix in '{name}'")
    if ext in SUSPICIOUS_EXTENSIONS:
        reasons.append(f"suspicious extension '{ext}'")

    return (bool(reasons), "; ".join(reasons))


class _RGEventHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[FileEvent], None]):
        super().__init__()
        self._cb = callback

    def _emit(self, raw_event, etype: str, dest: str = ""):
        susp, why = _check_suspicious(raw_event.src_path, dest)
        ev = FileEvent(
            timestamp=datetime.now(),
            event_type=etype,
            src_path=raw_event.src_path,
            dest_path=dest,
            suspicious=susp,
            suspicious_why=why,
        )
        self._cb(ev)

    def on_moved(self, event):
        if not event.is_directory:
            self._emit(event, "rename", event.dest_path)

    def on_modified(self, event):
        if not event.is_directory:
            self._emit(event, "modify")

    def on_created(self, event):
        if not event.is_directory:
            self._emit(event, "create")

    def on_deleted(self, event):
        if not event.is_directory:
            self._emit(event, "delete")


class FileMonitor:
    """
    Starts watchdog observers on all configured WATCH_PATHS.
    Calls `on_event(FileEvent)` for every file system change.
    """

    def __init__(self, on_event: Callable[[FileEvent], None]):
        self._on_event  = on_event
        self._observers: List[Observer] = []
        self._lock      = threading.Lock()
        self._running   = False

    def start(self):
        handler = _RGEventHandler(self._on_event)
        with self._lock:
            for path in WATCH_PATHS:
                if not os.path.exists(path):
                    logger.warning(f"Watch path does not exist, skipping: {path}")
                    continue
                obs = Observer()
                obs.schedule(handler, path, recursive=True)
                obs.start()
                self._observers.append(obs)
                logger.info(f"Watching: {path}")
            self._running = True
        logger.info(f"FileMonitor active — {len(self._observers)} path(s) monitored")

    def stop(self):
        with self._lock:
            for obs in self._observers:
                obs.stop()
                obs.join()
            self._observers.clear()
            self._running = False
        logger.info("FileMonitor stopped")

    @property
    def running(self):
        return self._running
