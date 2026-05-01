"""
Movement Sequence Tuner
-----------------------
Build and test the WASD movement sequence used to reach the code-input NPC.
Edits are made in memory; use 's' to save back to settings.json.

Controls:
  a <key> <secs>       - append step         e.g.  a w 1.5
  i <idx> <key> <secs> - insert before index  e.g.  i 0 s 0.8
  e <idx> <secs>       - edit step duration   e.g.  e 2 2.5
  d <idx>              - delete step           e.g.  d 1
  u <idx>              - move step up          e.g.  u 2
  x <idx>              - move step down        e.g.  x 0
  t                    - test sequence in-game (3 s countdown)
  s                    - save to settings.json
  r                    - reload from settings.json (discard changes)
  q                    - quit
"""

import json
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

from rblib import r_input

SETTINGS_PATH = os.path.join(
    _BASE, "avlib", "AnimeVangaurdsLibrary", "settings.json"
)

VALID_KEYS = {"w", "a", "s", "d", "q", "e"}


def load_settings() -> dict:
    with open(SETTINGS_PATH, "r") as f:
        return json.load(f)


def save_settings(data: dict) -> None:
    with open(SETTINGS_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print("  Saved.")


def print_sequence(seq: list) -> None:
    if not seq:
        print("  (empty)")
        return
    total = sum(d for _, d in seq)
    for i, (key, dur) in enumerate(seq):
        print(f"  [{i}]  {key.upper()}  {dur:.2f}s")
    print(f"  total: {total:.2f}s")


def run_sequence(seq: list) -> None:
    if not seq:
        print("  Sequence is empty — nothing to run.")
        return
    print("  Running in 3...")
    time.sleep(1)
    print("  2...")
    time.sleep(1)
    print("  1...")
    time.sleep(1)
    print("  GO")
    for key, duration in seq:
        r_input.KeyDown(key)
        time.sleep(duration)
        r_input.KeyUp(key)
    print("  Done.")


def parse_duration(raw: str) -> float | None:
    try:
        v = float(raw)
        if v <= 0:
            print("  Duration must be > 0")
            return None
        return v
    except ValueError:
        print(f"  Bad duration: {raw!r}")
        return None


def parse_key(raw: str) -> str | None:
    k = raw.lower()
    if k not in VALID_KEYS:
        print(f"  Unknown key {raw!r}. Valid: {', '.join(sorted(VALID_KEYS))}")
        return None
    return k


def parse_index(raw: str, seq: list) -> int | None:
    try:
        idx = int(raw)
        if not (0 <= idx < len(seq)):
            print(f"  Index {idx} out of range (0–{len(seq)-1})")
            return None
        return idx
    except ValueError:
        print(f"  Bad index: {raw!r}")
        return None


def main() -> None:
    data = load_settings()
    seq: list = [list(step) for step in data["avcs"]["movement_sequence"]]
    dirty = False

    print(__doc__)
    print(f"Settings: {SETTINGS_PATH}\n")

    while True:
        print("\nCurrent sequence:")
        print_sequence(seq)
        print()

        try:
            raw = input("cmd> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not raw:
            continue

        parts = raw.split()
        cmd = parts[0].lower()

        if cmd == "q":
            if dirty:
                ans = input("  Unsaved changes. Save before quitting? [y/n] ").strip().lower()
                if ans == "y":
                    data["avcs"]["movement_sequence"] = seq
                    save_settings(data)
            break

        elif cmd == "s":
            data["avcs"]["movement_sequence"] = seq
            save_settings(data)
            dirty = False

        elif cmd == "r":
            data = load_settings()
            seq = [list(step) for step in data["avcs"]["movement_sequence"]]
            dirty = False
            print("  Reloaded.")

        elif cmd == "t":
            run_sequence(seq)

        elif cmd == "a":
            if len(parts) != 3:
                print("  Usage: a <key> <secs>")
                continue
            key = parse_key(parts[1])
            dur = parse_duration(parts[2])
            if key and dur:
                seq.append([key, dur])
                dirty = True

        elif cmd == "i":
            if len(parts) != 4:
                print("  Usage: i <idx> <key> <secs>")
                continue
            if not seq and parts[1] == "0":
                idx = 0
            else:
                idx = parse_index(parts[1], seq)
                if idx is None:
                    continue
            key = parse_key(parts[2])
            dur = parse_duration(parts[3])
            if key and dur:
                seq.insert(idx, [key, dur])
                dirty = True

        elif cmd == "e":
            if len(parts) != 3:
                print("  Usage: e <idx> <secs>")
                continue
            idx = parse_index(parts[1], seq)
            dur = parse_duration(parts[2])
            if idx is not None and dur:
                seq[idx][1] = dur
                dirty = True

        elif cmd == "d":
            if len(parts) != 2:
                print("  Usage: d <idx>")
                continue
            idx = parse_index(parts[1], seq)
            if idx is not None:
                removed = seq.pop(idx)
                print(f"  Removed [{idx}] {removed[0].upper()} {removed[1]:.2f}s")
                dirty = True

        elif cmd == "u":
            if len(parts) != 2:
                print("  Usage: u <idx>")
                continue
            idx = parse_index(parts[1], seq)
            if idx is not None:
                if idx == 0:
                    print("  Already at top.")
                else:
                    seq[idx - 1], seq[idx] = seq[idx], seq[idx - 1]
                    dirty = True

        elif cmd == "x":
            if len(parts) != 2:
                print("  Usage: x <idx>")
                continue
            idx = parse_index(parts[1], seq)
            if idx is not None:
                if idx == len(seq) - 1:
                    print("  Already at bottom.")
                else:
                    seq[idx], seq[idx + 1] = seq[idx + 1], seq[idx]
                    dirty = True

        else:
            print(f"  Unknown command: {cmd!r}")

    print("Bye.")


if __name__ == "__main__":
    main()
