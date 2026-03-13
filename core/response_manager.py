"""
RANSOMGUARD – Response Manager
Executes the appropriate response when the Decision Engine fires.

Actions:
  1. Alert  – tkinter popup (non-blocking) + system tray notification
  2. Isolate – terminate suspicious process via psutil
  3. Backup  – trigger BackupManager snapshot
  4. Network block (optional) – Windows Firewall outbound block
"""

import os
import threading
from typing import Optional

try:
    import psutil
except ImportError:
    psutil = None  # Gracefully degrade; process kill disabled

from config import PROCESS_KILL_ENABLED, NETWORK_BLOCK_ENABLED
from .decision_engine import Decision, ThreatLevel
from .backup_manager import create_snapshot
from rg_logger import get_logger, EventLogger

logger      = get_logger("ResponseManager")
event_log   = EventLogger()

# Tkinter must run on the main thread – we post alerts to a queue
import queue
_alert_queue: queue.Queue = queue.Queue()


# ──────────────────────────────────────────────
# ALERT
# ──────────────────────────────────────────────

def _show_popup(title: str, message: str):
    """Display a tkinter warning dialog (runs on calling thread)."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        messagebox.showwarning(title, message, master=root)
        root.destroy()
    except Exception as e:
        logger.warning(f"Popup failed (headless?): {e}")
        print(f"\n{'='*60}\n{title}\n{message}\n{'='*60}\n")


def _alert_worker():
    """Background thread that drains the alert queue."""
    while True:
        title, msg = _alert_queue.get()
        _show_popup(title, msg)
        _alert_queue.task_done()


_alert_thread = threading.Thread(target=_alert_worker, daemon=True)
_alert_thread.start()


def send_alert(decision: Decision):
    level_titles = {
        ThreatLevel.WARN:    "RansomGuard – Notice",
        ThreatLevel.ALERT:   "RansomGuard – WARNING",
        ThreatLevel.ISOLATE: "RansomGuard – CRITICAL THREAT",
    }
    title = level_titles.get(decision.level, "RansomGuard")
    _alert_queue.put((title, decision.message))
    logger.warning(f"Alert queued: [{decision.level.value}] score={decision.risk_score:.0f}")


# ──────────────────────────────────────────────
# ISOLATE (process termination)
# ──────────────────────────────────────────────

def isolate_process(pid: int, process_name: str) -> bool:
    """
    Attempt to terminate the suspicious process.
    Returns True if killed successfully.
    """
    if not PROCESS_KILL_ENABLED:
        logger.info(f"Process kill disabled in config. Would kill PID {pid} ({process_name})")
        return False

    if psutil is None:
        logger.error("psutil not installed — cannot terminate process.")
        return False

    if pid <= 0:
        logger.warning("No valid PID provided for isolation.")
        return False

    try:
        proc = psutil.Process(pid)
        proc.terminate()
        proc.wait(timeout=5)
        logger.warning(f"Process terminated: {process_name} (PID {pid})")
        return True
    except psutil.NoSuchProcess:
        logger.info(f"Process {pid} already gone.")
        return True
    except psutil.AccessDenied:
        logger.error(f"Access denied terminating PID {pid}. Run as Administrator.")
        return False
    except Exception as e:
        logger.error(f"Failed to terminate PID {pid}: {e}")
        return False


# ──────────────────────────────────────────────
# NETWORK BLOCK (Windows Firewall)
# ──────────────────────────────────────────────

def block_network(process_name: str) -> bool:
    """Add Windows Firewall rule to block outbound traffic from process."""
    if not NETWORK_BLOCK_ENABLED:
        return False
    try:
        import subprocess
        rule_name = f"RansomGuard_Block_{process_name}"
        subprocess.run([
            "netsh", "advfirewall", "firewall", "add", "rule",
            f"name={rule_name}",
            "dir=out",
            "action=block",
            f"program={process_name}",
        ], check=True, capture_output=True)
        logger.warning(f"Network blocked for process: {process_name}")
        return True
    except Exception as e:
        logger.error(f"Network block failed: {e}")
        return False


# ──────────────────────────────────────────────
# ORCHESTRATOR
# ──────────────────────────────────────────────

def execute(decision: Decision):
    """
    Central response dispatcher — called by the main agent loop.
    """
    snap    = decision.snapshot
    pid     = snap.top_process_pid
    proc    = snap.top_process

    action_taken = "none"

    # 1. Alert
    if decision.should_alert:
        send_alert(decision)
        action_taken = "alert"

    # 2. Isolate
    if decision.should_isolate:
        killed = isolate_process(pid, proc)
        if NETWORK_BLOCK_ENABLED:
            block_network(proc)
        action_taken = "isolate+kill" if killed else "isolate_failed"

    # 3. Backup
    if decision.should_backup:
        backup_path = create_snapshot()
        action_taken += f"|backup→{backup_path}"

    # 4. Event log
    event_log.log(
        file_path    = proc,
        operation    = "aggregate",
        risk_score   = decision.risk_score,
        trigger      = ", ".join(snap.active_signals) or "none",
        action       = action_taken,
        process_name = proc,
        pid          = pid,
    )
