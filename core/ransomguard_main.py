"""
RANSOMGUARD – Main Agent
Wires all components together and runs the event loop.

Usage:
  python ransomguard_main.py          # foreground mode
  python ransomguard_main.py --service  # Windows Service mode (via pywin32)

Architecture:
  FileMonitor  →  BehaviorAnalyzer  →  (timer-based)  →  DecisionEngine  →  ResponseManager
"""

import sys
import time
import signal
import argparse
import threading
from datetime import datetime
from config import THRESHOLDS
from .file_monitor import FileMonitor
from .behavior_analyzer import BehaviorAnalyzer
from .decision_engine import evaluate, ThreatLevel
from .response_manager import execute
from .backup_manager import create_snapshot
from rg_logger import get_logger



logger = get_logger("RansomGuard")

ANALYSIS_INTERVAL = 5  # seconds between analysis cycles


class RansomGuardAgent:
    def __init__(self):
        self._analyzer = BehaviorAnalyzer()
        self._monitor  = FileMonitor(on_event=self._on_file_event)
        self._running  = False
        self._stats    = {
            "events_ingested": 0,
            "alerts_fired":    0,
            "isolations":      0,
            "backups_created": 0,
            "start_time":      None,
        }

    # ─────────────────────────────────────────
    # LIFECYCLE
    # ─────────────────────────────────────────

    def start(self):
        logger.info("=" * 55)
        logger.info("  RANSOMGUARD – Early Warning System  v1.0")
        logger.info("=" * 55)
        logger.info(f"Analysis interval : {ANALYSIS_INTERVAL}s")
        logger.info(f"Rename threshold  : {THRESHOLDS['rename_per_minute']}/min")
        logger.info(f"Mod threshold     : {THRESHOLDS['modifications_per_minute']}/min")
        logger.info(f"Alert threshold   : score ≥ {THRESHOLDS['risk_score_alert']}")
        logger.info(f"Isolate threshold : score ≥ {THRESHOLDS['risk_score_isolate']}")
        logger.info("-" * 55)

        self._running          = True
        self._stats["start_time"] = datetime.now()

        self._monitor.start()

        # Analysis timer runs on a background thread
        self._analysis_thread = threading.Thread(
            target=self._analysis_loop, daemon=True
        )
        self._analysis_thread.start()

        logger.info("Agent running. Press Ctrl+C to stop.\n")

    def stop(self):
        logger.info("Shutting down RansomGuard…")
        self._running = False
        self._monitor.stop()
        self._print_summary()

    def wait(self):
        """Block until stop() is called (main thread idle loop)."""
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    # ─────────────────────────────────────────
    # EVENT HANDLER  (called from watchdog threads)
    # ─────────────────────────────────────────

    def _on_file_event(self, event):
        self._analyzer.ingest(event)
        self._stats["events_ingested"] += 1

    # ─────────────────────────────────────────
    # ANALYSIS LOOP  (timer-based, every N seconds)
    # ─────────────────────────────────────────

    def _analysis_loop(self):
        while self._running:
            time.sleep(ANALYSIS_INTERVAL)
            try:
                snapshot = self._analyzer.analyze()
                decision = evaluate(snapshot)

                if decision.level != ThreatLevel.CLEAR:
                    logger.info(
                        f"[{decision.level.value}] score={decision.risk_score:.1f} "
                        f"| signals={snapshot.active_signals}"
                    )

                if decision.should_alert:
                    self._stats["alerts_fired"] += 1
                if decision.should_isolate:
                    self._stats["isolations"] += 1
                if decision.should_backup:
                    self._stats["backups_created"] += 1

                execute(decision)

            except Exception as e:
                logger.error(f"Analysis loop error: {e}", exc_info=True)

    # ─────────────────────────────────────────
    # STATS SUMMARY
    # ─────────────────────────────────────────

    def _print_summary(self):
        up = datetime.now() - self._stats["start_time"]
        logger.info("-" * 55)
        logger.info(f"Uptime            : {str(up).split('.')[0]}")
        logger.info(f"Events ingested   : {self._stats['events_ingested']}")
        logger.info(f"Alerts fired      : {self._stats['alerts_fired']}")
        logger.info(f"Process isolations: {self._stats['isolations']}")
        logger.info(f"Backups created   : {self._stats['backups_created']}")
        logger.info("-" * 55)


# ─────────────────────────────────────────────
# WINDOWS SERVICE WRAPPER  (pywin32)
# ─────────────────────────────────────────────

def _try_service_mode():
    try:
        import win32serviceutil
        import win32service
        import win32event
        import servicemanager

        class RansomGuardService(win32serviceutil.ServiceFramework):
            _svc_name_         = "RansomGuard"
            _svc_display_name_ = "RansomGuard Early Warning System"
            _svc_description_  = "Monitors file behaviour for ransomware activity."

            def __init__(self, args):
                super().__init__(args)
                self._stop_event = win32event.CreateEvent(None, 0, 0, None)
                self._agent      = RansomGuardAgent()

            def SvcStop(self):
                self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
                self._agent.stop()
                win32event.SetEvent(self._stop_event)

            def SvcDoRun(self):
                servicemanager.LogMsg(
                    servicemanager.EVENTLOG_INFORMATION_TYPE,
                    servicemanager.PYS_SERVICE_STARTED,
                    (self._svc_name_, ""),
                )
                self._agent.start()
                win32event.WaitForSingleObject(self._stop_event, win32event.INFINITE)

        win32serviceutil.HandleCommandLine(RansomGuardService)

    except ImportError:
        logger.error("pywin32 not installed — cannot run as Windows Service.")
        logger.error("Install with: pip install pywin32")
        sys.exit(1)


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="RansomGuard Early Warning System")
    parser.add_argument("--service", action="store_true", help="Run as Windows Service")
    parser.add_argument("--install", action="store_true", help="Install Windows Service")
    parser.add_argument("--remove",  action="store_true", help="Remove Windows Service")
    args = parser.parse_args()

    if args.service or args.install or args.remove:
        _try_service_mode()
        return

    # Foreground mode
    agent = RansomGuardAgent()

    def _sig_handler(sig, frame):
        agent.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT,  _sig_handler)
    signal.signal(signal.SIGTERM, _sig_handler)

    agent.start()
    agent.wait()


if __name__ == "__main__":
    main()
