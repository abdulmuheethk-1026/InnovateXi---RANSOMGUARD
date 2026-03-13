"""
RANSOMGUARD – Decision Engine
Evaluates BehaviorSnapshots and emits Decision objects.

Decision levels:
  CLEAR    – score < warn threshold
  WARN     – score ≥ warn threshold     → log
  ALERT    – score ≥ alert threshold    → popup + log
  ISOLATE  – score ≥ isolate threshold  → kill process + backup + log
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from config import THRESHOLDS
from .behavior_analyzer import BehaviorSnapshot
from rg_logger import get_logger

logger = get_logger("DecisionEngine")


class ThreatLevel(Enum):
    CLEAR   = "CLEAR"
    WARN    = "WARN"
    ALERT   = "ALERT"
    ISOLATE = "ISOLATE"


@dataclass
class Decision:
    level:          ThreatLevel
    risk_score:     float
    snapshot:       BehaviorSnapshot
    message:        str
    should_alert:   bool
    should_isolate: bool
    should_backup:  bool


_LAST_LEVEL = ThreatLevel.CLEAR    # module-level state to avoid repeat alerts


def evaluate(snapshot: BehaviorSnapshot) -> Decision:
    global _LAST_LEVEL
    score = snapshot.risk_score

    if score >= THRESHOLDS["risk_score_isolate"]:
        level = ThreatLevel.ISOLATE
        msg   = (
            f"🔴 CRITICAL – Ransomware behaviour detected!\n"
            f"Risk score: {score:.0f}/100\n"
            f"Signals: {', '.join(snapshot.active_signals)}\n"
            f"Process: {snapshot.top_process} (PID {snapshot.top_process_pid})\n"
            f"Action: Isolating process and creating backup."
        )
        should_alert   = True
        should_isolate = True
        should_backup  = True

    elif score >= THRESHOLDS["risk_score_alert"]:
        level = ThreatLevel.ALERT
        msg   = (
            f"🟠 WARNING – Suspicious file activity detected.\n"
            f"Risk score: {score:.0f}/100\n"
            f"Signals: {', '.join(snapshot.active_signals)}\n"
            f"Renames/min: {snapshot.renames_per_min}  "
            f"Modifications/min: {snapshot.modifications_per_min}"
        )
        should_alert   = True
        should_isolate = False
        should_backup  = True

    elif score >= THRESHOLDS["risk_score_warn"]:
        level = ThreatLevel.WARN
        msg   = (
            f"🟡 NOTICE – Elevated file activity.\n"
            f"Risk score: {score:.0f}/100\n"
            f"Monitoring closely."
        )
        should_alert   = (_LAST_LEVEL == ThreatLevel.CLEAR)  # only first warn
        should_isolate = False
        should_backup  = False

    else:
        level = ThreatLevel.CLEAR
        msg   = f"✅ Normal — score={score:.0f}"
        should_alert   = False
        should_isolate = False
        should_backup  = False

    if level != _LAST_LEVEL:
        logger.info(f"Threat level changed: {_LAST_LEVEL.value} → {level.value} | score={score:.1f}")
    _LAST_LEVEL = level

    return Decision(
        level=level,
        risk_score=score,
        snapshot=snapshot,
        message=msg,
        should_alert=should_alert,
        should_isolate=should_isolate,
        should_backup=should_backup,
    )
