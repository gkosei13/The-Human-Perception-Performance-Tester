"""
Human Perception & Performance Tester
-------------------------------------
Tkinter app with:
  * Visual controls: contrast (High/Medium/Low), size (Small/Medium/Large),
    brightness slider
  * Task A: Identification of an ambiguous figure (Necker cube, duck/rabbit)
  * Task B: Target hitting (Fitts' Law) varying distance and target size
  * Automatic CSV logging to results.csv (same folder as this script)

Run:  python hci_tester.py
"""

import csv
import os
import random
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
CSV_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "results.csv")
CSV_COLUMNS = [
    "timestamp", "participant_id", "task_type", "visual_condition",
    "contrast", "size", "brightness_pct", "distance_px", "target_size_px",
    "time_seconds", "misses", "response", "ease_of_use_1to5",
]

# (foreground, background) before brightness scaling
CONTRAST = {
    "High":   ("#000000", "#FFFFFF"),   # ~21:1
    "Medium": ("#6E6E6E", "#D9D9D9"),   # ~3:1
    "Low":    ("#B5B5B5", "#D9D9D9"),   # ~1.5:1
}
FONT_SIZE = {"Small": 10, "Medium": 16, "Large": 26}   # approximates visual angle
SHAPE_SCALE = {"Small": 0.6, "Medium": 1.0, "Large": 1.5}

# Fitts' Law conditions
DISTANCES = [100, 250, 400]     # px from start circle to target centre
TARGET_SIZES = [20, 40, 80]     # px (square side)
REPETITIONS = 2                 # each distance x size combo is repeated

CANVAS_W, CANVAS_H = 900, 560


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def scale_colour(hex_colour, factor):
    """Darken a #RRGGBB colour by factor (0..1) to simulate lower brightness."""
    r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % (int(r * factor), int(g * factor), int(b * factor))


def ensure_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(CSV_COLUMNS)


def append_rows(rows):
    ensure_csv()
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        for row in rows:
            writer.writerow(row)


# ----------------------------------------------------------------------------
# Main application
# ----------------------------------------------------------------------------
class App:
    def __init__(self, root):
        self.root = root
        root.title("Human Perception & Performance Tester")
        root.resizable(False, False)

        # Experimenter-controlled variables
        self.participant = tk.StringVar(value="P1")
        self.contrast = tk.StringVar(value="High")
        self.size = tk.StringVar(value="Medium")
        self.brightness = tk.IntVar(value=100)

        # State
        self.mode = "idle"            # idle | identify | fitts_wait_start | fitts_wait_target
        self.stimulus_index = 0
        self.t_start = 0.0
        self.misses = 0
        self.trials = []
        self.trial_i = 0
        self.block_rows = []
        self.target_box = None        # (x1, y1, x2, y2)
        self.start_box = None

        self._build_ui()
        self.refresh_look()
        ensure_csv()

    # ------------------------------------------------------------------ UI
    def _build_ui(self):
        panel = tk.Frame(self.root, padx=10, pady=10)
        panel.grid(row=0, column=0, sticky="ns")

        tk.Label(panel, text="Experimenter Controls", font=("Arial", 13, "bold")).pack(anchor="w")

        tk.Label(panel, text="Participant ID").pack(anchor="w", pady=(10, 0))
        tk.Entry(panel, textvariable=self.participant, width=16).pack(anchor="w")

        self._radio_group(panel, "Contrast", self.contrast, list(CONTRAST))
        self._radio_group(panel, "Size", self.size, list(FONT_SIZE))

        tk.Label(panel, text="Brightness (%)", font=("Arial", 10, "bold")).pack(anchor="w", pady=(12, 0))
        tk.Scale(panel, from_=20, to=100, orient="horizontal", variable=self.brightness,
                 length=160, command=lambda _v: self.refresh_look()).pack(anchor="w")

        tk.Label(panel, text="Tasks", font=("Arial", 13, "bold")).pack(anchor="w", pady=(18, 4))
        tk.Button(panel, text="Identification Task", width=20,
                  command=self.start_identification).pack(pady=3)
        tk.Button(panel, text="Target Hitting Task", width=20,
                  command=self.start_fitts).pack(pady=3)

        tk.Label(panel, text=f"Data saved to:\n{os.path.basename(CSV_FILE)}",
                 fg="#555", justify="left").pack(anchor="w", pady=(20, 0))

        stage = tk.Frame(self.root)
        stage.grid(row=0, column=1, padx=(0, 10), pady=10)
        self.canvas = tk.Canvas(stage, width=CANVAS_W, height=CANVAS_H,
                                highlightthickness=1, highlightbackground="#444")
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        # Answer bar (only used by the identification task)
        self.answer_bar = tk.Frame(stage)
        self.answer_label = tk.Label(self.answer_bar, text="What do you see?")
        self.answer_label.pack(side="left", padx=5)
        self.answer_entry = tk.Entry(self.answer_bar, width=30)
        self.answer_entry.pack(side="left", padx=5)
        self.answer_entry.bind("<Return>", lambda _e: self.submit_identification())
        self.submit_btn = tk.Button(self.answer_bar, text="Submit",
                                    command=self.submit_identification)
        self.submit_btn.pack(side="left", padx=5)

    def _radio_group(self, parent, title, var, options):
        tk.Label(parent, text=title, font=("Arial", 10, "bold")).pack(anchor="w", pady=(12, 0))
        for opt in options:
            tk.Radiobutton(parent, text=opt, variable=var, value=opt,
                           command=self.refresh_look).pack(anchor="w")

    # -------------------------------------------------------------- look
    def colours(self):
        fg, bg = CONTRAST[self.contrast.get()]
        f = self.brightness.get() / 100.0
        return scale_colour(fg, f), scale_colour(bg, f)

    def font(self, bold=False):
        return ("Arial", FONT_SIZE[self.size.get()], "bold" if bold else "normal")

    def refresh_look(self):
        """Apply contrast / size / brightness to the stage and redraw it."""
        fg, bg = self.colours()
        self.canvas.config(bg=bg)
        self.answer_bar.config(bg=bg)
        self.answer_label.config(bg=bg, fg=fg, font=self.font())
        self.answer_entry.config(font=self.font(), bg=bg, fg=fg, insertbackground=fg)
        self.submit_btn.config(font=self.font(), bg=bg, fg=fg, activebackground=bg)
        if self.mode == "idle":
            self.show_message("Choose a task on the left.\nAdjust contrast, size and brightness first.")
        elif self.mode == "identify":
            self.draw_stimulus()

    def show_message(self, text):
        fg, _bg = self.colours()
        self.canvas.delete("all")
        self.canvas.create_text(CANVAS_W / 2, CANVAS_H / 2, text=text, fill=fg,
                                font=self.font(), justify="center", width=CANVAS_W - 60)

    # ------------------------------------------------- rating dialog
    def ask_rating(self, prompt):
        """Modal 1-5 ease-of-use dialog. Returns an int."""
        result = {"value": None}
        win = tk.Toplevel(self.root)
        win.title("Ease of use")
        win.transient(self.root)
        win.protocol("WM_DELETE_WINDOW", lambda: None)   # force an answer
        tk.Label(win, text=prompt, font=("Arial", 12), padx=15, pady=10).pack()
        tk.Label(win, text="1 = very difficult      5 = very easy").pack()
        row = tk.Frame(win, pady=10)
        row.pack()

        def choose(v):
            result["value"] = v
            win.destroy()

        for v in range(1, 6):
            tk.Button(row, text=str(v), width=4, height=2,
                      command=lambda v=v: choose(v)).pack(side="left", padx=4)
        win.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - win.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - win.winfo_height()) // 2
        win.geometry(f"+{x}+{y}")
        win.grab_set()
        self.root.wait_window(win)
        return result["value"]

    # --------------------------------------------- row construction
    def base_row(self, task):
        c, s, b = self.contrast.get(), self.size.get(), self.brightness.get()
        return {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "participant_id": self.participant.get().strip() or "unknown",
            "task_type": task,
            "visual_condition": f"contrast={c}; size={s}; brightness={b}%",
            "contrast": c, "size": s, "brightness_pct": b,
            "distance_px": "", "target_size_px": "", "time_seconds": "",
            "misses": "", "response": "", "ease_of_use_1to5": "",
        }

    # ===================================================== IDENTIFICATION
    def start_identification(self):
        self.mode = "identify"
        self.stimulus_index = (self.stimulus_index + 1) % 2
        self.answer_entry.delete(0, "end")
        self.answer_bar.pack(pady=6, fill="x")
        self.draw_stimulus()
        self.answer_entry.focus_set()
        self.t_start = time.perf_counter()

    def draw_stimulus(self):
        fg, bg = self.colours()
        s = SHAPE_SCALE[self.size.get()]
        cx, cy = CANVAS_W / 2, CANVAS_H / 2
        c = self.canvas
        c.delete("all")

        if self.stimulus_index == 0:
            # Necker cube: two offset squares joined at corners
            L = 130 * s
            x0, y0 = cx - L * 0.75, cy - L * 0.25
            dx, dy = L * 0.5, -L * 0.5
            front = [(x0, y0), (x0 + L, y0), (x0 + L, y0 + L), (x0, y0 + L)]
            back = [(x + dx, y + dy) for x, y in front]
            for pts in (front, back):
                c.create_polygon(pts, outline=fg, fill="", width=3)
            for (a, b_) in zip(front, back):
                c.create_line(a, b_, fill=fg, width=3)
        else:
            # Duck / rabbit: left lobes are a duck's bill OR a rabbit's ears
            def T(pts):
                return [coord for x, y in pts for coord in (cx + x * s, cy + y * s)]
            head = [-90, -70, 110, 80]
            c.create_oval(cx + head[0] * s, cy + head[1] * s, cx + head[2] * s,
                          cy + head[3] * s, outline=fg, fill=bg, width=3)
            upper = [(-60, -45), (-130, -110), (-190, -125), (-170, -85), (-100, -20)]
            lower = [(-80, 10), (-160, -25), (-195, -10), (-165, 20), (-90, 35)]
            for lobe in (upper, lower):
                c.create_polygon(T(lobe), outline=fg, fill=bg, width=3, smooth=True)
            r = 6 * s
            ex, ey = cx + 20 * s, cy - 20 * s
            c.create_oval(ex - r, ey - r, ex + r, ey + r, fill=fg, outline=fg)

        c.create_text(CANVAS_W / 2, 30, text="Describe what you see, then press Submit",
                      fill=fg, font=self.font())

    def submit_identification(self):
        if self.mode != "identify":
            return
        elapsed = time.perf_counter() - self.t_start
        response = self.answer_entry.get().strip()
        if not response:
            messagebox.showinfo("Identification", "Please type what you see first.")
            return
        self.mode = "idle"
        rating = self.ask_rating("How easy was it to identify the shape?")
        row = self.base_row("Identification")
        row.update({"time_seconds": round(elapsed, 3), "response": response,
                    "ease_of_use_1to5": rating})
        append_rows([row])
        self.answer_bar.pack_forget()
        self.refresh_look()
        self.show_message("Saved. Change the visual conditions and run the task again.")

    # ======================================================== FITTS' LAW
    def start_fitts(self):
        self.answer_bar.pack_forget()
        combos = [(d, s) for d in DISTANCES for s in TARGET_SIZES] * REPETITIONS
        random.shuffle(combos)
        self.trials = combos
        self.trial_i = 0
        self.block_rows = []
        self.next_trial()

    def next_trial(self):
        if self.trial_i >= len(self.trials):
            self.finish_fitts()
            return
        fg, _bg = self.colours()
        c = self.canvas
        c.delete("all")
        cx, cy = CANVAS_W / 2, CANVAS_H / 2
        r = 25
        self.start_box = (cx - r, cy - r, cx + r, cy + r)
        c.create_oval(*self.start_box, outline=fg, width=3)
        c.create_text(cx, cy, text="Start", fill=fg, font=("Arial", 9, "bold"))
        c.create_text(CANVAS_W / 2, 30, fill=fg, font=self.font(),
                      text=f"Trial {self.trial_i + 1} of {len(self.trials)}: "
                           f"click the circle, then the square as fast as you can")
        self.target_box = None
        self.misses = 0
        self.mode = "fitts_wait_start"

    def show_target(self):
        fg, _bg = self.colours()
        dist, size = self.trials[self.trial_i]
        direction = random.choice([-1, 1])
        tx = CANVAS_W / 2 + direction * dist
        ty = CANVAS_H / 2
        h = size / 2
        self.target_box = (tx - h, ty - h, tx + h, ty + h)
        self.canvas.create_rectangle(*self.target_box, fill=fg, outline=fg)
        self.mode = "fitts_wait_target"
        self.misses = 0
        self.t_start = time.perf_counter()

    @staticmethod
    def inside(box, x, y):
        return box[0] <= x <= box[2] and box[1] <= y <= box[3]

    def on_canvas_click(self, event):
        if self.mode == "fitts_wait_start":
            # Accept clicks within the circle's bounding box
            if self.inside(self.start_box, event.x, event.y):
                self.show_target()
        elif self.mode == "fitts_wait_target":
            if self.inside(self.target_box, event.x, event.y):
                elapsed = time.perf_counter() - self.t_start
                dist, size = self.trials[self.trial_i]
                row = self.base_row("Target Hitting")
                row.update({"distance_px": dist, "target_size_px": size,
                            "time_seconds": round(elapsed, 3), "misses": self.misses})
                self.block_rows.append(row)
                self.trial_i += 1
                self.mode = "idle"
                self.root.after(250, self.next_trial)
            else:
                self.misses += 1

    def finish_fitts(self):
        self.mode = "idle"
        rating = self.ask_rating("How easy was it to hit the targets?")
        for row in self.block_rows:
            row["ease_of_use_1to5"] = rating
        append_rows(self.block_rows)
        self.refresh_look()
        self.show_message(f"Block complete ({len(self.block_rows)} trials saved).\n"
                          "Change the visual conditions and run it again.")


if __name__ == "__main__":
    tk_root = tk.Tk()
    App(tk_root)
    tk_root.mainloop()
