import logging
import os
import subprocess
import sys
import time
import threading

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (
    os.path.join(_BASE, "rblib", "src"),
    os.path.join(_BASE, "avlib"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import macro_state

logger = logging.getLogger(__name__)

AV_PLACE_ID    = 16146832113
REJOIN_TIMEOUT = 120

_HAPPY_STAGE = 4
_HAPPY_ACT   = 1

_AREA_ICON = os.path.join(
    _BASE, "avlib", "AnimeVangaurdsLibrary", "tools", "resources", "AreaIcon.png"
)
_VOTE_START_IMG = os.path.join(_BASE, "Images", "vote_start.png")


def wait_for_vote_start(
    stop_event: threading.Event | None = None,
    log_cb=print,
    timeout: float = 120,
) -> bool:
    """Block until Vote Start button is visible. Returns False if stopped or timed out."""
    def stopped():
        return stop_event is not None and stop_event.is_set()

    log_cb("Waiting for Vote Start…")
    deadline = time.time() + timeout
    while time.time() < deadline:
        if stopped():
            return False
        try:
            from rblib import r_util
            if r_util.imageExists(_VOTE_START_IMG, 0.7):
                log_cb("Vote Start detected — game loaded")
                return True
        except Exception:
            pass
        time.sleep(0.5)

    log_cb("Vote Start wait timed out")
    return False


def is_in_lobby() -> bool:
    """Return True if the AreaIcon (lobby hub) is currently visible on screen."""
    try:
        from rblib import r_util
        return r_util.imageExists(_AREA_ICON, 0.75)
    except Exception:
        return False


def extract_ps_code(value: str) -> str:
    from urllib.parse import urlparse, parse_qs
    parsed = urlparse(value)
    qs = parse_qs(parsed.query)
    if "privateServerLinkCode" in qs:
        return qs["privateServerLinkCode"][0]
    return value.strip()


def _roblox_exe() -> str | None:
    try:
        import psutil
        for proc in psutil.process_iter(["name", "exe"]):
            try:
                if "robloxplayerbeta" in proc.name().lower():
                    return proc.exe()
            except Exception:
                pass
    except Exception:
        pass
    return None


def do_rejoin(
    stop_event: threading.Event | None = None,
    log_cb=print,
) -> bool:
    """Kill Roblox, relaunch into private server, wait for game to load."""
    def stopped():
        return stop_event is not None and stop_event.is_set()

    ps_code = extract_ps_code(macro_state.PRIVATE_SERVER_CODE)
    if not ps_code:
        log_cb("Rejoin: no private server code set — skipping")
        return False

    exe = _roblox_exe()
    if not exe:
        log_cb("Rejoin: RobloxPlayerBeta.exe not found")
        return False

    log_cb("Rejoin: killing Roblox processes")
    try:
        import psutil
        for proc in psutil.process_iter(["name"]):
            try:
                if "roblox" in proc.name().lower():
                    proc.kill()
            except Exception:
                pass
    except Exception as e:
        log_cb(f"Rejoin: kill error: {e}")

    time.sleep(2)
    if stopped():
        return False

    url = f"roblox://placeId={AV_PLACE_ID}&linkCode={ps_code}/"
    log_cb(f"Rejoin: launching {url}")
    subprocess.Popen([exe, url])

    log_cb("Rejoin: waiting for Roblox to load")
    deadline = time.time() + REJOIN_TIMEOUT
    while time.time() < deadline:
        if stopped():
            return False
        try:
            import pygetwindow
            wins = [w for w in pygetwindow.getAllWindows() if w.title == "Roblox"]
            if wins:
                log_cb("Rejoin: Roblox window detected — waiting 12s for game to load")
                time.sleep(12)
                return True
        except Exception:
            pass
        time.sleep(2)

    log_cb("Rejoin: timed out waiting for Roblox window")
    return False


_DAILY_REWARDS_CLOSE = (654, 187)
_LEADERBOARD_CLOSE   = (642, 115)


def _daily_rewards_visible() -> bool:
    try:
        from rblib import r_util
        return r_util.pixelMatchesColor(*_DAILY_REWARDS_CLOSE, (255, 255, 255), 5)
    except Exception:
        return False


def _close_lobby_ui(log_cb=print) -> None:
    """Dismiss daily rewards popup and leaderboard before pathing."""
    from rblib import r_input
    if _daily_rewards_visible():
        log_cb("Lobby: closing daily rewards")
        r_input.Click(*_DAILY_REWARDS_CLOSE, 0.3)
    log_cb("Lobby: closing leaderboard")
    r_input.Click(*_LEADERBOARD_CLOSE, 0.3)


def do_lobby_path(
    stop_event: threading.Event | None = None,
    log_cb=print,
) -> None:
    from AnimeVangaurdsLibrary.tools.av_game import lobby_path, Areas
    _close_lobby_ui(log_cb=log_cb)
    log_cb(f"Lobby path: navigating to Happy Raid Act 1 (Stage {_HAPPY_STAGE})")
    lobby_path(Areas.RAID, _HAPPY_STAGE, _HAPPY_ACT)
    wait_for_vote_start(stop_event=stop_event, log_cb=log_cb)
