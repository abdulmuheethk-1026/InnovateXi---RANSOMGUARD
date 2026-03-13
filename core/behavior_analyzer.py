"""
RANSOMGUARD – Behavior Analysis Engine
Sliding time-window statistics + weighted AI risk scoring.

Architecture:
  FileEvent → BehaviorAnalyzer → BehaviorSnapshot (risk_score 0-100)

Risk score composition (configurable weights in config.py):
  rapid_rename      30 pts  – renames > threshold/min
  bulk_modification 25 pts  – modifications > threshold/min
  ext_change        20 pts  – extension changes detected
  suspicious_prefix 15 pts  – locked_/encrypted_ prefixes
  bulk_access       10 pts  – high read frequency by single process

Anomaly amplifier (AI layer):
  If multiple signals fire together the score is multiplied by
  a confidence factor derived from signal co-occurrence — mimicking
  a simple anomaly detector without requiring ML dependencies.
"""

import threading
from collections import deque, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from config import THRESHOLDS, TIME_WINDOW_SECONDS, SCORE_WEIGHTS, SCORE_DECAY_FACTOR
from .file_monitor import FileEvent
from rg_logger import get_logger

logger = get_logger("BehaviorAnalyzer")


@dataclass
class BehaviorSnapshot:
    """Point-in-time summary fed to the Decision Engine."""
    timestamp:               datetime
    risk_score:              float        # 0–100
    active_signals:          List[str]    # which rules fired
    renames_per_min:         int
    modifications_per_min:   int
    ext_changes_per_min:     int
    suspicious_prefix_count: int
    top_process:             str          # process triggering most events
    top_process_pid:         int
    top_process_access_rate: int


@dataclass
class _WindowCounter:
    """Thread-safe sliding-window event counter."""
    _events: deque = field(default_factory=deque)
    _lock:   threading.Lock = field(default_factory=threading.Lock)

    def add(self, ts: datetime):
        with self._lock:
            self._events.append(ts)
            self._purge(ts)

    def count(self, now: Optional[datetime] = None) -> int:
        now = now or datetime.now()
        with self._lock:
            self._purge(now)
            return len(self._events)

    def _purge(self, now: datetime):
        cutoff = now - timedelta(seconds=TIME_WINDOW_SECONDS)
        while self._events and self._events[0] < cutoff:
            self._events.popleft()


class BehaviorAnalyzer:
    """
    Receives FileEvents and maintains rolling behavioural statistics.
    Call .analyze() to get the current BehaviorSnapshot.
    """

    def __init__(self):
        self._renames       = _WindowCounter()
        self._modifications = _WindowCounter()
        self._ext_changes   = _WindowCounter()
        self._susp_prefixes = _WindowCounter()

        # Per-process file access tracking
        self._proc_access: Dict[str, _WindowCounter] = defaultdict(_WindowCounter)
        self._proc_pid:    Dict[str, int]             = {}

        self._prev_score   = 0.0
        self._lock         = threading.Lock()

    # ─────────────────────────────────────────
    # PUBLIC API
    # ─────────────────────────────────────────

    def ingest(self, event: FileEvent):
        """Feed a FileEvent into the analyzer."""
        now = event.timestamp

        if event.event_type == "rename":
            self._renames.add(now)
            self._check_ext_change(event)

        elif event.event_type == "modify":
            self._modifications.add(now)

        elif event.event_type in ("create", "access"):
            pass  # count via process tracker

        if event.suspicious:
            self._susp_prefixes.add(now)

        # Track process-level access rate (requires psutil enrichment upstream)
        proc = event.suspicious_why or "unknown"
        self._proc_access[proc].add(now)

    def analyze(self) -> BehaviorSnapshot:
        """Return current BehaviorSnapshot with risk score."""
        now = datetime.now()

        renames       = self._renames.count(now)
        modifications = self._modifications.count(now)
        ext_changes   = self._ext_changes.count(now)
        susp_prefix   = self._susp_prefixes.count(now)

        # Top process by access rate
        top_proc, top_rate = "unknown", 0
        top_pid = 0
        for proc, ctr in self._proc_access.items():
            rate = ctr.count(now)
            if rate > top_rate:
                top_proc, top_rate = proc, rate
                top_pid = self._proc_pid.get(proc, 0)

        # ── Signal evaluation ──────────────────
        signals: Dict[str, float] = {}

        if renames >= THRESHOLDS["rename_per_minute"]:
            # Linear scale: 1.0 at threshold, 2.0 at 2× threshold
            intensity = min(renames / THRESHOLDS["rename_per_minute"], 2.0)
            signals["rapid_rename"] = SCORE_WEIGHTS["rapid_rename"] * intensity

        if modifications >= THRESHOLDS["modifications_per_minute"]:
            intensity = min(modifications / THRESHOLDS["modifications_per_minute"], 2.0)
            signals["bulk_modification"] = SCORE_WEIGHTS["bulk_modification"] * intensity

        if ext_changes >= THRESHOLDS["ext_changes_per_minute"]:
            intensity = min(ext_changes / THRESHOLDS["ext_changes_per_minute"], 2.0)
            signals["ext_change"] = SCORE_WEIGHTS["ext_change"] * intensity

        if susp_prefix > 0:
            intensity = min(susp_prefix / 3, 2.0)
            signals["suspicious_prefix"] = SCORE_WEIGHTS["suspicious_prefix"] * intensity

        if top_rate >= THRESHOLDS["file_access_per_minute"]:
            intensity = min(top_rate / THRESHOLDS["file_access_per_minute"], 2.0)
            signals["bulk_access"] = SCORE_WEIGHTS["bulk_access"] * intensity

        # ── AI amplifier: co-occurrence confidence ──
        raw_score  = sum(signals.values())
        confidence = self._co_occurrence_factor(signals)
        score      = min(raw_score * confidence, 100.0)

        # Apply decay if no new signals
        if not signals:
            score = self._prev_score * SCORE_DECAY_FACTOR

        with self._lock:
            self._prev_score = score

        snapshot = BehaviorSnapshot(
            timestamp=now,
            risk_score=score,
            active_signals=list(signals.keys()),
            renames_per_min=renames,
            modifications_per_min=modifications,
            ext_changes_per_min=ext_changes,
            suspicious_prefix_count=susp_prefix,
            top_process=top_proc,
            top_process_pid=top_pid,
            top_process_access_rate=top_rate,
        )

        if score >= THRESHOLDS["risk_score_warn"]:
            logger.warning(
                f"Risk score {score:.1f} | signals={list(signals.keys())} | "
                f"renames={renames} mods={modifications} susp_prefix={susp_prefix}"
            )

        return snapshot

    # ─────────────────────────────────────────
    # PRIVATE HELPERS
    # ─────────────────────────────────────────

    def _check_ext_change(self, event: FileEvent):
        """Detect extension changes on rename events."""
        if event.dest_path:
            src_ext  = event.src_path.rsplit(".", 1)[-1].lower()
            dest_ext = event.dest_path.rsplit(".", 1)[-1].lower()
            if src_ext != dest_ext:
                self._ext_changes.add(event.timestamp)

    @staticmethod
    def _co_occurrence_factor(signals: Dict[str, float]) -> float:
        """
        AI amplifier: multiple signals firing simultaneously is a stronger
        ransomware indicator than any single signal alone.

        1 signal  → ×1.0  (no amplification)
        2 signals → ×1.3
        3 signals → ×1.6
        4 signals → ×1.9
        5 signals → ×2.2  (capped)
        """
        n = len(signals)
        if n == 0:
            return 1.0
        return min(1.0 + (n - 1) * 0.3, 2.2)
