"""
Act 1 Main Loop
---------------
Sequence:
  1. Auto-position (setup_position)
  2. Burn slots 2-6, dismiss cancel popup
  3. Vote start
  4. Place Escanor with auto-upgrade
  5. Wave code detection
  6. (After code input, TP to act 2 — handled externally)

Run standalone: py core/act1_loop.py
"""

import os
import sys
import time
import threading

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (
    os.path.join(_BASE, "rblib", "src"),
    os.path.join(_BASE, "avlib"),
    os.path.join(_BASE, "core"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from rblib import r_input
from AnimeVangaurdsLibrary.tools.av_ability import prideburn
from AnimeVangaurdsLibrary.tools.av_game import start
from AnimeVangaurdsLibrary.tools.av_unit import place_unit

from position_setup import setup_position
from code_submit import submit_code
import macro_state

CANCEL_BTN = (408, 372)
from wave_code_detector import WaveCodeDetector

ESC_POS = (358, 165)


def run_act1(act1_team: int = 1, act2_team: int = 2, caloric_unit: str = "", stop_event: threading.Event | None = None, log_cb=print, code_cb=None) -> tuple[str, bool | None]:
    def stopped() -> bool:
        return stop_event is not None and stop_event.is_set()

    victory: bool | None = None
    macro_state.state["run_start"] = time.time()

    setup_position(act1_team=act1_team, log_cb=log_cb)
    if stopped(): return "", None

    log_cb("Act 1: burning slots 2-6")
    prideburn(1)
    if stopped(): return "", None

    r_input.Click(*CANCEL_BTN, 0.1)
    if stopped(): return "", None

    from rejoin import wait_for_vote_start
    log_cb("Act 1: waiting for Vote Start (section 3 — back from act 2)")
    wait_for_vote_start(stop_event=stop_event, log_cb=log_cb)
    if stopped(): return "", None

    log_cb("Act 1: voting start")
    start()
    if stopped(): return "", None

    log_cb("Act 1: placing Escanor (auto-upgrade on)")
    place_unit(1, ESC_POS, auto_upgrade=True, close_unit=True)
    if stopped(): return "", None

    log_cb("Act 1: starting wave code detection")
    detector = WaveCodeDetector()
    code = detector.build_code(stop_event=stop_event, log_cb=log_cb, code_cb=code_cb)

    if code and not stopped():
        log_cb(f"Act 1: code={code}, submitting")
        submit_code(code, stop_event=stop_event, log_cb=log_cb)

    if not stopped():
        log_cb("Act 2: positioning")
        from act2_position import setup_act2_position
        setup_act2_position(act2_team, stop_event=stop_event, log_cb=log_cb)

    if not stopped():
        log_cb("Act 2: waiting for Vote Start (section 2 — entering act 2)")
        wait_for_vote_start(stop_event=stop_event, log_cb=log_cb)

    if not stopped():
        log_cb("Act 2 evac: placing units")
        from act2_loop import run_act2_evac
        run_act2_evac(stop_event=stop_event, log_cb=log_cb)

    if not stopped():
        log_cb("Bomb phase: starting")
        from bomb_phase import run_bomb_phase
        run_bomb_phase(stop_event=stop_event, log_cb=log_cb)

    if not stopped():
        from act2_loop import run_act2
        run_act2(caloric_unit, stop_event=stop_event, log_cb=log_cb)

    if not stopped():
        log_cb("End screen: waiting for match to end")
        from AnimeVangaurdsLibrary.tools.av_game import wait_for_end, retry
        from rblib import r_util
        victory = wait_for_end()
        macro_state.state["last_run_time"] = time.time() - macro_state.state["run_start"]
        log_cb(f"End screen: {'victory' if victory else 'defeat'} — clicking retry")
        retry()
        log_cb("End screen: waiting for Change Lineup button")
        _LINEUP_IMG = os.path.join(_BASE, "Images", "ChangeLineup.png")
        while not stopped():
            if os.path.exists(_LINEUP_IMG) and r_util.imageExists(_LINEUP_IMG, 0.8):
                break
            time.sleep(0.5)

    return code, victory


if __name__ == "__main__":
    run_act1()
