"""
Position Setup
--------------
Runs the full pre-detection setup sequence:
  1. Camera reset (zoom in, look down, zoom out)
  2. Burn slots 2-6 via Prideburn (keep slot 1)
  3. Vote start
  4. Place Escanor (slot 1)
  5. Spectate → left arrow → close
  6. Zoom out
  7. TP-to-spawn loop until RightSpot.png is in the expected region
  8. Backup zoom out
  9. Wait for wave 1, then restart match

Run standalone: py core/position_setup.py
"""

import ctypes
import os
import sys
import time

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (
    os.path.join(_BASE, "rblib", "src"),
    os.path.join(_BASE, "avlib"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from rblib import r_input, r_util
from rblib.r_client import focus_roblox_window
from AnimeVangaurdsLibrary.tools.av_ability import prideburn
from AnimeVangaurdsLibrary.tools.av_game import read_wave, restart_match, return_to_spawn, start
from AnimeVangaurdsLibrary.tools.av_unit import place_unit, use_team

# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
RIGHTSPOT_IMAGE   = os.path.join(_BASE, "Images", "RightSpot.png")
RIGHTSPOT_REGION  = (214, 156, 196, 115)  # x, y, w, h  (was x1,y1,x2,y2)
ESCANOR_MATCH_POS = (364, 159)   # match/detection reference coord
ESCANOR_POS       = (408, 333)   # placement coord used during positioning
SPECTATE_POS      = (156, 248)
LEFT_ARROW_POS    = (334, 545)
CLOSE_POS         = (408, 610)
Close_Unit_BTN    = (306, 234)


def setup_position(act1_team: int = 1, log_cb=print) -> None:
    log_cb("Positioning: aligning Roblox window")
    focus_roblox_window()

    log_cb("Positioning: moving leftover UI out of the way")
    from act2_position import _drag
    _drag(527, 215, 701, 132)

    log_cb("Positioning: TP to spawn")
    return_to_spawn()
    time.sleep(1.5)

    log_cb("Positioning: camera reset")
    r_input.PressKey("i", 1)
    ctypes.windll.user32.mouse_event(0x0001, 0, 100000, 0, 0)
    time.sleep(0.2)
    r_input.PressKey("o", 2)

    log_cb("Positioning: closing chat")
    r_input.Click(161, 65, 0.1)
    r_input.Click(161, 65, 0.1)

    log_cb(f"Positioning: switching to Act 1 team {act1_team}")
    use_team(act1_team)

    log_cb("Positioning: burning slots 2-6")
    prideburn(1)

    log_cb("Positioning: voting start")
    start()

    log_cb("Positioning: placing Escanor")
    r_input.KeyDown("w")
    time.sleep(0.5)
    r_input.KeyUp("w")
    place_unit(1, ESCANOR_POS, close_unit=False)

    log_cb("Positioning: spectating → finding spawn view")
    r_input.Click(*SPECTATE_POS, 0.5)
    r_input.Click(*LEFT_ARROW_POS, 0.5)
    r_input.Click(*CLOSE_POS, 0.8)
    r_input.Click(*Close_Unit_BTN, 0.2)
    r_input.Click(*Close_Unit_BTN, 0.1)
    r_input.PressKey("o", 2)

    time.sleep(1.5)
    tp_count = 0
    while not r_util.imageExists(RIGHTSPOT_IMAGE, 0.8, region=RIGHTSPOT_REGION):
        tp_count += 1
        log_cb(f"Positioning: TP to spawn (attempt {tp_count})")
        return_to_spawn()
        time.sleep(2)
    log_cb("Positioning: spawn view confirmed")

    r_input.PressKey("o", 2)

    log_cb("Positioning: waiting for wave 1...")
    while read_wave() < 1:
        time.sleep(0.5)

    log_cb("Positioning: restarting match")
    restart_match()
    log_cb("Positioning complete")


if __name__ == "__main__":
    setup_position()
