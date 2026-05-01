"""
Bomb Phase
----------
Waits for bomb phase to begin (yellow pixel at 407,734),
spams E+Q each second, clicks (678,521) when BombPhase banner
is visible, then exits when BossPhase banner appears.
"""

import os
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

from rblib import r_input, r_util

BOMB_IMAGE     = os.path.join(_BASE, "Images", "BombPhase.png")
BOSS_IMAGE     = os.path.join(_BASE, "Images", "BossPhase.png")
BOMB_REGION    = (657, 186, 759, 215)
BOSS_REGION    = (658, 187, 753, 213)


def run_bomb_phase(
    stop_event: threading.Event | None = None,
    log_cb=print,
) -> None:
    def stopped() -> bool:
        return stop_event is not None and stop_event.is_set()

    log_cb("Bomb phase: waiting for bomb phase banner")
    while not stopped():
        if r_util.imageExists(BOMB_IMAGE, 0.85, region=BOMB_REGION):
            break
        time.sleep(0.2)

    if stopped():
        return

    log_cb("Bomb phase: spamming Q+E until boss phase")
    while not stopped():
        if r_util.imageExists(BOSS_IMAGE, 0.85, region=BOSS_REGION):
            log_cb("Bomb phase: boss phase detected — exiting")
            break

        r_input.PressKey("q", 0.05)
        r_input.PressKey("e", 0.05)
        time.sleep(0.9)
