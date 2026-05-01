"""
Act 1 Main Loop
---------------
Sequence:
  1. Auto-position (setup_position)
  2. Burn slots 2-6, dismiss cancel popup
  3. Place Escanor
  4. Wave code detection
  5. (After code input, TP to act 2 — handled externally)

Run standalone: py Tools/act1_loop.py
"""

import os
import sys

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (
    os.path.join(_BASE, "rblib", "src"),
    os.path.join(_BASE, "avlib"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from rblib import r_input
from AnimeVangaurdsLibrary.tools.av_ability import prideburn
from AnimeVangaurdsLibrary.tools.av_unit import place_unit

from position_setup import CANCEL_BTN, ESCANOR_POS, setup_position
from wave_code_detector import WaveCodeDetector


def run_act1() -> str:
    setup_position()

    prideburn(1)
    r_input.Click(*CANCEL_BTN, 0.1)
    place_unit(1, ESCANOR_POS, close_unit=True, auto_upgrade=True)

    detector = WaveCodeDetector()
    code = detector.build_code()
    print(f"\nAct 1 code: {code}")
    return code


if __name__ == "__main__":
    run_act1()
