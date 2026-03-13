# 🛡️ RANSOMGUARD — Lightweight AI Early Warning System

> Ransomware detection for Small & Medium Enterprises (SMEs)  
> Python · Windows · Event-driven · No content scanning

---

## Architecture Overview

```
File System Events (watchdog)
        │
        ▼
  FileMonitor                ← renames, modifications, creates, deletes
        │
        ▼
BehaviorAnalyzer             ← sliding 60s window counters per signal type
        │   (every 5 seconds)
        ▼
 DecisionEngine              ← threshold rules + co-occurrence AI amplifier
        │
        ▼
ResponseManager              ← alert popup │ process kill │ secure backup
        │
        ▼
  EventLogger                ← JSONL forensic log + human-readable log
```

---

## Files

| File | Purpose |
|------|---------|
| `config.py` | All thresholds, paths, weights — tune here |
| `rg_logger.py` | Structured logging (file + console + JSONL) |
| `file_monitor.py` | Watchdog-based event-driven file watcher |
| `behavior_analyzer.py` | Sliding window stats + AI risk scoring |
| `decision_engine.py` | Threat level evaluation (CLEAR/WARN/ALERT/ISOLATE) |
| `response_manager.py` | Alert popup, process termination, network block |
| `backup_manager.py` | Timestamped, hidden, permission-restricted backups |
| `ransomguard_main.py` | Main orchestrator + Windows Service wrapper |
| `simulator.py` | Safe ransomware behaviour simulator for testing |
| `requirements.txt` | Python dependencies |

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure watch paths
Edit `config.py` → `WATCH_PATHS` to include your critical directories.

For testing with the simulator, add the sim dir:
```python
WATCH_PATHS = [
    r"C:\temp\rg_sim_files",   # simulator output
    os.path.expanduser("~\\Documents"),
    ...
]
```

### 3. Run in foreground
```bash
python ransomguard_main.py
```

### 4. Install as Windows Service (requires admin)
```bash
python ransomguard_main.py --install
python ransomguard_main.py start
```

### 5. Run the simulator (separate terminal)
```bash
# Mild attack — should trigger WARN/ALERT
python simulator.py --mode mixed --intensity mild

# Aggressive attack — should trigger ISOLATE
python simulator.py --mode mixed --intensity high

# Clean up test files
python simulator.py --cleanup
```

---

## AI Risk Scoring

The Behavior Analysis Engine assigns a **risk score (0–100)** using weighted signals:

| Signal | Weight | Trigger |
|--------|--------|---------|
| Rapid renames | 30 | > 10 renames/min |
| Bulk modifications | 25 | > 20 mods/min |
| Extension changes | 20 | > 5 ext changes/min |
| Suspicious prefixes | 15 | `locked_`, `encrypted_`, etc. |
| Bulk file access | 10 | > 50 reads/min by one process |

**Co-occurrence amplifier** (AI layer): when multiple signals fire simultaneously,
the score is multiplied by a confidence factor:

```
2 signals → ×1.3
3 signals → ×1.6
4 signals → ×1.9
5 signals → ×2.2 (cap)
```

This means a ransomware attack triggering *all* signals simultaneously scores
much higher than any single signal alone — reducing false positives from
legitimate batch operations.

### Threat Levels

| Score | Level | Response |
|-------|-------|---------|
| 0–39 | CLEAR | Monitor only |
| 40–64 | WARN | Log + first-time notice |
| 65–84 | ALERT | Popup + backup snapshot |
| 85–100 | ISOLATE | Popup + kill process + backup |

---

## Tuning for Your SME

All thresholds are in `config.py → THRESHOLDS`.

**High-volume file servers** → increase thresholds to reduce false positives:
```python
"rename_per_minute": 25,
"modifications_per_minute": 50,
```

**Sensitive environments** (medical, legal) → lower thresholds:
```python
"rename_per_minute": 5,
"risk_score_alert": 50,
```

---

## Backup Locations

Backups are stored in `C:\RansomGuard_Backup\<timestamp>\` with:
- `attrib +H +S` (hidden + system)
- `icacls` deny-delete for standard users
- Max size guard (default 500 MB)

---

## Performance

- **CPU**: Event-driven (no polling). Analysis every 5 seconds.
- **RAM**: Typically < 50 MB (well within 150 MB target).
- **Disk I/O**: Metadata-only monitoring. No content scanning.

---

## Future Roadmap

- [ ] ML anomaly detection (Isolation Forest on behaviour vectors)
- [ ] Cloud backup (AWS S3 / Google Drive)
- [ ] External drive backup
- [ ] Web dashboard (real-time risk gauge)
- [ ] Admin portal with encrypted config
- [ ] Licence key system
- [ ] SOC webhook integration

---

## ⚠️ Disclaimer

RANSOMGUARD is a prototype early-warning system, not a full antivirus solution.
It is designed to detect behavioural patterns early — it does **not** guarantee
prevention of data loss. Always maintain regular offsite backups.
