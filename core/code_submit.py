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

from rblib import r_input
from AnimeVangaurdsLibrary import Game_Settings


def submit_code(
    code: str,
    stop_event: threading.Event | None = None,
    log_cb=print,
) -> None:
    cfg = Game_Settings.avcs

    def stopped() -> bool:
        return stop_event is not None and stop_event.is_set()

    log_cb(f"Code submit: mounting (key={cfg.mount_key})")
    r_input.PressKey(cfg.mount_key, cfg.mount_delay)
    if stopped():
        return

    log_cb("Code submit: moving to location")
    for key, duration in cfg.movement_sequence:
        if stopped():
            return
        r_input.KeyDown(key)
        time.sleep(duration)
        r_input.KeyUp(key)

    if stopped():
        return

    log_cb("Code submit: opening UI (holding E)")
    time.sleep(cfg.hold_e_delay)
    r_input.KeyDown("e")
    time.sleep(cfg.hold_e_duration)
    r_input.KeyUp("e")

    if stopped():
        return

    log_cb(f"Code submit: entering code {code}")
    for digit in code:
        if stopped():
            return
        x, y = cfg.digit_buttons[digit]
        r_input.Click(x, y, cfg.digit_click_delay)

    if stopped():
        return

    cx, cy = cfg.confirm_button
    r_input.Click(cx, cy, cfg.confirm_delay)
    log_cb("Code submit: done")
