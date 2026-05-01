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

Run standalone: py Tools/position_setup.py
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
from AnimeVangaurdsLibrary.tools.av_ability import prideburn
from AnimeVangaurdsLibrary.tools.av_game import read_wave, restart_match, return_to_spawn, start
from AnimeVangaurdsLibrary.tools.av_unit import place_unit

# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
RIGHTSPOT_IMAGE   = os.path.join(_BASE, "Images", "RightSpot.png")
RIGHTSPOT_REGION  = (214, 156, 410, 271)
ESCANOR_MATCH_POS = (364, 159)   # match/detection reference coord
ESCANOR_POS       = (408, 333)   # placement coord used during positioning
SPECTATE_POS      = (156, 248)
LEFT_ARROW_POS    = (334, 545)
CLOSE_POS         = (408, 610)
CANCEL_BTN        = (408, 372)


def setup_position() -> None:
    print("\n=== Auto-positioning started ===\n")

    # 1-3. Camera reset
    r_input.PressKey("i", 1)
    ctypes.windll.user32.mouse_event(0x0001, 0, 100000, 0, 0)
    time.sleep(0.2)
    r_input.PressKey("o", 2)

    # 4-9. Burn slots 2-6, keep slot 1 (Escanor)
    prideburn(1)

    # 10. Vote start
    start()

    # 11. Place Escanor from hotbar slot 1
    place_unit(1, ESCANOR_POS, close_unit=True)

    # 12-15. Spectate → left arrow → close → zoom out
    r_input.Click(*SPECTATE_POS, 0.1)
    r_input.Click(*LEFT_ARROW_POS, 0.1)
    r_input.Click(*CLOSE_POS, 0.1)
    r_input.PressKey("o", 2)

    # 16. TP-to-spawn loop until camera is in the right spot
    print("  Waiting for correct camera position...")
    r_input.Click(*CANCEL_BTN, 0.1)
    time.sleep(1.5)
    while not r_util.imageExists(RIGHTSPOT_IMAGE, 0.8, region=RIGHTSPOT_REGION):
        return_to_spawn()
        time.sleep(2)
    print("  Position confirmed.")

    # 17. Backup zoom out
    r_input.PressKey("o", 2)

    # 18. Wait for wave 1 before restarting (can't restart on wave 0)
    print("  Waiting for wave 1...")
    while read_wave() < 1:
        time.sleep(0.5)

    restart_match()
    print("=== Positioning complete ===\n")


if __name__ == "__main__":
    setup_position()
