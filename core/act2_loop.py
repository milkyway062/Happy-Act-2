"""
Act 2 Strategy — New Team
--------------------------
Two phases:
  run_act2_evac()  — called right after act2_position, before bomb_phase
    1. Place 4× Dot (slot 4, Weakest targeting)
    2. Place 4× Weather (slot 5)
    3. Upgrade Nami to MAX
    4. Wave 10: upgrade Dots to lvl 3
    5. Wave 14: place Ainz (slot 1) + upgrade to lvl 3 + Water 2 spell

  run_act2()       — called after bomb_phase (boss phase active)
    1. Place Ainz (slot 1) at wave 14 + upgrade to lvl 3
    2. TODO: Pink Villain Boss Phase Nami action
    3. Ainz caloric stone → summon Teacher at AINZ_POS_1
    5. Place Ichigo (slot 2) + Closest targeting
    6. Set Teacher targeting to Closest
    7. Place Sakura (slot 3)
    8. Sakura corruption on Ainz then Ichigo
    9. Sell Sakura
"""

import json
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
from AnimeVangaurdsLibrary.tools.av_ability import ainz_abiliy, base_ability
from AnimeVangaurdsLibrary.tools.av_game import read_wave
from AnimeVangaurdsLibrary.tools.av_unit import close_unit, place_unit, select_unit, sell_unit

with open(os.path.join(_BASE, "config", "act2_positions.json")) as _f:
    _cfg = json.load(_f)

def _xy(k: str) -> tuple[int, int]:
    return (_cfg[k]["x"], _cfg[k]["y"])

def _up(k: str) -> int:
    return _cfg[k]["upgrades"]

AINZ_POS_1 = _xy("ainz_pos_1")
AINZ_POS_2 = _xy("ainz_pos_2")
ICHIGO_POS = _xy("ichigo")
SAKURA_POS = _xy("sakura")
DOT_1, DOT_2, DOT_3, DOT_4 = _xy("dot_1"), _xy("dot_2"), _xy("dot_3"), _xy("dot_4")
WEATHER_1, WEATHER_2, WEATHER_3, WEATHER_4 = (
    _xy("weather_1"), _xy("weather_2"), _xy("weather_3"), _xy("weather_4")
)
NAMI_POS = _xy("nami")


def run_act2_evac(
    stop_event: threading.Event | None = None,
    log_cb=print,
) -> None:
    """Place evac units right after positioning, before bomb phase."""
    def stopped() -> bool:
        return stop_event is not None and stop_event.is_set()

    dot_positions = [DOT_1, DOT_2, DOT_3, DOT_4]
    for i, pos in enumerate(dot_positions, 1):
        if stopped():
            return
        log_cb(f"Act 2 evac: placing Dot {i}")
        place_unit(4, pos, auto_upgrade=False, close_unit=False)
        for _ in range(4):
            r_input.PressKey("r", 0.1)
        close_unit()

    weather_positions = [WEATHER_1, WEATHER_2, WEATHER_3, WEATHER_4]
    for i, pos in enumerate(weather_positions, 1):
        if stopped():
            return
        log_cb(f"Act 2 evac: placing Weather {i}")
        place_unit(5, pos, auto_upgrade=False, close_unit=True)

    if stopped():
        return

    log_cb("Act 2 evac: upgrading Nami to MAX")
    select_unit(NAMI_POS)
    r_input.PressKey("z", 0.1)
    close_unit()

    log_cb("Act 2 evac: waiting for wave 10 to upgrade Dots")
    while not stopped() and read_wave() < 10:
        time.sleep(0.5)
    if stopped():
        return
    log_cb("Act 2 evac: upgrading Dots 1-3 to lvl 3")
    for i, pos in enumerate([DOT_1, DOT_2, DOT_3], 1):
        if stopped():
            return
        log_cb(f"Act 2 evac: upgrading Dot {i}")
        select_unit(pos)
        for _ in range(_up("dot_1")):
            r_input.PressKey("t", 0.15)
        close_unit()

    log_cb("Act 2 evac: waiting for wave 14 to place Ainz")
    while not stopped() and read_wave() < 14:
        time.sleep(0.5)
    if stopped():
        return
    log_cb("Act 2 evac: placing Ainz (pre-bomb)")
    place_unit(1, AINZ_POS_1, auto_upgrade=False, close_unit=False)
    for _ in range(_up("ainz_pos_1")):
        r_input.PressKey("t", 0.15)

    log_cb("Act 2 evac: Ainz Water 2 spell")
    ainz_abiliy("spells", ("wa2",))
    close_unit()

    log_cb("Act 2 evac: complete")


def run_act2(
    caloric_unit: str = "(Final",
    stop_event: threading.Event | None = None,
    log_cb=print,
) -> None:
    """Boss-phase unit sequence. Called after bomb_phase exits."""
    def stopped() -> bool:
        return stop_event is not None and stop_event.is_set()

    log_cb("Act 2 boss: waiting for wave 14 to place Ainz")
    while not stopped() and read_wave() < 14:
        time.sleep(0.5)
    if stopped():
        return

    log_cb("Act 2 boss: placing Ainz (post-bomb)")
    place_unit(1, AINZ_POS_2, auto_upgrade=False, close_unit=False)
    for _ in range(_up("ainz_pos_2")):
        r_input.PressKey("t", 0.15)
    if stopped():
        return

    # TODO: Pink Villain Boss Phase — Nami targeting action TBD
    # log_cb("Act 2 boss: Nami Pink Villain Boss Phase (TBD)")

    log_cb(f"Act 2 boss: caloric stone ({caloric_unit})")
    ainz_abiliy("worlditem", ("cs", caloric_unit, AINZ_POS_1))
    if stopped():
        return

    log_cb("Act 2 boss: placing Ichigo (Closest)")
    place_unit(2, ICHIGO_POS, auto_upgrade=False, close_unit=False)
    for _ in range(2):
        r_input.PressKey("r", 0.1)
    close_unit()
    if stopped():
        return

    log_cb("Act 2 boss: setting Teacher targeting to Closest")
    select_unit(AINZ_POS_1)
    for _ in range(2):
        r_input.PressKey("r", 0.1)
    close_unit()
    if stopped():
        return

    log_cb("Act 2 boss: placing Sakura")
    place_unit(3, SAKURA_POS, auto_upgrade=False, close_unit=False)
    if stopped():
        return

    log_cb("Act 2 boss: Sakura corruption (Ainz then Ichigo)")
    base_ability()
    r_input.Click(*AINZ_POS_2, 0.2)
    r_input.Click(*SAKURA_POS, 0.2)
    close_unit()
    base_ability()
    r_input.Click(*ICHIGO_POS, 0.2)
    r_input.Click(*SAKURA_POS, 0.2)
    sell_unit(SAKURA_POS)

    log_cb("Act 2: complete")
