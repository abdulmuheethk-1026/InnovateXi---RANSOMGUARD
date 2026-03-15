"""
RANSOMGUARD – System Tray Application
Main entry point after installation. Shows tray icon with status,
launches activation if needed, and runs the guard in background.
"""

import sys
import os
import threading
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from app.activation_gui import ActivationWindow

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ── Dependency check ──────────────────────────────
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

from app.license_manager import is_activated, get_license_status

from rg_logger import get_logger

logger = get_logger("TrayApp")
import os

LICENSE_FILE = r"C:\ProgramData\RansomGuard\license.dat"

def reset_activation():
    if os.path.exists(LICENSE_FILE):
        os.remove(LICENSE_FILE)
        print("Activation reset successfully.")
    else:
        print("License file not found.")

APP_NAME = "RansomGuard"
ACCENT   = "#E84545"
BG_DARK  = "#1A1A2E"
BG_PANEL = "#16213E"
FG_WHITE = "#EAEAEA"
FG_GRAY  = "#8892A4"
FG_GREEN = "#2ECC71"


# ─────────────────────────────────────────────────────
# DASHBOARD WINDOW
# ─────────────────────────────────────────────────────

class Dashboard:
    def __init__(self, agent=None):
        self.agent  = agent
        self.root   = None
        self._open  = False

    def show(self):
        if self._open:
            self.root.lift()
            self.root.focus_force()
            return
        self._open = True
        self.root  = tk.Tk()
        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self._hide)
        self._refresh_loop()
        self.root.mainloop()
        self._open = False

    def _hide(self):
        self.root.destroy()
        self._open = False

    def _build(self):
        r = self.root
        r.title(f"{APP_NAME} – Dashboard")
        r.geometry("640x460")
        r.resizable(False, False)
        r.configure(bg=BG_DARK)
        r.eval("tk::PlaceWindow . center")

        # Header
        hdr = tk.Frame(r, bg=ACCENT, pady=15, padx=25)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"🛡️  {APP_NAME}  —  Early Warning System",
                 font=("Segoe UI", 13, "bold"), bg=ACCENT, fg="white").pack(side="left")
        tk.Label(hdr, text="v1.0.0", font=("Segoe UI", 9),
                 bg=ACCENT, fg="#FFAAAA").pack(side="right")

        # Status card
        card = tk.Frame(r, bg=BG_PANEL, padx=25, pady=20)
        card.pack(fill="x", padx=20, pady=15)

        self.status_icon  = tk.Label(card, text="🟢", font=("Segoe UI", 28),
                                     bg=BG_PANEL)
        self.status_icon.pack(side="left")
        info = tk.Frame(card, bg=BG_PANEL)
        info.pack(side="left", padx=15)
        self.status_title = tk.Label(info, text="Protected", font=("Segoe UI", 14, "bold"),
                                     bg=BG_PANEL, fg=FG_GREEN)
        self.status_title.pack(anchor="w")
        self.status_sub   = tk.Label(info, text="Monitoring 3 paths • Score: 0",
                                     font=("Segoe UI", 9), bg=BG_PANEL, fg=FG_GRAY)
        self.status_sub.pack(anchor="w")

        # Stats row
        stats = tk.Frame(r, bg=BG_DARK)
        stats.pack(fill="x", padx=20)

        self.stat_vars = {}
        for label, key, val in [
            ("Events Ingested",   "events",    "0"),
            ("Alerts Fired",      "alerts",    "0"),
            ("Backups Created",   "backups",   "0"),
            ("Risk Score",        "score",     "0"),
        ]:
            box = tk.Frame(stats, bg=BG_PANEL, padx=18, pady=14)
            box.pack(side="left", fill="x", expand=True, padx=5)
            v = tk.StringVar(value=val)
            self.stat_vars[key] = v
            tk.Label(box, textvariable=v, font=("Segoe UI", 22, "bold"),
                     bg=BG_PANEL, fg=ACCENT).pack()
            tk.Label(box, text=label, font=("Segoe UI", 8),
                     bg=BG_PANEL, fg=FG_GRAY).pack()

        # License info
        lic_frame = tk.Frame(r, bg=BG_PANEL, padx=25, pady=12)
        lic_frame.pack(fill="x", padx=20, pady=15)
        lic = get_license_status()
        if lic.get("valid"):
            lic_txt = (f"License: {lic['tier']}  •  "
                       f"Key: {lic['key_masked']}  •  "
                       f"Expires: {lic['expiry']}  ({lic['days_remaining']} days left)")
            lic_clr = FG_GREEN
        else:
            lic_txt = f"⚠ No valid license: {lic.get('reason', 'Unknown')}"
            lic_clr = ACCENT
        tk.Label(lic_frame, text=lic_txt, font=("Segoe UI", 9),
                 bg=BG_PANEL, fg=lic_clr).pack(anchor="w")

        # Buttons
        btn_row = tk.Frame(r, bg=BG_DARK)
        btn_row.pack(fill="x", padx=20, pady=5)
        for txt, cmd in [
            ("📂 Open Logs",         self._open_logs),
            ("💾 Create Backup Now", self._manual_backup),
            ("🔑 License Details",   self._show_license),
        ]:
            tk.Button(btn_row, text=txt, font=("Segoe UI", 9, "bold"),
                      bg=BG_PANEL, fg=FG_WHITE, relief="flat",
                      cursor="hand2", pady=8, padx=14,
                      activebackground="#2C3E50",
                      command=cmd).pack(side="left", padx=5)

    def _refresh_loop(self):
        if not self._open:
            return
        if self.agent:
            s = self.agent._stats
            score = 0
            try:
                snap = self.agent._analyzer.analyze()
                score = int(snap.risk_score)
            except Exception:
                pass

            self.stat_vars["events"].set(str(s.get("events_ingested", 0)))
            self.stat_vars["alerts"].set(str(s.get("alerts_fired", 0)))
            self.stat_vars["backups"].set(str(s.get("backups_created", 0)))
            self.stat_vars["score"].set(str(score))

            if score >= 85:
                self.status_icon.config(text="🔴")
                self.status_title.config(text="CRITICAL THREAT", fg=ACCENT)
            elif score >= 65:
                self.status_icon.config(text="🟠")
                self.status_title.config(text="Alert", fg="#E67E22")
            elif score >= 40:
                self.status_icon.config(text="🟡")
                self.status_title.config(text="Warning", fg="#F1C40F")
            else:
                self.status_icon.config(text="🟢")
                self.status_title.config(text="Protected", fg=FG_GREEN)

        self.root.after(3000, self._refresh_loop)

    def _open_logs(self):
        log_dir = r"C:\RansomGuard_Logs"
        if os.path.exists(log_dir):
            os.startfile(log_dir)
        else:
            messagebox.showinfo(APP_NAME, f"Log directory not found:\n{log_dir}")

    def _manual_backup(self):
        from core.backup_manager import create_snapshot
        path = create_snapshot()
        if path:
            messagebox.showinfo(APP_NAME, f"Backup created:\n{path}")
        else:
            messagebox.showerror(APP_NAME, "Backup failed. Check logs.")

    def _show_license(self):
        lic = get_license_status()
        if lic.get("valid"):
            info = (f"Status:        Active\n"
                    f"Tier:          {lic['tier']}\n"
                    f"Key:           {lic['key_masked']}\n"
                    f"Seats:         {lic['seats']}\n"
                    f"Activated:     {lic['activated']}\n"
                    f"Expires:       {lic['expiry']}\n"
                    f"Days remaining:{lic['days_remaining']}")
        else:
            info = f"No valid license.\nReason: {lic.get('reason')}"
        messagebox.showinfo(f"{APP_NAME} – License", info)


# ─────────────────────────────────────────────────────
# TRAY ICON
# ─────────────────────────────────────────────────────

def _make_tray_icon():
    """Generate a shield icon programmatically."""
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d   = ImageDraw.Draw(img)
    d.polygon([(32, 4), (60, 18), (60, 38), (32, 60), (4, 38), (4, 18)],
              fill="#E84545")
    d.polygon([(32, 12), (52, 22), (52, 36), (32, 52), (12, 36), (12, 22)],
              fill="#C0392B")
    d.text((22, 22), "RG", fill="white")
    return img

def run_tray(agent, dashboard):
    from core.backup_manager import create_snapshot

    icon_img = _make_tray_icon()

    def open_dashboard(icon, item):
        threading.Thread(target=dashboard.show, daemon=True).start()

    def start_scan(icon, item):
        logger.info("Manual scan triggered")
        messagebox.showinfo("RansomGuard", "Scan feature will be added soon.")

    def view_status(icon, item):
        if dashboard:
            threading.Thread(target=dashboard.show, daemon=True).start()

    def exit_app(icon, item):
        logger.info("RansomGuard shutting down...")
        agent.stop()
        icon.stop()
        sys.exit(0)

    menu = pystray.Menu(
        pystray.MenuItem("Start Scan", start_scan),
        pystray.MenuItem("View Status", view_status),
        pystray.MenuItem("Create Backup", lambda icon, item: create_snapshot()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Exit", exit_app)
    )

    icon = pystray.Icon(APP_NAME, icon_img, APP_NAME, menu)

    icon.run()


# ─────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────

def main():

     # Reset activation if requested
    if "--reset" in sys.argv:
        reset_activation()

    # License check
    if not is_activated():

        activated = False

        def on_success():
            nonlocal activated
            activated = True

        win = ActivationWindow(on_success=on_success)
        win.run()

        if not activated:
            sys.exit(0)
    print("Activation status:", is_activated())

    # 2. Start guard agent
    from core.ransomguard_main import RansomGuardAgent
    import signal

    agent     = RansomGuardAgent()
    dashboard = Dashboard(agent=agent)

    def _sig(sig, frame):
        logger.info("Stopping RansomGuard...")
        agent.stop()
        os._exit(0)
    signal.signal(signal.SIGINT,  _sig)
    signal.signal(signal.SIGTERM, _sig)

    agent.start()

    # 3. Tray / dashboard
    if TRAY_AVAILABLE:
        run_tray(agent, dashboard)
    else:
        # Fallback: show dashboard directly
        dashboard.show()
        agent.stop()


if __name__ == "__main__":
    main()
