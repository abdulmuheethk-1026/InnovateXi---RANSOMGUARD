"""
RANSOMGUARD – Logging Module
Structured logging to file + console with severity levels.
"""

import os
import logging
import json
from datetime import datetime
from config import LOG_DIR


def _ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)


def get_logger(name: str = "RansomGuard") -> logging.Logger:
    _ensure_log_dir()
    log_file = os.path.join(LOG_DIR, f"ransomguard_{datetime.now().strftime('%Y%m%d')}.log")

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # already initialised

    logger.setLevel(logging.DEBUG)

    # File handler – full detail
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    # Console handler – warnings and above
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger


class EventLogger:
    """
    Writes structured JSON event records for forensic analysis.
    Each record: timestamp, file, operation, risk_score, action.
    """

    def __init__(self):
        _ensure_log_dir()
        self.path = os.path.join(LOG_DIR, f"events_{datetime.now().strftime('%Y%m%d')}.jsonl")
        self.logger = get_logger("EventLogger")

    def log(
        self,
        file_path: str,
        operation: str,
        risk_score: float,
        trigger: str,
        action: str,
        process_name: str = "unknown",
        pid: int = 0,
    ):
        record = {
            "timestamp":    datetime.now().isoformat(),
            "file":         file_path,
            "operation":    operation,
            "process":      process_name,
            "pid":          pid,
            "risk_score":   round(risk_score, 2),
            "trigger":      trigger,
            "action":       action,
        }
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        level = logging.WARNING if risk_score >= 40 else logging.INFO
        self.logger.log(level, f"[{operation}] {file_path} | score={risk_score:.0f} | {trigger} → {action}")
