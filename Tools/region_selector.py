"""
Region Selector
---------------
Captures the Roblox window, displays it, and lets you drag-select a region.
Outputs window-relative coordinates ready to paste into wave_code_detector.py.

Controls:
  Drag     - draw selection rectangle
  ENTER / SPACE - confirm selection
  C        - cancel / redraw
  ESC      - quit without selecting
"""

import os
import sys

import cv2
import numpy as np

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (
    os.path.join(_BASE, "rblib", "src"),
    os.path.join(_BASE, "avlib"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from rblib import r_util
from rblib.r_client import get_geometry, get_roblox_hwnd


def _capture_window() -> np.ndarray:
    rect = get_geometry(get_roblox_hwnd())
    return r_util.captureRegion(
        (rect.x, rect.y, rect.x + rect.w, rect.y + rect.h)
    )


def _draw_crosshair(img: np.ndarray, x: int, y: int) -> np.ndarray:
    out = img.copy()
    cv2.line(out, (x, 0), (x, out.shape[0]), (0, 255, 0), 1)
    cv2.line(out, (0, y), (out.shape[1], y), (0, 255, 0), 1)
    cv2.putText(
        out,
        f"({x}, {y})",
        (x + 8, y - 8 if y > 20 else y + 16),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.45,
        (0, 255, 0),
        1,
        cv2.LINE_AA,
    )
    return out


def select_region(label: str = "region") -> tuple[int, int, int, int] | None:
    """
    Show the Roblox window and let the user drag-select a region.
    Returns (x1, y1, x2, y2) relative to the Roblox window, or None on cancel.
    """
    print(f"\nCapturing Roblox window for '{label}' selection...")
    screenshot = _capture_window()

    # Scale up small windows so the selector is easier to use
    scale = 1
    h, w = screenshot.shape[:2]
    if w < 500:
        scale = 2

    display = cv2.resize(screenshot, (w * scale, h * scale), interpolation=cv2.INTER_NEAREST)

    win_name = f"Select '{label}'  |  Drag rect  |  ENTER=confirm  C=redo  ESC=cancel"
    print(f"Window opened. Drag a rectangle around the '{label}' region.")
    print("  ENTER / SPACE = confirm    C = cancel / redraw    ESC = quit\n")

    roi = cv2.selectROI(win_name, display, fromCenter=False, showCrosshair=True)
    cv2.destroyAllWindows()

    if roi == (0, 0, 0, 0):
        print("No region selected.")
        return None

    # Convert back to original scale (window-relative)
    rx, ry, rw, rh = (int(v // scale) for v in roi)
    x1, y1 = rx, ry
    x2, y2 = rx + rw, ry + rh

    print(f"\n=== '{label}' region (window-relative) ===")
    print(f"  x1={x1}, y1={y1}, x2={x2}, y2={y2}")
    print(f"  width={x2 - x1}px, height={y2 - y1}px")
    print(f"\nPaste into wave_code_detector.py:")
    print(f"  WAVE_REGION = ({x1}, {y1}, {x2}, {y2})")

    return (x1, y1, x2, y2)


def preview_region(region: tuple[int, int, int, int], label: str = "region") -> None:
    """Show a zoomed preview of the selected region for verification."""
    x1, y1, x2, y2 = region
    screenshot = _capture_window()
    crop = screenshot[y1:y2, x1:x2]
    if crop.size == 0:
        print("Region is empty — check coordinates.")
        return

    # Zoom in so small regions (like the wave counter) are visible
    zoom = max(1, 200 // max(crop.shape[:2]))
    zoomed = cv2.resize(
        crop,
        (crop.shape[1] * zoom, crop.shape[0] * zoom),
        interpolation=cv2.INTER_NEAREST,
    )
    win_name = f"Preview: '{label}' ({x2-x1}x{y2-y1}px zoomed {zoom}x)  |  any key to close"
    cv2.imshow(win_name, zoomed)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    regions: dict[str, tuple[int, int, int, int]] = {}

    print("=== Region Selector ===")
    print("Select one or more regions. Results are window-relative coordinates.\n")

    labels = sys.argv[1:] if len(sys.argv) > 1 else ["wave_region", "code_region"]

    for lbl in labels:
        input(f"Press ENTER when ready to select '{lbl}'...")
        result = select_region(lbl)
        if result:
            regions[lbl] = result
            preview_region(result, lbl)

    if regions:
        print("\n=== All selected regions ===")
        for name, coords in regions.items():
            print(f"  {name}: {coords}")
        print("\nCopy these into wave_code_detector.py as WAVE_REGION / CODE_REGION constants.")
