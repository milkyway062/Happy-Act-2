"""
Wave Code Detector
------------------
Wave tracking: counts appearances of the wave pop-up banner (1 appearance = 1 wave).
Code detection: scans for the Pink Villain boss after each wave starts.
Boss present = current wave number is a code digit.

No OCR needed — both detections are pure template matching.

Setup:
  1. Save the wave pop-up banner to  Images/WavePopup.png
  2. Save the Pink Villain boss to    Images/PinkVillain.png
  3. Run: py Tools/wave_code_detector.py
"""

import os
import sys
import time

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
from position_setup import setup_position

# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------
WAVE_POPUP_IMAGE   = os.path.join(_BASE, "Images", "WavePopup.png")
BOSS_IMAGE         = os.path.join(_BASE, "Images", "PinkVillain.png")
WAVE_THRESHOLD     = 0.85   # confidence for wave pop-up detection
BOSS_THRESHOLD     = 0.85   # confidence for boss detection
WAVE_POPUP_REGION  = (377, 479, 426, 507)  # (x1, y1, x2, y2) window-relative


class WaveCodeDetector:
    """
    Counts wave pop-up appearances to track wave number (1–9).
    After each new wave, scans for the Pink Villain boss.
    Boss found → append current wave number to code.

    State machine for pop-up counting:
      - Pop-up not visible → visible : wave_count += 1
      - Pop-up visible → not visible : ready for next wave
    This prevents a single pop-up from being counted multiple times.
    """

    def __init__(
        self,
        wave_popup_image: str = WAVE_POPUP_IMAGE,
        boss_image: str = BOSS_IMAGE,
        wave_threshold: float = WAVE_THRESHOLD,
        boss_threshold: float = BOSS_THRESHOLD,
        wave_popup_region: tuple[int, int, int, int] | None = WAVE_POPUP_REGION,
    ) -> None:
        self.wave_threshold = wave_threshold
        self.boss_threshold = boss_threshold
        self.wave_popup_region = wave_popup_region
        self._wave_template: np.ndarray | None = None
        self._boss_template: np.ndarray | None = None
        self._load_template(wave_popup_image, "_wave_template", "wave pop-up")
        self._load_template(boss_image, "_boss_template", "boss")

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _load_template(self, path: str, attr: str, label: str) -> None:
        raw = cv2.imread(path)
        if raw is None:
            print(f"  WARNING: {label} image not found at {path}")
            return
        setattr(self, attr, cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY))
        print(f"  {label} template loaded OK")

    # ------------------------------------------------------------------
    # Screen capture
    # ------------------------------------------------------------------

    def _capture_gray(self, region: tuple[int, int, int, int] | None = None) -> np.ndarray:
        rect = get_geometry(get_roblox_hwnd())
        if region is not None:
            x1, y1, x2, y2 = region
            capture_rect = (rect.x + x1, rect.y + y1, rect.x + x2, rect.y + y2)
        else:
            capture_rect = (rect.x, rect.y, rect.x + rect.w, rect.y + rect.h)
        raw = r_util.captureRegion(capture_rect)
        return cv2.cvtColor(raw, cv2.COLOR_BGR2GRAY)

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def _match(
        self,
        template: np.ndarray | None,
        threshold: float,
        region: tuple[int, int, int, int] | None = None,
    ) -> tuple[bool, float]:
        """Template match against a region (or full window). Returns (found, confidence)."""
        if template is None:
            return False, 0.0
        screen = self._capture_gray(region)
        th, tw = template.shape[:2]
        if screen.shape[0] < th or screen.shape[1] < tw:
            return False, 0.0
        res = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(res)
        return float(max_val) >= threshold, float(max_val)

    def wave_popup_visible(self) -> tuple[bool, float]:
        return self._match(self._wave_template, self.wave_threshold, self.wave_popup_region)

    def boss_on_screen(self) -> tuple[bool, float]:
        return self._match(self._boss_template, self.boss_threshold)

    def count_bosses(self) -> int:
        """Count how many boss instances are visible via NMS. Returns 0, 1, or 2."""
        if self._boss_template is None:
            return 0
        screen = self._capture_gray()
        th, tw = self._boss_template.shape[:2]
        if screen.shape[0] < th or screen.shape[1] < tw:
            return 0
        res = cv2.matchTemplate(screen, self._boss_template, cv2.TM_CCOEFF_NORMED)
        locs = list(zip(*np.where(res >= self.boss_threshold)))
        if not locs:
            return 0
        # NMS: suppress hits within one template-width of a stronger hit
        hits = sorted(locs, key=lambda p: res[p[0], p[1]], reverse=True)
        kept: list[tuple[int, int]] = []
        for y, x in hits:
            if all(abs(y - ky) > th or abs(x - kx) > tw for ky, kx in kept):
                kept.append((y, x))
        return len(kept)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def build_code(self) -> str:
        """
        Count wave pop-up appearances (1 per wave, waves 1–9).
        After each new wave, scan for boss. Boss found → code += wave_number.
        Auto-fill 9 if 3 digits collected by end of wave 8.
        """
        code = ""
        wave = 0
        popup_was_visible = False
        print("\n=== Wave code detection started ===\n")
        print("Waiting for wave pop-up...\n")

        while len(code) < 4:
            visible, conf = self.wave_popup_visible()

            # Rising edge: pop-up just appeared → new wave
            if visible and not popup_was_visible:
                wave += 1
                popup_was_visible = True
                print(f"\n--- Wave {wave}  (popup conf={conf:.3f}) ---")
                time.sleep(0.6)

                found_boss = False
                for attempt in range(10):
                    count = self.count_bosses()
                    if count >= 1:
                        digit = str(wave) * min(count, 2)
                        code += digit
                        print(f"  Boss x{count} → digit(s)={digit!r}  code={code!r}")
                        found_boss = True
                        break
                    print(f"  [scan {attempt+1}/10] no boss")
                    time.sleep(0.2)

                if not found_boss:
                    print(f"  No boss on wave {wave}")

            # Falling edge: pop-up gone → ready for next wave
            elif not visible and popup_was_visible:
                popup_was_visible = False

            # Auto-fill: 3 digits by end of wave 8 → append 9
            if wave == 8 and not visible and len(code) == 3:
                code += "9"
                print(f"\n  Auto-filled 9 → {code!r}")

            if wave == 9 and not visible and len(code) < 4:
                print("\nWARNING: wave 9 passed without full code — no more code waves")
                break

            time.sleep(0.05)

        print(f"\n=== Final code: {code} ===")
        return code


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

if __name__ == "__main__":
    detector = WaveCodeDetector(
        wave_popup_image=WAVE_POPUP_IMAGE,
        boss_image=BOSS_IMAGE,
    )
    setup_position()
    result = detector.build_code()
    print(f"\nDone. Code = {result}")
