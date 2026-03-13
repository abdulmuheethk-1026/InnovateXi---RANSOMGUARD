"""
RANSOMGUARD – License Activation Window
Shown on first launch if no valid license is found.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
import webbrowser

from app.license_manager import activate, get_license_status

# ── Assets / branding ──────────────────────────────
APP_NAME    = "RansomGuard"
VERSION     = "1.0.0"
ACCENT      = "#E84545"     # red
BG_DARK     = "#1A1A2E"
BG_PANEL    = "#16213E"
FG_WHITE    = "#EAEAEA"
FG_GRAY     = "#8892A4"
FG_GREEN    = "#2ECC71"
FONT_TITLE  = ("Segoe UI", 22, "bold")
FONT_SUB    = ("Segoe UI", 10)
FONT_LABEL  = ("Segoe UI", 10, "bold")
FONT_ENTRY  = ("Consolas", 13)
FONT_BTN    = ("Segoe UI", 10, "bold")


class ActivationWindow:
    def __init__(self, on_success=None):
        self.on_success = on_success
        self.root = tk.Tk()
        self._build()

    def _build(self):
        r = self.root
        r.title(f"{APP_NAME} – License Activation")
        r.geometry("580x520")
        r.resizable(False, False)
        r.configure(bg=BG_DARK)
        r.eval("tk::PlaceWindow . center")
 
        # ── Header ────────────────────────────────────
        header = tk.Frame(r, bg=ACCENT, height=6)
        header.pack(fill="x")

        logo_frame = tk.Frame(r, bg=BG_DARK, pady=30)
        logo_frame.pack(fill="x")

        tk.Label(logo_frame, text="🛡️", font=("Segoe UI", 36),
                 bg=BG_DARK, fg=ACCENT).pack()
        tk.Label(logo_frame, text=APP_NAME, font=FONT_TITLE,
                 bg=BG_DARK, fg=FG_WHITE).pack()
        tk.Label(logo_frame, text=f"Early Warning System  v{VERSION}",
                 font=FONT_SUB, bg=BG_DARK, fg=FG_GRAY).pack()

        # ── Panel ─────────────────────────────────────
        panel = tk.Frame(r, bg=BG_PANEL, padx=40, pady=30)
        panel.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        tk.Label(panel, text="Enter Your License Key",
                 font=FONT_LABEL, bg=BG_PANEL, fg=FG_WHITE).pack(anchor="w")
        tk.Label(panel,
                 text="Your license key was provided in your purchase confirmation email.",
                 font=FONT_SUB, bg=BG_PANEL, fg=FG_GRAY, wraplength=480, justify="left"
                 ).pack(anchor="w", pady=(2, 16))

        # Key entry with live formatting
        self.key_var = tk.StringVar()
        self.key_var.trace("w", self._format_key)

        entry_frame = tk.Frame(panel, bg=ACCENT, padx=2, pady=2)
        entry_frame.pack(fill="x")
        self.key_entry = tk.Entry(
            entry_frame, textvariable=self.key_var,
            font=FONT_ENTRY, bg="#0F3460", fg=FG_WHITE,
            insertbackground=FG_WHITE, relief="flat",
            justify="center"
        )
        self.key_entry.pack(fill="x", ipady=10)
        self.key_entry.insert(0, "RG-XXXX-XXXX-XXXX-XXXX")
        self.key_entry.bind("<FocusIn>", self._clear_placeholder)

        # Status label
        self.status_var = tk.StringVar(value="")
        self.status_lbl = tk.Label(panel, textvariable=self.status_var,
                                   font=FONT_SUB, bg=BG_PANEL, fg=FG_GRAY)
        self.status_lbl.pack(pady=(8, 0))

        # Activate button
        self.btn = tk.Button(
            panel, text="Activate RansomGuard",
            font=FONT_BTN, bg=ACCENT, fg="white",
            activebackground="#C0392B", activeforeground="white",
            relief="flat", cursor="hand2", pady=10,
            command=self._on_activate
        )
        self.btn.pack(fill="x", pady=(16, 0))

        # Trial note
        tk.Label(panel,
                 text="Using a trial key? Enter:  RG-EVAL-FREE-TRIAL-30D",
                 font=("Segoe UI", 9), bg=BG_PANEL, fg=FG_GRAY
                 ).pack(pady=(12, 0))

        # Footer
        footer = tk.Frame(r, bg=BG_DARK)
        footer.pack(fill="x", padx=30, pady=(0, 15))
        tk.Label(footer, text="Need a key? ", font=FONT_SUB,
                 bg=BG_DARK, fg=FG_GRAY).pack(side="left")
        link = tk.Label(footer, text="Purchase at ransomguard.io",
                        font=FONT_SUB, bg=BG_DARK, fg=ACCENT, cursor="hand2")
        link.pack(side="left")
        link.bind("<Button-1>", lambda e: webbrowser.open("https://ransomguard.io"))

    def _clear_placeholder(self, event):
        if self.key_var.get() == "RG-XXXX-XXXX-XXXX-XXXX":
            self.key_entry.delete(0, "end")

    def _format_key(self, *_):
        """Allow typing including '-' but keep format RG-XXXX-XXXX-XXXX-XXXX"""
        value = self.key_var.get().upper()

        # Allow only letters, numbers, and dash
        filtered = "".join(c for c in value if c.isalnum() or c == "-")

        if filtered != value:
            self.key_var.set(filtered)
            self.key_entry.icursor("end")

    def _on_activate(self):
        key = self.key_var.get().strip()
        self.btn.config(state="disabled", text="Activating…")
        self.root.update()

        success, msg = activate(key)

        if success:
            self.status_var.set("✅ " + msg.split("\n")[0])
            self.status_lbl.config(fg=FG_GREEN)
            self.root.after(1500, self._close_success)
        else:
            self.status_var.set("❌ " + msg)
            self.status_lbl.config(fg=ACCENT)
            self.btn.config(state="normal", text="Activate RansomGuard")

    def _close_success(self):
        self.root.destroy()
        if self.on_success:
            self.on_success()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    ActivationWindow().run()
