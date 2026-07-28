import tkinter as tk
import threading
import time
import math
import datetime
import psutil

BG   = "#000000"
CYAN = "#00BFFF"
DIM  = "#003050"
GRN  = "#00ff88"
AMB  = "#ff6600"
W, H = 400, 400
CX, CY = 200, 200

class AlfredDashboard:
    def __init__(self):
        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)
        self.root.configure(bg=BG)
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{W}x{H}+{sw-W-16}+{sh-H-50}")

        self.canvas = tk.Canvas(self.root, width=W, height=H, bg=BG, highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", lambda e: setattr(self, '_dx', e.x) or setattr(self, '_dy', e.y))
        self.canvas.bind("<B1-Motion>", self._drag)

        self.state    = "standby"
        self.angle    = 0.0
        self.angle2   = 0.0
        self.pulse    = 0.0
        self.energy   = 0.0
        self.t_energy = 0.0
        self.cpu = self.ram = self.batt = 0
        self.timestr  = ""
        self._running = True
        self._dx = self._dy = 0

        self._start_loops()

    def _drag(self, e):
        x = self.root.winfo_x() + (e.x - self._dx)
        y = self.root.winfo_y() + (e.y - self._dy)
        self.root.geometry(f"+{x}+{y}")

    def _col(self):
        if self.state == "listening": return CYAN
        if self.state == "speaking":  return GRN
        if self.state == "thinking":
            p = (math.sin(self.pulse * 3) + 1) / 2
            return f"#{int(255*p):02x}{int(100*p):02x}00"
        p = (math.sin(self.pulse * 0.4) + 1) / 2 * 0.5 + 0.3
        v = int(0xBF * p)
        return f"#00{v:02x}ff"

    def _draw(self):
        c = self.canvas
        c.delete("all")
        self.angle  = (self.angle  + 0.5) % 360
        self.angle2 = (self.angle2 - 0.3) % 360
        self.pulse += 0.06
        self.energy += (self.t_energy - self.energy) * 0.1
        col = self._col()

        # ── Segmented rings (like your reference images) ──────
        rings = [
            (170, 20, 8, col,  2),   # outer — cyan segments
            (145, 16, 6, AMB,  1),   # amber middle
            (120, 14, 8, col,  1),   # cyan inner
            (95,  12, 6, DIM,  1),   # dim innermost
        ]
        for radius, seg_count, gap, color, width in rings:
            seg_angle = 360 / seg_count
            offset    = self.angle if color == col else self.angle2
            for i in range(seg_count):
                start = offset + i * seg_angle
                extent = seg_angle - gap
                c.create_arc(
                    CX - radius, CY - radius,
                    CX + radius, CY + radius,
                    start=start, extent=extent,
                    outline=color, width=width, style="arc"
                )

        # ── Tick marks on outer ring ──────────────────────────
        for i in range(36):
            a   = math.radians(self.angle + i * 10)
            r1  = 173
            r2  = 178 if i % 3 == 0 else 175
            x1  = CX + r1 * math.cos(a)
            y1  = CY + r1 * math.sin(a)
            x2  = CX + r2 * math.cos(a)
            y2  = CY + r2 * math.sin(a)
            c.create_line(x1, y1, x2, y2, fill=col, width=1)

        # ── Pulse rings from center ───────────────────────────
        pulse_r = math.sin(self.pulse) * 5 * (1 + self.energy * 2)
        for r in [70, 55, 40]:
            rr = r + pulse_r
            c.create_oval(
                CX - rr, CY - rr, CX + rr, CY + rr,
                outline=col, width=1
            )

        # ── Center crosshair ──────────────────────────────────
        c.create_line(CX-25, CY, CX-8,  CY, fill=col, width=1)
        c.create_line(CX+8,  CY, CX+25, CY, fill=col, width=1)
        c.create_line(CX, CY-25, CX, CY-8,  fill=col, width=1)
        c.create_line(CX, CY+8,  CX, CY+25, fill=col, width=1)

        # ── Glowing core dot ─────────────────────────────────
        cr = int(12 + pulse_r + self.energy * 8)
        c.create_oval(CX-cr, CY-cr, CX+cr, CY+cr, fill=col, outline="")
        c.create_oval(CX-5,  CY-5,  CX+5,  CY+5,  fill=BG,  outline="")

        # ── Waveform bars (equalizer style) ───────────────────
        if self.energy > 0.05:
            n = 24
            for i in range(n):
                a   = math.radians(i * (360 / n))
                amp = self.energy * (
                    15 + 20 * abs(math.sin(self.pulse * 4 + i * 0.5))
                )
                r1  = 78
                r2  = r1 + amp
                x1  = CX + r1 * math.cos(a)
                y1  = CY + r1 * math.sin(a)
                x2  = CX + r2 * math.cos(a)
                y2  = CY + r2 * math.sin(a)
                c.create_line(x1, y1, x2, y2, fill=col, width=2)

        # ── Time ─────────────────────────────────────────────
        c.create_text(CX, 16, text=self.timestr, fill=col, font=("Courier", 11, "bold"))

        # ── State ────────────────────────────────────────────
        states = {"standby": "STANDBY", "listening": "LISTENING",
                  "thinking": "THINKING", "speaking": "SPEAKING"}
        c.create_text(CX, H-18, text=states.get(self.state, ""),
                      fill=col, font=("Courier", 8, "bold"))

        # ── Stats ────────────────────────────────────────────
        c.create_text(60,  H-18, text=f"CPU {self.cpu}%",  fill=DIM, font=("Courier", 7))
        c.create_text(340, H-18, text=f"BAT {self.batt}%", fill=AMB, font=("Courier", 7))

    def _start_loops(self):
        def render():
            while self._running:
                try: self.root.after(0, self._draw)
                except: break
                time.sleep(0.033)
        threading.Thread(target=render, daemon=True).start()

        def stats():
            while self._running:
                try:
                    self.cpu  = round(psutil.cpu_percent(interval=1))
                    self.ram  = round(psutil.virtual_memory().percent)
                    b         = psutil.sensors_battery()
                    self.batt = round(b.percent) if b else 0
                except: pass
                time.sleep(4)
        threading.Thread(target=stats, daemon=True).start()

        def clock():
            while self._running:
                self.timestr = datetime.datetime.now().strftime("%H:%M:%S")
                time.sleep(1)
        threading.Thread(target=clock, daemon=True).start()

    def set_listening(self):
        self.state = "listening"; self.t_energy = 0.5
    def set_speaking(self):
        self.state = "speaking";  self.t_energy = 1.0
    def set_thinking(self):
        self.state = "thinking";  self.t_energy = 0.2
    def set_standby(self):
        self.state = "standby";   self.t_energy = 0.0

    def add_user_message(self, text): self.set_thinking()
    def add_alfred_message(self, text): pass
    def update_memory_count(self, count): pass
    def push_audio_energy(self, energy): self.t_energy = min(energy, 1.0)

    def run(self): self.root.mainloop()

    def destroy(self):
        self._running = False
        try: self.root.quit(); self.root.destroy()
        except: pass


_dashboard = None

def get_dashboard(): return _dashboard

def start_dashboard():
    global _dashboard
    ready = threading.Event()
    def _run():
        global _dashboard
        _dashboard = AlfredDashboard()
        ready.set()
        _dashboard.run()
    threading.Thread(target=_run, daemon=True).start()
    ready.wait(timeout=3)
    return _dashboard