"""
RANSOMGUARD – Ransomware Behaviour Simulator
Safe, controlled simulator for prototype testing.

NO real encryption is performed.
Creates dummy files and renames/modifies them to mimic ransomware patterns,
then automatically cleans up.

Usage:
  python simulator.py                      # mild simulation
  python simulator.py --intensity high     # aggressive simulation
  python simulator.py --mode rename        # rename attack only
  python simulator.py --mode mixed         # rename + modify + prefix
  python simulator.py --cleanup            # remove all sim files
"""

import os
import sys
import time
import shutil
import random
import argparse
import tempfile
import threading
from datetime import datetime

# ── Configuration ──────────────────────────────
SIM_DIR      = os.path.join(tempfile.gettempdir(), "rg_sim_files")
FILE_COUNT   = 30       # dummy files created
ATTACK_DELAY = 0.15     # seconds between file operations (mild)

INTENSITIES = {
    "low":    0.5,   # 0.5s between ops → ~2 renames/min (below threshold)
    "mild":   0.15,  # should trigger WARN
    "high":   0.05,  # should trigger ALERT/ISOLATE
    "brutal": 0.01,  # maximum aggression
}

SUSPICIOUS_EXTS    = [".locked", ".encrypted", ".crypt", ".enc"]
SUSPICIOUS_PREFIXES = ["locked_", "encrypted_", "crypt_"]
# ───────────────────────────────────────────────


def _banner(msg: str):
    print(f"\n{'─'*55}\n  {msg}\n{'─'*55}")


def setup_sim_files() -> list[str]:
    """Create dummy files to be 'attacked'."""
    os.makedirs(SIM_DIR, exist_ok=True)
    paths = []
    for i in range(FILE_COUNT):
        ext  = random.choice([".docx", ".xlsx", ".pdf", ".txt", ".jpg"])
        name = f"document_{i:03d}{ext}"
        path = os.path.join(SIM_DIR, name)
        with open(path, "w") as f:
            f.write(f"Dummy file #{i} – created for RansomGuard simulation.\n" * 5)
        paths.append(path)
    print(f"[SIM] Created {len(paths)} dummy files in: {SIM_DIR}")
    return paths


def simulate_rapid_rename(files: list[str], delay: float):
    """Rapidly rename files to suspicious names."""
    _banner("ATTACK: Rapid file renaming")
    renamed = []
    for path in files:
        if not os.path.exists(path):
            continue
        prefix = random.choice(SUSPICIOUS_PREFIXES)
        ext    = random.choice(SUSPICIOUS_EXTS)
        name   = prefix + os.path.splitext(os.path.basename(path))[0] + ext
        dest   = os.path.join(os.path.dirname(path), name)
        try:
            # In simulate_rapid_rename(), replace os.rename with:
            if not os.path.exists(dest):
                os.rename(path, dest)
            else:
                print(f"[SIM] Skipped (already renamed): {os.path.basename(dest)}")
            renamed.append(dest)
            print(f"[SIM] Renamed → {os.path.basename(dest)}")
        except Exception as e:
            print(f"[SIM] Rename failed: {e}")
        time.sleep(delay)
    return renamed


def simulate_bulk_modification(files: list[str], delay: float):
    """Rapidly modify file contents (simulates encryption in-place)."""
    _banner("ATTACK: Bulk file modification")
    for path in files:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "a") as f:
                f.write(f"[SIMULATED ENCRYPTION PAYLOAD @ {datetime.now().isoformat()}]\n" * 3)
            print(f"[SIM] Modified: {os.path.basename(path)}")
        except Exception as e:
            print(f"[SIM] Modify failed: {e}")
        time.sleep(delay)


def simulate_bulk_read(files: list[str], delay: float):
    """Rapidly read many files (mimics ransomware scanning stage)."""
    _banner("ATTACK: Bulk file read access")
    for path in files:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r") as f:
                _ = f.read()
            print(f"[SIM] Read: {os.path.basename(path)}")
        except Exception as e:
            print(f"[SIM] Read failed: {e}")
        time.sleep(delay)


def cleanup():
    """Remove all simulation files."""
    if os.path.exists(SIM_DIR):
        shutil.rmtree(SIM_DIR)
        print(f"[SIM] Cleaned up: {SIM_DIR}")
    else:
        print("[SIM] Nothing to clean up.")


def run_simulation(mode: str = "mixed", intensity: str = "mild"):
    delay = INTENSITIES.get(intensity, INTENSITIES["mild"])
    print(f"\n🦠 RansomGuard Simulator | mode={mode} | intensity={intensity} | delay={delay}s")
    print(f"   Watch directory: {SIM_DIR}")
    print(f"   Make sure RansomGuard is monitoring: {SIM_DIR}")
    print(f"   (Add SIM_DIR to WATCH_PATHS in config.py for testing)\n")

    input("   Press ENTER to begin simulation…")

    files = setup_sim_files()
    time.sleep(1)  # give monitor time to notice new files

    try:
        if mode in ("rename", "mixed"):
            renamed = simulate_rapid_rename(files, delay)

        if mode in ("modify", "mixed"):
            targets = renamed if mode == "mixed" else files
            simulate_bulk_modification(targets, delay)

        if mode in ("read", "mixed"):
            simulate_bulk_read(files, delay * 0.5)

    except KeyboardInterrupt:
        print("\n[SIM] Simulation interrupted by user.")

    print("\n[SIM] Simulation complete.")
    answer = input("Clean up simulation files? [Y/n]: ").strip().lower()
    if answer != "n":
        cleanup()


def main():
    parser = argparse.ArgumentParser(description="RansomGuard Behaviour Simulator")
    parser.add_argument("--mode",      choices=["rename","modify","read","mixed"], default="mixed")
    parser.add_argument("--intensity", choices=["low","mild","high","brutal"],     default="mild")
    parser.add_argument("--cleanup",   action="store_true", help="Remove simulation files and exit")
    args = parser.parse_args()

    if args.cleanup:
        cleanup()
        return

    run_simulation(args.mode, args.intensity)


if __name__ == "__main__":
    main()
