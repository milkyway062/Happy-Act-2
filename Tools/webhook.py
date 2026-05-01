import io
import json
import os
from datetime import datetime

import requests
from PIL import ImageGrab

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SETTINGS = os.path.join(_BASE, "config", "settings.json")


def _webhook_url() -> str:
    with open(_SETTINGS) as f:
        return json.load(f).get("webhook_url", "")


def _screenshot() -> io.BytesIO:
    img = ImageGrab.grab()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def send(wins: int, losses: int, run_time: str = "") -> None:
    url = _webhook_url()
    if not url:
        return

    total = wins + losses
    ratio = f"{(wins / total * 100):.1f}%" if total else "N/A"

    payload = {
        "username": "Happy Macro",
        "embeds": [
            {
                "title": "Happy Macro — Run Update",
                "color": 3447003,
                "fields": [
                    {"name": "⚔️ Wins",         "value": str(wins),    "inline": True},
                    {"name": "💀 Losses",        "value": str(losses),  "inline": True},
                    {"name": "📈 Win Rate",      "value": ratio,        "inline": True},
                    {"name": "🔁 Total Runs",    "value": str(total),   "inline": True},
                    {"name": "🕒 Run Time",      "value": run_time or "—", "inline": True},
                ],
                "image": {"url": "attachment://screenshot.png"},
                "footer": {"text": f"Happy Macro | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"},
                "timestamp": datetime.utcnow().isoformat(),
            }
        ],
    }

    try:
        requests.post(
            url,
            data={"payload_json": json.dumps(payload)},
            files={"file": ("screenshot.png", _screenshot(), "image/png")},
            timeout=10,
        )
    except Exception as e:
        print(f"Webhook error: {e}")
