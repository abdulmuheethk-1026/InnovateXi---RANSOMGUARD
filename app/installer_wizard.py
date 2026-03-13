"""
RANSOMGUARD – Install Wizard
Multi-step installer UI: Welcome → T&C → Install Path → License → Finish
Runs on first launch from the setup .exe.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import json
import shutil
import threading
import subprocess

APP_NAME   = "RansomGuard"
VERSION    = "1.0.0"
ACCENT     = "#E84545"
BG_DARK    = "#1A1A2E"
BG_PANEL   = "#16213E"
BG_STEP    = "#0F3460"
FG_WHITE   = "#EAEAEA"
FG_GRAY    = "#8892A4"
FG_GREEN   = "#2ECC71"
DEFAULT_INSTALL = r"C:\Program Files\RansomGuard"

TERMS_TEXT = """RANSOMGUARD END USER LICENSE AGREEMENT (EULA)

Version 1.0 | Effective: 2024

IMPORTANT – READ CAREFULLY BEFORE INSTALLING

By installing RansomGuard, you agree to be bound by the terms of this agreement. If you do not agree, do not install this software.

1. GRANT OF LICENSE
RansomGuard grants you a non-exclusive, non-transferable license to install and use this software on the number of devices specified in your license tier. This license is valid for the duration specified at activation.

2. PERMITTED USE
You may use RansomGuard solely for lawful cybersecurity monitoring of systems you own or have explicit written permission to monitor. Use on systems without authorization is strictly prohibited.

3. RESTRICTIONS
You may not: (a) reverse engineer, decompile, or disassemble the software; (b) rent, lease, or transfer the software to third parties; (c) remove or alter any proprietary notices or labels; (d) use the software to conduct offensive security operations.

4. PRIVACY & DATA
RansomGuard monitors file system metadata only. No file contents are read, transmitted, or stored. Log files are stored locally and never sent externally. No telemetry is collected in this prototype version.

5. DISCLAIMER OF WARRANTIES
THE SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND. RANSOMGUARD SHALL NOT BE LIABLE FOR ANY DATA LOSS, SYSTEM DAMAGE, OR BUSINESS INTERRUPTION ARISING FROM USE OR INABILITY TO USE THE SOFTWARE.

6. LIMITATION OF LIABILITY
IN NO EVENT SHALL RANSOMGUARD'S LIABILITY EXCEED THE AMOUNT PAID FOR THE LICENSE. RANSOMGUARD IS AN EARLY WARNING TOOL AND DOES NOT GUARANTEE PREVENTION OF RANSOMWARE ATTACKS.

7. TERMINATION
This license terminates automatically if you breach any term. Upon termination, you must destroy all copies of the software.

8. GOVERNING LAW
This agreement is governed by applicable local laws. Any disputes shall be resolved in the jurisdiction where the license was purchased.

9. UPDATES
RansomGuard may provide updates at its discretion. Major version updates may require a new license purchase.

10. ENTIRE AGREEMENT
This EULA constitutes the entire agreement between you and RansomGuard regarding this software.

By clicking "I Agree", you confirm you have read, understood, and accept these terms.

© 2024 RansomGuard. All rights reserved.
"""


class InstallerWizard:
    STEPS = ["Welcome", "License Agreement", "Install Location", "Installing", "Finish"]

    def __init__(self):
        self.root = tk.Tk()
        self.current_step = 0
        self.install_path = tk.StringVar(value=DEFAULT_INSTALL)
        self.agreed       = tk.BooleanVar(value=False)
        self.add_startup  = tk.BooleanVar(value=True)
        self.add_shortcut = tk.BooleanVar(value=True)
        self._build_shell()
        self._show_step(0)

    # ────────────────────────────────────────────
    # SHELL  (persistent outer frame)
    # ────────────────────────────────────────────

    def _build_shell(self):
        r = self.root
        r.title(f"{APP_NAME} Setup v{VERSION}")
        r.geometry("680x520")
        r.resizable(False, False)
        r.configure(bg=BG_DARK)
        r.eval("tk::PlaceWindow . center")

        # Left sidebar
        self.sidebar = tk.Frame(r, bg=BG_STEP, width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="🛡️", font=("Segoe UI", 40),
                 bg=BG_STEP, fg=ACCENT).pack(pady=(30, 5))
        tk.Label(self.sidebar, text=APP_NAME, font=("Segoe UI", 16, "bold"),
                 bg=BG_STEP, fg=FG_WHITE).pack()
        tk.Label(self.sidebar, text=f"v{VERSION}", font=("Segoe UI", 9),
                 bg=BG_STEP, fg=FG_GRAY).pack(pady=(2, 30))

        self.step_labels = []
        for i, name in enumerate(self.STEPS):
            lbl = tk.Label(self.sidebar, text=f"  {name}",
                           font=("Segoe UI", 9), bg=BG_STEP,
                           fg=FG_GRAY, anchor="w")
            lbl.pack(fill="x", padx=10, pady=3)
            self.step_labels.append(lbl)

        # Right content area
        self.content = tk.Frame(r, bg=BG_DARK)
        self.content.pack(side="right", fill="both", expand=True)

        # Bottom button bar
        self.btn_bar = tk.Frame(r, bg=BG_PANEL, pady=12, padx=20)
        self.btn_bar.pack(side="bottom", fill="x")

        self.btn_back = tk.Button(self.btn_bar, text="◀  Back",
            font=("Segoe UI", 9, "bold"), bg="#2C3E50", fg=FG_WHITE,
            relief="flat", padx=16, pady=6, cursor="hand2",
            command=self._back)
        self.btn_back.pack(side="left")

        self.btn_next = tk.Button(self.btn_bar, text="Next  ▶",
            font=("Segoe UI", 9, "bold"), bg=ACCENT, fg="white",
            relief="flat", padx=16, pady=6, cursor="hand2",
            command=self._next)
        self.btn_next.pack(side="right")

        self.btn_cancel = tk.Button(self.btn_bar, text="Cancel",
            font=("Segoe UI", 9), bg=BG_PANEL, fg=FG_GRAY,
            relief="flat", padx=16, pady=6, cursor="hand2",
            command=self._cancel)
        self.btn_cancel.pack(side="right", padx=(0, 10))

    # ────────────────────────────────────────────
    # STEP ROUTING
    # ────────────────────────────────────────────

    def _show_step(self, idx: int):
        self.current_step = idx
        for widget in self.content.winfo_children():
            widget.destroy()

        # Update sidebar highlights
        for i, lbl in enumerate(self.step_labels):
            if i == idx:
                lbl.config(fg=ACCENT, font=("Segoe UI", 9, "bold"))
            elif i < idx:
                lbl.config(fg=FG_GREEN, font=("Segoe UI", 9))
            else:
                lbl.config(fg=FG_GRAY, font=("Segoe UI", 9))

        steps = [
            self._step_welcome,
            self._step_terms,
            self._step_location,
            self._step_installing,
            self._step_finish,
        ]
        steps[idx]()

        # Button states
        self.btn_back.config(state="normal" if idx > 0 else "disabled")
        if idx == len(self.STEPS) - 1:
            self.btn_next.config(text="Launch RansomGuard  🛡️")
            self.btn_cancel.config(state="disabled")
        elif idx == 3:
            self.btn_next.config(state="disabled")
            self.btn_back.config(state="disabled")
        else:
            self.btn_next.config(text="Next  ▶", state="normal")

    def _next(self):
        if self.current_step == 1 and not self.agreed.get():
            messagebox.showwarning("Agreement Required",
                "You must accept the License Agreement to continue.")
            return
        if self.current_step == len(self.STEPS) - 1:
            self._launch_app()
            return
        self._show_step(self.current_step + 1)
        if self.current_step == 3:
            self.root.after(500, self._run_install)

    def _back(self):
        if self.current_step > 0:
            self._show_step(self.current_step - 1)

    def _cancel(self):
        if messagebox.askyesno("Cancel Setup", "Are you sure you want to cancel installation?"):
            self.root.destroy()

    # ────────────────────────────────────────────
    # STEP PAGES
    # ────────────────────────────────────────────

    def _step_welcome(self):
        f = self.content
        tk.Label(f, text="Welcome to RansomGuard Setup",
                 font=("Segoe UI", 16, "bold"), bg=BG_DARK, fg=FG_WHITE
                 ).pack(pady=(40, 8), padx=30, anchor="w")
        tk.Label(f,
                 text=(f"This wizard will guide you through the installation of "
                       f"{APP_NAME} v{VERSION} — a lightweight ransomware early "
                       f"warning system designed for small and medium enterprises.\n\n"
                       f"RansomGuard monitors file behaviour in real time, detects "
                       f"ransomware patterns early, and automatically backs up your "
                       f"critical files before damage occurs.\n\n"
                       f"Click Next to continue."),
                 font=("Segoe UI", 10), bg=BG_DARK, fg=FG_GRAY,
                 wraplength=430, justify="left"
                 ).pack(padx=30, anchor="w")

        # Feature highlights
        feats = [
            ("🔍", "Real-time file behaviour monitoring"),
            ("⚡", "AI-powered anomaly detection"),
            ("💾", "Automatic secure backup snapshots"),
            ("🛑", "Instant process isolation on threat"),
        ]
        feat_frame = tk.Frame(f, bg=BG_PANEL, padx=20, pady=15)
        feat_frame.pack(fill="x", padx=30, pady=20)
        for icon, txt in feats:
            row = tk.Frame(feat_frame, bg=BG_PANEL)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=icon, font=("Segoe UI", 12),
                     bg=BG_PANEL, fg=ACCENT, width=3).pack(side="left")
            tk.Label(row, text=txt, font=("Segoe UI", 10),
                     bg=BG_PANEL, fg=FG_WHITE).pack(side="left")

    def _step_terms(self):
        f = self.content
        tk.Label(f, text="License Agreement",
                 font=("Segoe UI", 14, "bold"), bg=BG_DARK, fg=FG_WHITE
                 ).pack(pady=(25, 5), padx=25, anchor="w")
        tk.Label(f, text="Please read and accept the End User License Agreement.",
                 font=("Segoe UI", 9), bg=BG_DARK, fg=FG_GRAY
                 ).pack(padx=25, anchor="w")

        # Scrollable text box
        txt_frame = tk.Frame(f, bg=ACCENT, padx=1, pady=1)
        txt_frame.pack(fill="both", expand=True, padx=25, pady=10)

        sb = tk.Scrollbar(txt_frame)
        sb.pack(side="right", fill="y")

        txt = tk.Text(txt_frame, font=("Consolas", 8), bg="#0A1628", fg=FG_GRAY,
                      relief="flat", wrap="word", yscrollcommand=sb.set,
                      padx=10, pady=10)
        txt.insert("1.0", TERMS_TEXT)
        txt.config(state="disabled")
        txt.pack(fill="both", expand=True)
        sb.config(command=txt.yview)

        # Checkbox
        chk = tk.Checkbutton(f,
            text="I have read and agree to the License Agreement",
            variable=self.agreed,
            font=("Segoe UI", 10, "bold"), bg=BG_DARK, fg=FG_WHITE,
            activebackground=BG_DARK, activeforeground=ACCENT,
            selectcolor=BG_PANEL, cursor="hand2"
        )
        chk.pack(padx=25, pady=(0, 10), anchor="w")

    def _step_location(self):
        f = self.content
        tk.Label(f, text="Installation Location",
                 font=("Segoe UI", 14, "bold"), bg=BG_DARK, fg=FG_WHITE
                 ).pack(pady=(25, 5), padx=25, anchor="w")
        tk.Label(f, text="Choose where RansomGuard will be installed.",
                 font=("Segoe UI", 9), bg=BG_DARK, fg=FG_GRAY
                 ).pack(padx=25, anchor="w", pady=(0, 20))

        path_frame = tk.Frame(f, bg=BG_DARK)
        path_frame.pack(fill="x", padx=25)
        tk.Entry(path_frame, textvariable=self.install_path,
                 font=("Consolas", 10), bg=BG_PANEL, fg=FG_WHITE,
                 insertbackground=FG_WHITE, relief="flat"
                 ).pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        tk.Button(path_frame, text="Browse…",
                  font=("Segoe UI", 9), bg="#2C3E50", fg=FG_WHITE,
                  relief="flat", cursor="hand2", padx=12, pady=6,
                  command=self._browse).pack(side="right")

        # Options
        opts = tk.Frame(f, bg=BG_PANEL, padx=20, pady=15)
        opts.pack(fill="x", padx=25, pady=20)
        tk.Label(opts, text="Additional Options",
                 font=("Segoe UI", 10, "bold"), bg=BG_PANEL, fg=FG_WHITE
                 ).pack(anchor="w", pady=(0, 8))
        for var, txt in [(self.add_startup, "Start RansomGuard automatically at system boot"),
                         (self.add_shortcut, "Create desktop shortcut")]:
            tk.Checkbutton(opts, text=txt, variable=var,
                           font=("Segoe UI", 10), bg=BG_PANEL, fg=FG_GRAY,
                           activebackground=BG_PANEL, selectcolor=BG_DARK,
                           cursor="hand2").pack(anchor="w", pady=2)

        # Disk space note
        tk.Label(f, text="Disk space required: ~45 MB",
                 font=("Segoe UI", 9), bg=BG_DARK, fg=FG_GRAY
                 ).pack(padx=25, anchor="w")

    def _step_installing(self):
        f = self.content
        tk.Label(f, text="Installing RansomGuard…",
                 font=("Segoe UI", 14, "bold"), bg=BG_DARK, fg=FG_WHITE
                 ).pack(pady=(40, 5), padx=25, anchor="w")

        self.install_status = tk.StringVar(value="Preparing…")
        tk.Label(f, textvariable=self.install_status,
                 font=("Segoe UI", 10), bg=BG_DARK, fg=FG_GRAY
                 ).pack(padx=25, anchor="w", pady=(0, 15))

        self.progress = ttk.Progressbar(f, length=400, mode="determinate")
        self.progress.pack(padx=25, pady=5)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TProgressbar", troughcolor=BG_PANEL,
                        background=ACCENT, thickness=8)

        self.install_log = tk.Text(f, font=("Consolas", 8), bg=BG_PANEL,
                                   fg=FG_GRAY, relief="flat", height=10,
                                   state="disabled")
        self.install_log.pack(fill="both", expand=True, padx=25, pady=10)

    def _step_finish(self):
        f = self.content
        tk.Label(f, text="✅", font=("Segoe UI", 48),
                 bg=BG_DARK, fg=FG_GREEN).pack(pady=(40, 10))
        tk.Label(f, text="Installation Complete!",
                 font=("Segoe UI", 18, "bold"), bg=BG_DARK, fg=FG_WHITE
                 ).pack()
        tk.Label(f,
                 text=(f"{APP_NAME} has been installed successfully.\n\n"
                       f"Click 'Launch RansomGuard' to activate your license\n"
                       f"and start protecting your system."),
                 font=("Segoe UI", 10), bg=BG_DARK, fg=FG_GRAY,
                 justify="center"
                 ).pack(pady=20)

    # ────────────────────────────────────────────
    # INSTALL LOGIC
    # ────────────────────────────────────────────

    def _browse(self):
        d = filedialog.askdirectory(initialdir=r"C:\Program Files")
        if d:
            self.install_path.set(os.path.join(d, "RansomGuard"))

    def _log_install(self, msg: str):
        self.install_log.config(state="normal")
        self.install_log.insert("end", msg + "\n")
        self.install_log.see("end")
        self.install_log.config(state="disabled")
        self.root.update_idletasks()

    def _run_install(self):
        def install():
            steps = [
                (10, "Creating installation directory…",      self._do_mkdir),
                (30, "Copying application files…",            self._do_copy_files),
                (55, "Registering application…",              self._do_register),
                (70, "Configuring startup…",                   self._do_startup),
                (85, "Creating shortcuts…",                    self._do_shortcut),
                (95, "Finalising…",                            self._do_finalise),
                (100, "Installation complete.",                lambda: None),
            ]
            for pct, msg, fn in steps:
                self.install_status.set(msg)
                self._log_install(f"  [{pct:>3}%]  {msg}")
                self.progress["value"] = pct
                self.root.update_idletasks()
                try:
                    fn()
                except Exception as e:
                    self._log_install(f"         ⚠ Warning: {e}")
                import time; time.sleep(0.4)

            self.btn_next.config(state="normal")
            self._show_step(4)

        threading.Thread(target=install, daemon=True).start()

    def _do_mkdir(self):
        os.makedirs(self.install_path.get(), exist_ok=True)

    def _do_copy_files(self):
        src = os.path.dirname(os.path.abspath(__file__))
        dst = self.install_path.get()
        for f in os.listdir(src):
            if f.endswith(".py") or f in ("requirements.txt", "README.md"):
                shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
                self._log_install(f"           Copied: {f}")

    def _do_register(self):
        # Write uninstall registry key (Windows)
        try:
            import winreg
            key = winreg.CreateKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\RansomGuard"
            )
            winreg.SetValueEx(key, "DisplayName",        0, winreg.REG_SZ, "RansomGuard")
            winreg.SetValueEx(key, "DisplayVersion",     0, winreg.REG_SZ, VERSION)
            winreg.SetValueEx(key, "InstallLocation",    0, winreg.REG_SZ, self.install_path.get())
            winreg.SetValueEx(key, "Publisher",          0, winreg.REG_SZ, "RansomGuard Security")
            winreg.SetValueEx(key, "UninstallString",    0, winreg.REG_SZ,
                              os.path.join(self.install_path.get(), "uninstall.exe"))
            winreg.CloseKey(key)
        except Exception:
            pass  # Non-Windows or no admin

    def _do_startup(self):
        if not self.add_startup.get():
            return
        try:
            import winreg
            exe = os.path.join(self.install_path.get(), "RansomGuard.exe")
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                0, winreg.KEY_SET_VALUE
            )
            winreg.SetValueEx(key, "RansomGuard", 0, winreg.REG_SZ, f'"{exe}"')
            winreg.CloseKey(key)
        except Exception:
            pass

    def _do_shortcut(self):
        if not self.add_shortcut.get():
            return
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        shortcut = os.path.join(desktop, "RansomGuard.lnk")
        try:
            import win32com.client
            shell = win32com.client.Dispatch("WScript.Shell")
            sc = shell.CreateShortCut(shortcut)
            sc.TargetPath = os.path.join(self.install_path.get(), "RansomGuard.exe")
            sc.WorkingDirectory = self.install_path.get()
            sc.Description = "RansomGuard Early Warning System"
            sc.save()
        except Exception:
            pass

    def _do_finalise(self):
        config = {
            "install_path": self.install_path.get(),
            "version":      VERSION,
            "installed_at": __import__("datetime").datetime.now().isoformat(),
            "startup":      self.add_startup.get(),
        }
        cfg_dir = r"C:\ProgramData\RansomGuard"
        os.makedirs(cfg_dir, exist_ok=True)
        with open(os.path.join(cfg_dir, "install.json"), "w") as f:
            json.dump(config, f, indent=2)

    def _launch_app(self):
        self.root.destroy()
        # Launch activation screen, then main app
        from activation_gui import ActivationWindow
        from license_manager import is_activated
        if not is_activated():
            ActivationWindow(on_success=_launch_main).run()
        else:
            _launch_main()

    def run(self):
        self.root.mainloop()


def _launch_main():
    import subprocess, sys
    install_cfg = r"C:\ProgramData\RansomGuard\install.json"
    if os.path.exists(install_cfg):
        with open(install_cfg) as f:
            cfg = json.load(f)
        exe = os.path.join(cfg["install_path"], "RansomGuard.exe")
    else:
        exe = sys.executable
    subprocess.Popen([exe], creationflags=0x00000008)  # DETACHED_PROCESS


if __name__ == "__main__":
    InstallerWizard().run()
