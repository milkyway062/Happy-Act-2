"""
Pixel Check
-----------
Captures the full screen and highlights an absolute screen coordinate.
Shows the pixel location with a crosshair and prints its current color.

Usage:
  py Tools/pixel_check.py 407 734
  py Tools/pixel_check.py          (defaults to 407, 734)

Controls:
  Any key / click - close
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

import ctypes
import cv2
import numpy as np
from rblib import r_util


def _screen_size():
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    return user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)


def main():
    px = int(sys.argv[1]) if len(sys.argv) > 1 else 407
    py = int(sys.argv[2]) if len(sys.argv) > 2 else 734

    sw, sh = _screen_size()
    img = r_util.captureRegion((0, 0, sw, sh))

    color_bgr = img[py, px].tolist()
    color_hex = "#{:02X}{:02X}{:02X}".format(color_bgr[2], color_bgr[1], color_bgr[0])
    print(f"Pixel ({px}, {py})  BGR={color_bgr}  HEX={color_hex}")

    out = img.copy()

    # crosshair
    cv2.line(out, (px, 0), (px, out.shape[0]), (0, 255, 0), 1)
    cv2.line(out, (0, py), (out.shape[1], py), (0, 255, 0), 1)

    # filled dot at pixel
    cv2.circle(out, (px, py), 6, (0, 0, 255), -1)
    cv2.circle(out, (px, py), 6, (255, 255, 255), 1)

    # label
    label = f"({px}, {py})  {color_hex}"
    lx = px + 10 if px < out.shape[1] - 160 else px - 160
    ly = py - 10 if py > 20 else py + 20
    cv2.putText(out, label, (lx, ly),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1, cv2.LINE_AA)

    win = f"Pixel check ({px}, {py})  {color_hex}  |  any key to close"
    cv2.imshow(win, out)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
