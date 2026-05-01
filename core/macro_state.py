import threading

# ── Runtime-mutable settings (written by GUI) ─────────────────────────
PRIVATE_SERVER_CODE    = ""
WEBHOOK_URL            = ""
AUTO_REJOIN_AFTER_RUNS = 0   # 0 = disabled

# ── Shared state dict (read by GUI _tick, written by worker) ──────────
state = {
    "wins":              0,
    "losses":            0,
    "total_runs":        0,
    "runs_since_rejoin": 0,
    "session_start":     0.0,
    "run_start":         0.0,
    "last_run_time":     0.0,
    "running":           False,
}

_lock = threading.Lock()
