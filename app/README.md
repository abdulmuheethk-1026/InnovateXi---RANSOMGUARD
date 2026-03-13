# 🛡️ RANSOMGUARD — Lightweight AI Early Warning System
### Windows Desktop Application · v1.0.0

> Ransomware early detection for Small & Medium Enterprises  
> Installs like any Windows app — License key activation included

---

## What's New in This Version

| Added | Description |
|-------|-------------|
| `license_manager.py` | Key validation, activation, expiry, tamper detection |
| `activation_gui.py` | Professional license key entry screen |
| `installer_wizard.py` | Full multi-step install wizard with Terms & Conditions |
| `tray_app.py` | System tray app + live dashboard |
| `build.py` | PyInstaller build script → produces `RansomGuard.exe` |
| `RansomGuard_Setup.iss` | Inno Setup script → produces `RansomGuard_Setup_v1.0.0.exe` |

---

## User Journey (End to End)

```
1. User visits ransomguard.io → downloads RansomGuard_Setup_v1.0.0.exe
         ↓
2. Runs installer → sees multi-step wizard:
   • Welcome screen
   • Terms & Conditions (must accept to proceed)
   • Choose install location  +  startup / shortcut options
   • Progress bar install
   • Finish screen
         ↓
3. App launches → License Activation screen appears
   • Enters key:  RG-XXXX-XXXX-XXXX-XXXX
   • Key validated → "Activated Successfully"
         ↓
4. RansomGuard starts in system tray (shield icon, bottom-right)
   • Double-click → opens Dashboard
   • Background monitoring begins immediately
         ↓
5. If attack detected → popup alert, backup created, process killed
```

---

## Prototype License Keys (for testing)

| Key | Tier | Duration |
|-----|------|----------|
| `RG-EVAL-FREE-TRIAL-30D` | Trial | 30 days |
| `RG-PROT-O1AB-2024-DEMO` | Prototype | 365 days |
| `RG-SME1-AAAA-BBBB-CCCC` | SME Basic | 365 days |
| `RG-SME2-1111-2222-3333` | SME Pro | 2 years |

---

## All Files

| File | Purpose |
|------|---------|
| `config.py` | Thresholds, paths, weights |
| `rg_logger.py` | File + console + JSONL logging |
| `file_monitor.py` | Watchdog file system watcher |
| `behavior_analyzer.py` | Sliding window stats + AI risk scoring |
| `decision_engine.py` | CLEAR / WARN / ALERT / ISOLATE |
| `response_manager.py` | Alert popup, process kill, firewall block |
| `backup_manager.py` | Hidden timestamped backup snapshots |
| `ransomguard_main.py` | Core agent orchestrator |
| `license_manager.py` | Key validation, activation, tamper protection |
| `activation_gui.py` | License key entry UI |
| `installer_wizard.py` | Install wizard (Welcome → T&C → Path → Install → Finish) |
| `tray_app.py` | System tray + live dashboard |
| `build.py` | Builds RansomGuard.exe via PyInstaller |
| `RansomGuard_Setup.iss` | Inno Setup script → distributable installer |
| `simulator.py` | Safe ransomware behaviour simulator |
| `requirements.txt` | Python dependencies |

---

## Build Instructions (Developers)

### Step 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### Step 2 — Build the .exe
```bash
python build.py
# Output: dist/RansomGuard/RansomGuard.exe
```

### Step 3 — Build the installer (requires Inno Setup 6)
Download from: https://jrsoftware.org/isinfo.php
```bash
python build.py --installer
# Output: Output/RansomGuard_Setup_v1.0.0.exe
```

---

## Running Without Building (Dev Mode)

```bash
python tray_app.py          # full app (activation + tray + guard)
python activation_gui.py    # activation screen only
python installer_wizard.py  # install wizard only
python ransomguard_main.py  # core guard only
python simulator.py --mode mixed --intensity high   # attack sim
```

---

## AI Risk Scoring

| Signal | Weight | Threshold |
|--------|--------|-----------|
| Rapid renames | 30 pts | > 10/min |
| Bulk modifications | 25 pts | > 20/min |
| Extension changes | 20 pts | > 5/min |
| Suspicious prefixes | 15 pts | any `locked_`, `encrypted_` |
| Bulk file access | 10 pts | > 50/min |

Co-occurrence amplifier: 2 signals → ×1.3 · 3 → ×1.6 · 4 → ×1.9 · 5 → ×2.2

| Score | Level | Response |
|-------|-------|---------|
| 0–39 | CLEAR | Monitor |
| 40–64 | WARN | Log |
| 65–84 | ALERT | Popup + backup |
| 85–100 | ISOLATE | Popup + kill + backup |

---

## Roadmap

- [ ] ML anomaly detection (Isolation Forest)
- [ ] Cloud backup (AWS S3 / Google Drive)
- [ ] Server-side license validation
- [ ] Auto-update mechanism
- [ ] Web dashboard

---

© 2024 RansomGuard Security. Prototype version.
