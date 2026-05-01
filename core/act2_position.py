"""
Act 2 Position Setup
--------------------
Runs after the Act 1 code is submitted.
Sequence:
  1. Wait for Change Lineup button (or 12 s timeout)
  2. Dismiss unneeded UI (click + drag)
  3. Switch to Act 2 team
  4. Camera reset (zoom in, look down, zoom out)
  5. Vote start
  6. Place Nami (slot 6) at positioning spot
  7. Spectate -> left arrow -> close -> close unit btn -> zoom out
  8. TP-to-spawn loop until RightSpot2 is in expected region
  9. Sell Nami, mount, D 3 s, unmount, right-click, re-place Nami, upgrade lvl 1
"""

import ctypes
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
from rblib.r_client import get_geometry, get_roblox_hwnd
from AnimeVangaurdsLibrary.tools.av_game import return_to_spawn, start
from AnimeVangaurdsLibrary.tools.av_unit import close_unit, place_unit, select_unit, use_team

RIGHTSPOT2_IMAGE  = os.path.join(_BASE, "Images", "RightSpot2.png")
RIGHTSPOT2_REGION = (257, 158, 399, 397)
LINEUP_IMAGE      = os.path.join(_BASE, "Images", "ChangeLineup.png")

NAMI_POS_1     = (407, 337)   # initial positioning spot (same as old Tempest pos)
NAMI_POS_2     = (536, 236)   # final spot after D 3s walk

SPECTATE_POS   = (156, 248)
LEFT_ARROW_POS = (334, 545)
CLOSE_POS      = (408, 610)
CLOSE_UNIT_BTN = (306, 234)
POST_MOVE_RC   = (408, 524)   # right-click after D 3s walk


def _drag(x1: int, y1: int, x2: int, y2: int) -> None:
    win = get_geometry(get_roblox_hwnd())
    extra = ctypes.c_ulong(0)

    r_input.MoveTo(x1 + win.x, y1 + win.y)
    time.sleep(0.1)

    _iu = r_input.InputUnion()
    _iu.mi = r_input.MouseInput(0, 0, 0, r_input.MOUSEEVENTF_LEFTDOWN, 0, ctypes.pointer(extra))
    inp = r_input.Input(ctypes.c_ulong(r_input.INPUT_MOUSE), _iu)
    r_input.SendInput(1, ctypes.pointer(inp), ctypes.sizeof(inp))
    time.sleep(0.1)

    r_input.MoveTo(x2 + win.x, y2 + win.y)
    time.sleep(0.1)

    _iu.mi = r_input.MouseInput(0, 0, 0, r_input.MOUSEEVENTF_LEFTUP, 0, ctypes.pointer(extra))
    inp = r_input.Input(ctypes.c_ulong(r_input.INPUT_MOUSE), _iu)
    r_input.SendInput(1, ctypes.pointer(inp), ctypes.sizeof(inp))


def _right_click(x: int, y: int) -> None:
    win = get_geometry(get_roblox_hwnd())
    extra = ctypes.c_ulong(0)
    r_input.MoveTo(x + win.x, y + win.y)
    time.sleep(0.1)
    _iu = r_input.InputUnion()
    _iu.mi = r_input.MouseInput(0, 0, 0, 0x0008, 0, ctypes.pointer(extra))  # MOUSEEVENTF_RIGHTDOWN
    inp = r_input.Input(ctypes.c_ulong(r_input.INPUT_MOUSE), _iu)
    r_input.SendInput(1, ctypes.pointer(inp), ctypes.sizeof(inp))
    time.sleep(0.05)
    _iu.mi = r_input.MouseInput(0, 0, 0, 0x0010, 0, ctypes.pointer(extra))  # MOUSEEVENTF_RIGHTUP
    inp = r_input.Input(ctypes.c_ulong(r_input.INPUT_MOUSE), _iu)
    r_input.SendInput(1, ctypes.pointer(inp), ctypes.sizeof(inp))


def setup_act2_position(
    act2_team: int = 2,
    stop_event: threading.Event | None = None,
    log_cb=print,
) -> None:
    def stopped() -> bool:
        return stop_event is not None and stop_event.is_set()

    log_cb("Act 2 pos: waiting for Change Lineup button")
    deadline = time.time() + 12
    while time.time() < deadline:
        if stopped():
            return
        if os.path.exists(LINEUP_IMAGE) and r_util.imageExists(LINEUP_IMAGE, 0.8):
            break
        time.sleep(0.5)

    if stopped():
        return

    log_cb("Act 2 pos: moving UI out of the way")
    _drag(527, 215, 701, 132)

    if stopped():
        return

    log_cb(f"Act 2 pos: switching to team {act2_team}")
    use_team(act2_team)

    if stopped():
        return

    log_cb("Act 2 pos: camera reset")
    r_input.PressKey("i", 1)
    ctypes.windll.user32.mouse_event(0x0001, 0, 100000, 0, 0)
    time.sleep(0.2)
    r_input.PressKey("o", 2)

    if stopped():
        return

    log_cb("Act 2 pos: vote start")
    start()

    if stopped():
        return

    log_cb("Act 2 pos: placing Nami (positioning)")
    place_unit(6, NAMI_POS_1, auto_upgrade=False, close_unit=False)

    if stopped():
        return

    log_cb("Act 2 pos: spectate sequence")
    r_input.Click(*SPECTATE_POS, 0.5)
    r_input.Click(*LEFT_ARROW_POS, 0.5)
    r_input.Click(*CLOSE_POS, 0.8)
    r_input.Click(*CLOSE_UNIT_BTN, 0.2)
    r_input.Click(*CLOSE_UNIT_BTN, 0.1)
    r_input.PressKey("o", 2)

    if stopped():
        return

    time.sleep(1.5)
    tp_count = 0
    while not r_util.imageExists(RIGHTSPOT2_IMAGE, 0.8, region=RIGHTSPOT2_REGION):
        if stopped():
            return
        tp_count += 1
        log_cb(f"Act 2 pos: TP to spawn (attempt {tp_count})")
        return_to_spawn()
        time.sleep(2)
    log_cb("Act 2 pos: spawn view confirmed")

    if stopped():
        return

    log_cb("Act 2 pos: mounting and moving to spot (deleting Nami)")
    r_input.PressKey("v", 0.5)
    _d_start = time.time()
    r_input.KeyDown("d")
    r_input.PressKey("f")
    time.sleep(0.5)
    r_input.Click(622, 249, 0.1)
    r_input.PressKey("f")
    _elapsed = time.time() - _d_start
    if 3.0 - _elapsed > 0:
        time.sleep(3.0 - _elapsed)
    r_input.KeyUp("d")
    r_input.PressKey("v", 0.5)

    time.sleep(1.0)
    _right_click(*POST_MOVE_RC)
    time.sleep(2.0)

    if stopped():
        return

    log_cb("Act 2 pos: re-placing Nami at final spot")
    place_unit(6, NAMI_POS_2, auto_upgrade=False, close_unit=False)

    if stopped():
        return

    log_cb("Act 2 pos: upgrading Nami to lvl 1")
    r_input.PressKey("t", 0.15)
    close_unit()

    log_cb("Act 2 pos: complete")
