"""
Happy Macro GUI
"""

import ctypes
import json
import os
import queue
import sys
import threading
import time
import tkinter as tk

_HERE = os.path.dirname(os.path.abspath(__file__))

# Point pytesseract at the bundled tesseract binary
import pytesseract as _pt
_pt.pytesseract.tesseract_cmd = os.path.join(_HERE, "tesseract", "tesseract.exe")

for _p in (
    os.path.join(_HERE, "Tools"),
    os.path.join(_HERE, "avlib"),
    os.path.join(_HERE, "rblib", "src"),
    os.path.join(_HERE, "core"),
):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import keyboard
import macro_state
import webhook
from act1_loop import run_act1
from rblib.r_client import focus_roblox_window

_CONFIG_PATH = os.path.join(_HERE, "config.json")

def _load_config() -> dict:
    try:
        with open(_CONFIG_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def _save_config(data: dict) -> None:
    with open(_CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


# ── Palette ────────────────────────────────────────────────────────────────
BG      = "#13120f"
SURFACE = "#1a1916"
CARD    = "#1f1d19"
CARD2   = "#252320"
BORDER  = "#2e2b24"
BORDER2 = "#3a3730"
ENTRY   = "#17160f"
FG      = "#e8e0d0"
FG_DIM  = "#7a7060"
FG_MID  = "#a89880"
SEL_BG  = "#2e2b24"

GREEN   = "#6dbb5e"
GREEN_D = "#3d7a30"
GREEN_A = "#58a04a"
RED     = "#c45c5c"
RED_D   = "#7a2828"
RED_A   = "#a84444"
AMBER   = "#d49030"
AMBER_A = "#b87820"
BLUE    = "#5b8dd9"

_DOT_IDLE = "#3a3730"
_DOT_RUN  = GREEN
_DOT_STOP = AMBER
_DOT_ERR  = RED

FONT_UI    = ("Segoe UI",          10)
FONT_LABEL = ("Segoe UI",           9)
FONT_SMALL = ("Segoe UI",           8)
FONT_TITLE = ("Segoe UI Semibold", 12)
FONT_STAT  = ("Segoe UI Semibold", 22)
FONT_CODE  = ("Segoe UI Semibold", 36)
FONT_MONO  = ("Consolas",           9)

WIN_W = 480


# ── Helpers ────────────────────────────────────────────────────────────────

def _hover(w, n, a):
    w.bind("<Enter>", lambda _: w.config(bg=a))
    w.bind("<Leave>", lambda _: w.config(bg=n))

def _fmt_time(s: float) -> str:
    s = int(max(0, s))
    return f"{s//3600:02d}:{(s%3600)//60:02d}:{s%60:02d}"


# ── GUI ────────────────────────────────────────────────────────────────────

class MacroGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Happy Macro")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)
        self.root.geometry(f"{WIN_W}x1")   # height snaps to content

        self._thread:     threading.Thread | None = None
        self._stop_event: threading.Event         = threading.Event()
        self._log_queue:  queue.Queue             = queue.Queue(maxsize=600)
        self._pulse:      bool                    = False
        self._cfg                                 = _load_config()

        self._build_ui()
        self._apply_config()
        self._tick()
        self.root.update_idletasks()
        self.root.geometry(f"{WIN_W}x{self.root.winfo_reqheight()}")

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        keyboard.on_press_key("f1", lambda _: self.root.after(0, self._on_start))
        keyboard.on_press_key("f3", lambda _: self.root.after(0, self._on_stop))

    # ── low-level widget factories ─────────────────────────────

    def _section(self, title: str) -> tk.Frame:
        """Divider label + bordered card, returns inner frame."""
        row = tk.Frame(self.root, bg=BG)
        row.pack(fill="x", padx=14, pady=(10, 0))
        tk.Frame(row, bg=BORDER, height=1).pack(side="left", fill="y", padx=(0, 6))
        tk.Label(row, text=title, bg=BG, fg=FG_DIM,
                 font=FONT_SMALL).pack(side="left")
        tk.Frame(row, bg=BORDER, height=1).pack(side="left", fill="both",
                                                 expand=True, padx=(6, 0))
        outer = tk.Frame(self.root, bg=BORDER2)
        outer.pack(fill="x", padx=14, pady=(4, 0))
        inner = tk.Frame(outer, bg=CARD)
        inner.pack(fill="x", padx=1, pady=1)
        return inner

    def _btn(self, parent, text, cmd, bg, hbg,
             width=None, font=FONT_UI, state="normal", fg=FG):
        kw = dict(text=text, bg=bg, fg=fg,
                  activebackground=hbg, activeforeground=fg,
                  relief="flat", bd=0, cursor="hand2",
                  font=font, command=cmd, state=state,
                  padx=16, pady=8)
        if width:
            kw["width"] = width
        b = tk.Button(parent, **kw)
        if state != "disabled":
            _hover(b, bg, hbg)
        return b

    def _entry(self, parent, var, width=None, show=None):
        kw = dict(textvariable=var, bg=ENTRY, fg=FG,
                  insertbackground=FG, selectbackground=SEL_BG,
                  selectforeground=FG, relief="flat", bd=0,
                  font=FONT_UI, highlightthickness=1,
                  highlightbackground=BORDER2, highlightcolor=AMBER)
        if width:
            kw["width"] = width
        if show:
            kw["show"] = show
        e = tk.Entry(parent, **kw)
        e.bind("<FocusIn>",  lambda _: e.config(highlightbackground=AMBER))
        e.bind("<FocusOut>", lambda _: e.config(highlightbackground=BORDER2))
        return e

    def _row(self, parent, pady=(4, 4)) -> tk.Frame:
        f = tk.Frame(parent, bg=CARD)
        f.pack(fill="x", padx=14, pady=pady)
        return f

    def _field_label(self, parent, text, width=15):
        tk.Label(parent, text=text, bg=CARD, fg=FG_MID,
                 font=FONT_LABEL, width=width, anchor="w").pack(side="left")

    def _sep(self, parent, color=BORDER):
        tk.Frame(parent, bg=color, height=1).pack(fill="x")

    # ── build ──────────────────────────────────────────────────

    def _build_ui(self):
        self._build_header()
        self._build_controls()
        self._build_stats()
        self._build_config()
        self._build_status()
        self._build_footer()

    # header ───────────────────────────────────────────────────

    def _build_header(self):
        hdr = tk.Frame(self.root, bg=BG)
        hdr.pack(fill="x", padx=16, pady=(14, 6))

        left = tk.Frame(hdr, bg=BG)
        left.pack(side="left")
        tk.Label(left, text="◆", bg=BG, fg=AMBER,
                 font=("Segoe UI", 14)).pack(side="left", padx=(0, 6))
        tk.Label(left, text="Happy Macro", bg=BG, fg=FG,
                 font=FONT_TITLE).pack(side="left")

        right = tk.Frame(hdr, bg=BG)
        right.pack(side="right")
        self._dot_cv = tk.Canvas(right, width=8, height=8,
                                  bg=BG, highlightthickness=0)
        self._dot_cv.pack(side="left", padx=(0, 6))
        self._dot_id = self._dot_cv.create_oval(1, 1, 7, 7,
                                                  fill=_DOT_IDLE, outline="")
        self._status_var = tk.StringVar(value="idle")
        tk.Label(right, textvariable=self._status_var,
                 bg=BG, fg=FG_DIM, font=FONT_LABEL).pack(side="left")

    # controls ─────────────────────────────────────────────────

    def _build_controls(self):
        inner = self._section("CONTROLS")

        row = tk.Frame(inner, bg=CARD)
        row.pack(fill="x", padx=12, pady=12)

        self._start_btn = self._btn(row, "▶  Start", self._on_start, GREEN_D, GREEN_A,
                                    font=FONT_UI, fg="#d0f0c0")
        self._start_btn.pack(side="left", padx=(0, 6))

        self._stop_btn = self._btn(row, "■  Stop", self._on_stop, RED_D, RED_A,
                                   font=FONT_UI, fg="#f0d0d0", state="disabled")
        self._stop_btn.pack(side="left", padx=(0, 6))

        self._align_btn = self._btn(row, "⊡  Align", self._on_align,
                                    CARD2, BORDER2, font=FONT_UI)
        self._align_btn.pack(side="left")

        tk.Label(row, text="F1  /  F3", bg=CARD, fg=FG_DIM,
                 font=FONT_SMALL).pack(side="right", padx=2)

    # stats ────────────────────────────────────────────────────

    def _build_stats(self):
        inner = self._section("STATS")

        # big counters
        nums = tk.Frame(inner, bg=CARD)
        nums.pack(fill="x", padx=14, pady=(14, 6))

        self._runs_var = tk.StringVar(value="0")
        self._wins_var = tk.StringVar(value="0")
        self._loss_var = tk.StringVar(value="0")

        for var, label, color in (
            (self._runs_var, "RUNS",   FG),
            (self._wins_var, "WINS",   GREEN),
            (self._loss_var, "LOSSES", RED),
        ):
            blk = tk.Frame(nums, bg=CARD)
            blk.pack(side="left", padx=(0, 32))
            tk.Label(blk, textvariable=var, bg=CARD, fg=color,
                     font=FONT_STAT).pack(anchor="w")
            tk.Label(blk, text=label, bg=CARD, fg=FG_DIM,
                     font=("Segoe UI", 7)).pack(anchor="w")

        # win-rate bar
        bar_row = tk.Frame(inner, bg=CARD)
        bar_row.pack(fill="x", padx=14, pady=(0, 8))

        self._wr_label = tk.Label(bar_row, text="—% win rate",
                                   bg=CARD, fg=FG_DIM, font=FONT_SMALL,
                                   anchor="e")
        self._wr_label.pack(side="right", padx=(6, 0))

        bar_bg = tk.Frame(bar_row, bg=BORDER, height=4)
        bar_bg.pack(side="left", fill="x", expand=True, pady=6)
        bar_bg.pack_propagate(False)
        self._wr_bar = tk.Frame(bar_bg, bg=GREEN_D, height=4)
        self._wr_bar.place(x=0, y=0, relheight=1, relwidth=0)

        self._sep(inner)

        # timers
        timers = tk.Frame(inner, bg=CARD)
        timers.pack(fill="x", padx=14, pady=(8, 14))

        self._sess_var     = tk.StringVar(value="00:00:00")
        self._run_var      = tk.StringVar(value="00:00:00")
        self._last_run_var = tk.StringVar(value="—")

        for label, var in (
            ("Session", self._sess_var),
            ("Run",     self._run_var),
            ("Last",    self._last_run_var),
        ):
            blk = tk.Frame(timers, bg=CARD)
            blk.pack(side="left", padx=(0, 24))
            tk.Label(blk, text=label, bg=CARD, fg=FG_DIM,
                     font=FONT_SMALL).pack(side="left", padx=(0, 5))
            tk.Label(blk, textvariable=var, bg=CARD, fg=FG,
                     font=FONT_LABEL).pack(side="left")

    # config ───────────────────────────────────────────────────

    def _build_config(self):
        inner = self._section("CONFIG")

        _cfg   = self._cfg
        _teams = list(range(1, 13))

        # teams row
        row = self._row(inner, pady=(12, 4))
        self._act1_team_var = tk.IntVar(value=_cfg.get("act1_team", 1))
        self._act2_team_var = tk.IntVar(value=_cfg.get("act2_team", 2))

        for label, var in (("Act 1 Team", self._act1_team_var),
                            ("Act 2 Team", self._act2_team_var)):
            tk.Label(row, text=label, bg=CARD, fg=FG_MID,
                     font=FONT_LABEL).pack(side="left", padx=(0, 4))
            dd = tk.OptionMenu(row, var, *_teams)
            dd.config(bg=ENTRY, fg=FG, activebackground=SEL_BG, activeforeground=FG,
                      relief="flat", bd=0, highlightthickness=1,
                      highlightbackground=BORDER2, highlightcolor=AMBER,
                      font=FONT_LABEL, width=3, cursor="hand2")
            dd["menu"].config(bg=CARD2, fg=FG, activebackground=SEL_BG,
                              activeforeground=FG, font=FONT_LABEL)
            dd.pack(side="left", padx=(0, 20))

        # caloric
        row = self._row(inner)
        self._field_label(row, "Caloric Unit")
        self._caloric_var = tk.StringVar(value=_cfg.get("caloric_unit", "(Final"))
        self._entry(row, self._caloric_var, width=22).pack(side="left")

        self._sep(inner)

        # private server
        row = self._row(inner)
        self._field_label(row, "Private Server")
        self._ps_var = tk.StringVar(value=_cfg.get("private_server", ""))
        self._entry(row, self._ps_var).pack(side="left", fill="x", expand=True, padx=(0, 6))
        join = self._btn(row, "Join", self._on_join_ps, CARD2, BORDER2, font=FONT_LABEL)
        join.pack(side="left")

        # webhook
        row = self._row(inner)
        self._field_label(row, "Webhook URL")
        self._wh_var = tk.StringVar(value=_cfg.get("webhook_url", ""))
        wh = self._entry(row, self._wh_var)
        wh.pack(side="left", fill="x", expand=True)
        wh.bind("<FocusOut>", lambda _: self._save_prefs())
        wh.bind("<Return>",   lambda _: self._save_prefs())

        # auto-rejoin
        row = self._row(inner, pady=(4, 12))
        self._field_label(row, "Auto-rejoin after")
        self._rejoin_var = tk.StringVar(value=str(_cfg.get("auto_rejoin_runs", 0)))
        self._entry(row, self._rejoin_var, width=5).pack(side="left", padx=(0, 6))
        tk.Label(row, text="runs  (0 = off)", bg=CARD, fg=FG_DIM,
                 font=FONT_LABEL).pack(side="left")

        # trace saves
        for var in (self._act1_team_var, self._act2_team_var, self._caloric_var,
                    self._ps_var, self._rejoin_var):
            var.trace_add("write", lambda *_: self._save_prefs())

    # status / code ────────────────────────────────────────────

    def _build_status(self):
        inner = self._section("STATUS")

        self._phase_var = tk.StringVar(value="—")
        tk.Label(inner, textvariable=self._phase_var,
                 bg=CARD, fg=FG_MID, font=FONT_LABEL,
                 anchor="w", padx=14, pady=6).pack(fill="x")

        self._sep(inner)

        self._code_var = tk.StringVar(value="—")
        tk.Label(inner, textvariable=self._code_var,
                 bg=CARD, fg=AMBER, font=FONT_CODE,
                 anchor="center", pady=14).pack(fill="x")

    # footer ───────────────────────────────────────────────────

    def _build_footer(self):
        foot = tk.Frame(self.root, bg=BG)
        foot.pack(fill="x", padx=14, pady=(10, 10))

        self._show_log = tk.BooleanVar(value=False)
        tk.Checkbutton(foot, text="Show log", variable=self._show_log,
                       command=self._toggle_log,
                       bg=BG, fg=FG_DIM, selectcolor=ENTRY,
                       activebackground=BG, activeforeground=FG,
                       font=FONT_SMALL, bd=0, cursor="hand2").pack(side="left")

        self._log_frame = tk.Frame(self.root, bg=SURFACE, bd=0)
        self._log_frame.pack(fill="x", padx=14, pady=(0, 10))
        self._log_frame.pack_forget()

        self._log_text = tk.Text(
            self._log_frame, height=9, state="disabled", wrap="word",
            font=FONT_MONO, bg=SURFACE, fg=FG_DIM, relief="flat", bd=0,
            padx=10, pady=8, insertbackground=FG,
            selectbackground=SEL_BG,
        )
        sb = tk.Scrollbar(self._log_frame, command=self._log_text.yview,
                          bg=SURFACE, troughcolor=BG, width=10, relief="flat")
        self._log_text.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._log_text.pack(side="left", fill="both", expand=True)

    # ── config persistence ─────────────────────────────────────

    def _apply_config(self):
        cfg = self._cfg
        for key, attr, state_attr in (
            ("webhook_url",      "_wh_var",     "WEBHOOK_URL"),
            ("private_server",   "_ps_var",     "PRIVATE_SERVER_CODE"),
        ):
            if key in cfg:
                getattr(self, attr).set(cfg[key])
                setattr(macro_state, state_attr, cfg[key])
        if "auto_rejoin_runs" in cfg:
            self._rejoin_var.set(str(cfg["auto_rejoin_runs"]))
            macro_state.AUTO_REJOIN_AFTER_RUNS = int(cfg["auto_rejoin_runs"])

    def _save_prefs(self):
        try:
            macro_state.WEBHOOK_URL            = self._wh_var.get().strip()
            macro_state.PRIVATE_SERVER_CODE    = self._ps_var.get().strip()
            macro_state.AUTO_REJOIN_AFTER_RUNS = int(self._rejoin_var.get() or 0)

            import json as _j
            with open(os.path.join(_HERE, "config", "settings.json"), "w") as f:
                _j.dump({"webhook_url": macro_state.WEBHOOK_URL}, f, indent=2)
        except (ValueError, Exception):
            pass

        _save_config({
            "act1_team":        self._act1_team_var.get(),
            "act2_team":        self._act2_team_var.get(),
            "caloric_unit":     self._caloric_var.get(),
            "private_server":   self._ps_var.get().strip(),
            "webhook_url":      self._wh_var.get().strip(),
            "auto_rejoin_runs": self._rejoin_var.get(),
        })

    # ── worker ─────────────────────────────────────────────────

    def _worker(self):
        act1_team    = self._act1_team_var.get()
        act2_team    = self._act2_team_var.get()
        caloric_unit = self._caloric_var.get().strip()
        cycle        = 0

        macro_state.state.update({
            "session_start":     time.time(),
            "wins":              0,
            "losses":            0,
            "total_runs":        0,
            "runs_since_rejoin": 0,
            "running":           True,
        })

        def _update_code(c: str):
            self.root.after(0, lambda: self._code_var.set(c))

        def _sess_str() -> str:
            return _fmt_time(time.time() - macro_state.state["session_start"])

        try:
            from rejoin import do_lobby_path, is_in_lobby
            if is_in_lobby():
                self._log("Lobby detected — pathing to Happy Act 1")
                self._set_phase("Lobby → Happy Act 1…")
                do_lobby_path(stop_event=self._stop_event, log_cb=self._log)

            while not self._stop_event.is_set():
                cycle += 1
                self._set_phase(f"Cycle {cycle}")
                self.root.after(0, lambda: self._code_var.set("—"))

                rejoin_after = macro_state.AUTO_REJOIN_AFTER_RUNS
                if rejoin_after > 0 and macro_state.state["runs_since_rejoin"] >= rejoin_after:
                    self._log(f"Auto-rejoin after {macro_state.state['runs_since_rejoin']} runs")
                    self._set_phase("Rejoining Roblox…")
                    from rejoin import do_rejoin
                    if do_rejoin(stop_event=self._stop_event, log_cb=self._log):
                        do_lobby_path(stop_event=self._stop_event, log_cb=self._log)
                    macro_state.state["runs_since_rejoin"] = 0
                    if self._stop_event.is_set():
                        break

                code, victory = run_act1(
                    act1_team=act1_team,
                    act2_team=act2_team,
                    caloric_unit=caloric_unit,
                    stop_event=self._stop_event,
                    log_cb=self._log,
                    code_cb=_update_code,
                )
                if self._stop_event.is_set():
                    break

                macro_state.state["total_runs"]        += 1
                macro_state.state["runs_since_rejoin"] += 1
                if victory is True:
                    macro_state.state["wins"]   += 1
                elif victory is False:
                    macro_state.state["losses"] += 1

                w = macro_state.state["wins"]
                l = macro_state.state["losses"]
                self._log(f"Cycle {cycle} — W:{w} L:{l} | code: {code}")
                self._set_phase(f"Cycle {cycle} done")

                if victory is not None:
                    threading.Thread(
                        target=webhook.send,
                        args=(w, l, _sess_str()),
                        daemon=True,
                    ).start()

            self._set_phase("Stopped")

        except Exception as exc:
            self._log(f"ERROR: {exc}")
            self.root.after(0, lambda: self._set_status("error", _DOT_ERR))
            self.root.after(0, lambda: self._set_phase(f"Error: {exc}"))
        finally:
            macro_state.state["running"] = False
            self.root.after(0, self._on_run_complete)

    def _on_run_complete(self):
        self._start_btn.config(state="normal")
        _hover(self._start_btn, GREEN_D, GREEN_A)
        self._stop_btn.config(state="disabled")
        self._set_status("idle", _DOT_IDLE)

    # ── actions ────────────────────────────────────────────────

    def _on_start(self):
        if self._thread and self._thread.is_alive():
            return
        self._save_prefs()
        self._stop_event.clear()
        self._code_var.set("—")
        self._set_status("running", _DOT_RUN)
        self._set_phase("Starting…")
        self._start_btn.config(state="disabled")
        self._stop_btn.config(state="normal")
        _hover(self._stop_btn, RED_D, RED_A)
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def _on_stop(self):
        self._stop_event.set()
        self._set_status("stopping…", _DOT_STOP)
        self._stop_btn.config(state="disabled")

    def _on_align(self):
        focus_roblox_window()
        self._set_phase("Window aligned")

    def _on_join_ps(self):
        code = self._ps_var.get().strip()
        if not code:
            self._set_status("no private server link set", _DOT_ERR)
            return
        from rejoin import extract_ps_code
        url = f"roblox://placeId=16146832113&linkCode={extract_ps_code(code)}/"
        try:
            os.startfile(url)
        except Exception:
            import subprocess
            subprocess.Popen(["start", url], shell=True)

    def _on_close(self):
        self._save_prefs()
        self._stop_event.set()
        self.root.destroy()

    # ── helpers ────────────────────────────────────────────────

    def _set_status(self, text: str, dot: str):
        self._status_var.set(text)
        self._dot_cv.itemconfig(self._dot_id, fill=dot)

    def _set_phase(self, text: str):
        self.root.after(0, lambda: self._phase_var.set(text))

    def _log(self, msg: str):
        try:
            self._log_queue.put_nowait(msg)
        except queue.Full:
            pass

    def _toggle_log(self):
        if self._show_log.get():
            self._log_frame.pack(fill="x", padx=14, pady=(0, 10))
        else:
            self._log_frame.pack_forget()
        self.root.update_idletasks()
        self.root.geometry(f"{WIN_W}x{self.root.winfo_reqheight()}")

    # ── tick ───────────────────────────────────────────────────

    def _tick(self):
        st = macro_state.state

        # counters
        self._runs_var.set(str(st["total_runs"]))
        self._wins_var.set(str(st["wins"]))
        self._loss_var.set(str(st["losses"]))

        # win-rate bar
        total = st["wins"] + st["losses"]
        if total > 0:
            wr = st["wins"] / total
            self._wr_bar.place(relwidth=wr)
            self._wr_bar.config(bg=GREEN if wr >= 0.5 else RED_D)
            self._wr_label.config(text=f"{wr*100:.0f}% win rate")
        else:
            self._wr_bar.place(relwidth=0)
            self._wr_label.config(text="—% win rate")

        # timers
        if st["session_start"] > 0 and st["running"]:
            self._sess_var.set(_fmt_time(time.time() - st["session_start"]))
        if st["running"] and st["run_start"] > 0:
            self._run_var.set(_fmt_time(time.time() - st["run_start"]))
        if st["last_run_time"] > 0:
            self._last_run_var.set(_fmt_time(st["last_run_time"]))

        # pulse dot
        if st["running"]:
            self._pulse = not self._pulse
            self._dot_cv.itemconfig(self._dot_id,
                                     fill=GREEN if self._pulse else GREEN_A)

        # log drain
        if self._show_log.get():
            msgs = []
            try:
                while True:
                    msgs.append(self._log_queue.get_nowait())
            except queue.Empty:
                pass
            if msgs:
                at_bottom = self._log_text.yview()[1] >= 0.99
                self._log_text.config(state="normal")
                self._log_text.insert("end", "\n".join(msgs) + "\n")
                if at_bottom:
                    self._log_text.see("end")
                self._log_text.config(state="disabled")

        self.root.after(500, self._tick)


# ── entry ──────────────────────────────────────────────────────────────────

_MUTEX = None

def _single_instance() -> bool:
    global _MUTEX
    _MUTEX = ctypes.windll.kernel32.CreateMutexW(None, True, "HappyMacro_Instance")
    return ctypes.windll.kernel32.GetLastError() != 183


if __name__ == "__main__":
    if not _single_instance():
        import tkinter.messagebox as mb
        _r = tk.Tk(); _r.withdraw()
        mb.showerror("Already running", "Happy Macro is already running.")
        _r.destroy()
        sys.exit(1)

    root = tk.Tk()
    MacroGUI(root)
    root.mainloop()
