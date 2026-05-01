"""
Act 2 Position Editor
---------------------
View and edit unit positions + upgrade counts.
Left: canvas showing where each unit is placed (scaled game area).
Right: form fields for x, y, upgrades per unit.
Click a dot on the canvas to jump to that unit's form row.
"Show Overlay" draws dots directly over the live Roblox window.
"""

import ctypes
import ctypes.wintypes
import json
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_BASE, "rblib", "src"))

CFG_PATH = os.path.join(_BASE, "config", "act2_positions.json")

GAME_W = 760
GAME_H = 560
SCALE  = 0.75
CVS_W  = int(GAME_W * SCALE)
CVS_H  = int(GAME_H * SCALE)
DOT_R  = 7
OVL_R  = 9   # overlay dot radius (larger for on-screen visibility)

TRANSPARENT = "#000001"


def load_cfg() -> dict:
    with open(CFG_PATH) as f:
        return json.load(f)


def save_cfg(cfg: dict) -> None:
    with open(CFG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)


def _get_roblox_rect() -> tuple[int, int, int, int] | None:
    """Return (x, y, w, h) of the Roblox window, or None if not found."""
    user32 = ctypes.windll.user32

    # Try pid-based lookup first (uses rblib)
    hwnd = None
    try:
        from rblib.r_client import get_roblox_hwnd, get_geometry
        hwnd = get_roblox_hwnd()
        if hwnd:
            g = get_geometry(hwnd)
            return g.x, g.y, g.w, g.h
    except Exception:
        pass

    # Fallback: find by window title
    for title in ("Roblox", "Roblox Game Client"):
        hwnd = user32.FindWindowW(None, title)
        if hwnd:
            break

    if not hwnd:
        return None

    rect = ctypes.wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    x, y = rect.left, rect.top
    w, h = rect.right - rect.left, rect.bottom - rect.top
    return x, y, w, h


class Overlay:
    """Transparent topmost window that draws unit dots over Roblox."""

    def __init__(self, cfg: dict, rx: int, ry: int, rw: int, rh: int) -> None:
        self.win = tk.Toplevel()
        self.win.overrideredirect(True)
        self.win.wm_attributes("-topmost", True)
        self.win.wm_attributes("-transparentcolor", TRANSPARENT)
        self.win.geometry(f"{rw}x{rh}+{rx}+{ry}")

        self.canvas = tk.Canvas(self.win, width=rw, height=rh,
                                bg=TRANSPARENT, highlightthickness=0)
        self.canvas.pack()

        self._draw(cfg)

        # Press Escape or click the X chip to close
        self.win.bind("<Escape>", lambda e: self.close())
        self._add_close_btn(rw)

    def _draw(self, cfg: dict) -> None:
        self.canvas.delete("all")
        for unit in cfg.values():
            x, y = unit["x"], unit["y"]
            color = unit.get("color", "#ffffff")
            label = unit["label"]

            # Dot
            self.canvas.create_oval(
                x - OVL_R, y - OVL_R, x + OVL_R, y + OVL_R,
                fill=color, outline="#ffffff", width=2
            )
            # Shadow text then white text for readability
            self.canvas.create_text(x + OVL_R + 2, y + 1, text=label,
                                    anchor="w", fill="#000000",
                                    font=("Segoe UI", 8, "bold"))
            self.canvas.create_text(x + OVL_R + 2, y, text=label,
                                    anchor="w", fill="#ffffff",
                                    font=("Segoe UI", 8, "bold"))

    def _add_close_btn(self, rw: int) -> None:
        btn = tk.Label(self.canvas, text=" ✕ Close Overlay ",
                       bg="#f38ba8", fg="#1e1e2e",
                       font=("Segoe UI", 9, "bold"), cursor="hand2")
        btn.place(x=rw - 130, y=8)
        btn.bind("<Button-1>", lambda e: self.close())

    def close(self) -> None:
        self.win.destroy()


class PositionEditor:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Act 2 Position Editor")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")

        self.cfg = load_cfg()
        self.rows: dict[str, dict] = {}
        self.dot_items: dict[str, int] = {}
        self.selected_key: str | None = None
        self._overlay: Overlay | None = None

        self._build_ui()
        self._draw_canvas()

    def _build_ui(self) -> None:
        outer = tk.Frame(self.root, bg="#1e1e2e")
        outer.pack(padx=10, pady=10, fill="both", expand=True)

        # ── Canvas (left) ──────────────────────────────────────────
        cvs_frame = tk.Frame(outer, bg="#1e1e2e")
        cvs_frame.grid(row=0, column=0, padx=(0, 10), sticky="n")

        tk.Label(cvs_frame, text="Unit Positions", bg="#1e1e2e", fg="#cdd6f4",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 4))

        self.canvas = tk.Canvas(cvs_frame, width=CVS_W, height=CVS_H,
                                bg="#11111b", highlightthickness=1,
                                highlightbackground="#313244")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # ── Form (right) ───────────────────────────────────────────
        form_outer = tk.Frame(outer, bg="#1e1e2e")
        form_outer.grid(row=0, column=1, sticky="ns")

        tk.Label(form_outer, text="Edit Units", bg="#1e1e2e", fg="#cdd6f4",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 4))

        scroll_canvas = tk.Canvas(form_outer, bg="#1e1e2e", highlightthickness=0,
                                  width=300, height=CVS_H)
        scrollbar = ttk.Scrollbar(form_outer, orient="vertical", command=scroll_canvas.yview)
        scroll_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        scroll_canvas.pack(side="left", fill="both", expand=True)

        self.form_frame = tk.Frame(scroll_canvas, bg="#1e1e2e")
        scroll_canvas.create_window((0, 0), window=self.form_frame, anchor="nw")

        self.form_frame.bind("<Configure>", lambda e: scroll_canvas.configure(
            scrollregion=scroll_canvas.bbox("all")))
        self.scroll_canvas = scroll_canvas

        for key, unit in self.cfg.items():
            self._build_row(key, unit)

        # ── Buttons (bottom) ───────────────────────────────────────
        btn_frame = tk.Frame(self.root, bg="#1e1e2e")
        btn_frame.pack(pady=(0, 10))

        tk.Button(btn_frame, text="Save", width=12, command=self._save,
                  bg="#a6e3a1", fg="#1e1e2e", font=("Segoe UI", 10, "bold"),
                  relief="flat", cursor="hand2").pack(side="left", padx=6)

        tk.Button(btn_frame, text="Reload", width=12, command=self._reload,
                  bg="#89b4fa", fg="#1e1e2e", font=("Segoe UI", 10, "bold"),
                  relief="flat", cursor="hand2").pack(side="left", padx=6)

        tk.Button(btn_frame, text="Show Overlay", width=14, command=self._show_overlay,
                  bg="#cba6f7", fg="#1e1e2e", font=("Segoe UI", 10, "bold"),
                  relief="flat", cursor="hand2").pack(side="left", padx=6)

    def _build_row(self, key: str, unit: dict) -> None:
        color = unit.get("color", "#cdd6f4")

        frame = tk.Frame(self.form_frame, bg="#313244", relief="flat", bd=0)
        frame.pack(fill="x", padx=4, pady=4, ipady=4)

        header = tk.Frame(frame, bg="#313244")
        header.pack(fill="x", padx=6, pady=(4, 2))
        tk.Canvas(header, width=12, height=12, bg=color,
                  highlightthickness=0).pack(side="left", padx=(0, 6))
        tk.Label(header, text=unit["label"], bg="#313244", fg="#cdd6f4",
                 font=("Segoe UI", 9, "bold")).pack(side="left")

        fields = tk.Frame(frame, bg="#313244")
        fields.pack(fill="x", padx=6, pady=2)

        x_var = tk.IntVar(value=unit["x"])
        y_var = tk.IntVar(value=unit["y"])
        up_var = tk.IntVar(value=unit["upgrades"])

        for col, (lbl, var) in enumerate([("x", x_var), ("y", y_var), ("upgrades", up_var)]):
            tk.Label(fields, text=lbl, bg="#313244", fg="#a6adc8",
                     font=("Segoe UI", 8)).grid(row=0, column=col * 2, padx=(0, 2), sticky="e")
            if lbl == "upgrades":
                w = tk.Spinbox(fields, from_=0, to=10, textvariable=var, width=4,
                               bg="#1e1e2e", fg="#cdd6f4", insertbackground="#cdd6f4",
                               relief="flat", font=("Segoe UI", 9),
                               command=lambda k=key: self._on_field_change(k))
            else:
                w = tk.Entry(fields, textvariable=var, width=5,
                             bg="#1e1e2e", fg="#cdd6f4", insertbackground="#cdd6f4",
                             relief="flat", font=("Segoe UI", 9))
                w.bind("<KeyRelease>", lambda e, k=key: self._on_field_change(k))
            w.grid(row=0, column=col * 2 + 1, padx=(0, 8))

        self.rows[key] = {"frame": frame, "x": x_var, "y": y_var, "upgrades": up_var}

    def _draw_canvas(self) -> None:
        self.canvas.delete("all")
        self.dot_items.clear()

        for gx in range(0, GAME_W, 100):
            sx = int(gx * SCALE)
            self.canvas.create_line(sx, 0, sx, CVS_H, fill="#1e1e2e", width=1)
        for gy in range(0, GAME_H, 100):
            sy = int(gy * SCALE)
            self.canvas.create_line(0, sy, CVS_W, sy, fill="#1e1e2e", width=1)

        for key, unit in self.cfg.items():
            sx = int(unit["x"] * SCALE)
            sy = int(unit["y"] * SCALE)
            color = unit.get("color", "#cdd6f4")
            is_sel = key == self.selected_key
            outline = "#ffffff" if is_sel else "#000000"
            width = 2 if is_sel else 1

            dot = self.canvas.create_oval(
                sx - DOT_R, sy - DOT_R, sx + DOT_R, sy + DOT_R,
                fill=color, outline=outline, width=width, tags=(key,)
            )
            self.canvas.create_text(sx + DOT_R + 3, sy, text=unit["label"],
                                    anchor="w", fill="#cdd6f4",
                                    font=("Segoe UI", 7), tags=(key,))
            self.dot_items[key] = dot

    def _on_canvas_click(self, event: tk.Event) -> None:
        items = self.canvas.find_overlapping(
            event.x - DOT_R, event.y - DOT_R,
            event.x + DOT_R, event.y + DOT_R
        )
        for item in items:
            for tag in self.canvas.gettags(item):
                if tag in self.rows:
                    self._select(tag)
                    return

    def _select(self, key: str) -> None:
        if self.selected_key and self.selected_key in self.rows:
            self.rows[self.selected_key]["frame"].configure(bg="#313244")
            for child in self.rows[self.selected_key]["frame"].winfo_children():
                _recolor(child, "#313244")

        self.selected_key = key
        self.rows[key]["frame"].configure(bg="#45475a")
        for child in self.rows[key]["frame"].winfo_children():
            _recolor(child, "#45475a")

        self._scroll_to(key)
        self._draw_canvas()

    def _scroll_to(self, key: str) -> None:
        self.form_frame.update_idletasks()
        frame = self.rows[key]["frame"]
        total_h = self.form_frame.winfo_height()
        if total_h == 0:
            return
        self.scroll_canvas.yview_moveto(frame.winfo_y() / total_h)

    def _on_field_change(self, key: str) -> None:
        try:
            self.cfg[key]["x"] = self.rows[key]["x"].get()
            self.cfg[key]["y"] = self.rows[key]["y"].get()
            self.cfg[key]["upgrades"] = self.rows[key]["upgrades"].get()
            self._draw_canvas()
        except tk.TclError:
            pass

    def _save(self) -> None:
        for key, row in self.rows.items():
            try:
                self.cfg[key]["x"] = row["x"].get()
                self.cfg[key]["y"] = row["y"].get()
                self.cfg[key]["upgrades"] = row["upgrades"].get()
            except tk.TclError:
                messagebox.showerror("Error", f"Invalid value in {self.cfg[key]['label']}")
                return
        save_cfg(self.cfg)
        self._draw_canvas()
        messagebox.showinfo("Saved", "Positions saved to act2_positions.json")

    def _reload(self) -> None:
        self.cfg = load_cfg()
        for key, unit in self.cfg.items():
            if key in self.rows:
                self.rows[key]["x"].set(unit["x"])
                self.rows[key]["y"].set(unit["y"])
                self.rows[key]["upgrades"].set(unit["upgrades"])
        self._draw_canvas()

    def _show_overlay(self) -> None:
        if self._overlay is not None:
            try:
                self._overlay.close()
            except Exception:
                pass
            self._overlay = None

        rect = _get_roblox_rect()
        if rect is None:
            messagebox.showwarning("Roblox not found",
                                   "Could not find the Roblox window. Make sure Roblox is open.")
            return

        rx, ry, rw, rh = rect
        self._overlay = Overlay(self.cfg, rx, ry, rw, rh)


def _recolor(widget: tk.Widget, bg: str) -> None:
    try:
        widget.configure(bg=bg)
    except tk.TclError:
        pass
    for child in widget.winfo_children():
        _recolor(child, bg)


if __name__ == "__main__":
    root = tk.Tk()
    app = PositionEditor(root)
    root.mainloop()
