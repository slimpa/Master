import os
import time
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2

from face_app.recognizer import detect_faces_and_eyes, evaluate_eye_state


class DriverMonitoringGUI:
    def __init__(
        self,
        root=None,
        capture_factory=None,
        detector=None,
        evaluator=None,
        clock=None,
        image_size=(780, 520),
        snapshots_dir=None
    ):
        self.root = root or tk.Tk()
        self.root.title("Driver Monitoring – Demo")
        self.root.geometry("1200x780")

        self.capture_factory = capture_factory or cv2.VideoCapture
        self.detector = detector or detect_faces_and_eyes
        self.evaluator = evaluator or evaluate_eye_state
        self.clock = clock or time.time

        self.image_size = image_size
        self.snapshots_dir = snapshots_dir or os.path.join(os.path.dirname(__file__), "snapshots")

        self.running = True
        self.mode = "instant"
        self.threshold_sec = 3.0

        self.closed_start_time = None
        self.last_alert_time = None
        self.last_frame = None

        self._build_ui()

        # Camera init
        self.cap = self.capture_factory(0)
        if not self.cap or not self.cap.isOpened():
            raise RuntimeError("Camera not accessible")

        # try set resolution (best-effort)
        try:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        except Exception:
            pass

    def _build_ui(self):
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        main = ttk.Frame(self.root)
        main.pack(fill="both", expand=True, padx=16, pady=16)
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(0, weight=1)

        # Left: video
        left = ttk.Frame(main)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        header = ttk.Frame(left)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="Live Camera", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, sticky="w")

        self.status_badge = tk.Label(header, text="WAITING", font=("Segoe UI", 11, "bold"), padx=12, pady=6)
        self.status_badge.grid(row=0, column=1, sticky="e")
        self._set_badge("warn", "WAITING")

        self.image_label = tk.Label(left, bg="black")
        self.image_label.grid(row=1, column=0, sticky="nsew", pady=(12, 0))

        # Right: controls
        right = ttk.Frame(main)
        right.grid(row=0, column=1, sticky="nsew")

        mode_box = ttk.Labelframe(right, text="Detection Mode")
        mode_box.pack(fill="x", pady=(0, 12))

        self.mode_var = tk.StringVar(value="instant")
        ttk.Radiobutton(mode_box, text="Instant", value="instant", variable=self.mode_var, command=self._on_mode).pack(anchor="w", padx=12, pady=(8, 4))
        ttk.Radiobutton(mode_box, text="Timed", value="timed", variable=self.mode_var, command=self._on_mode).pack(anchor="w", padx=12, pady=(0, 8))

        th_box = ttk.Labelframe(right, text="Timed Threshold")
        th_box.pack(fill="x", pady=(0, 12))

        self.th_label = ttk.Label(th_box, text="Threshold: 3.0 s")
        self.th_label.pack(anchor="w", padx=12, pady=(8, 4))

        self.th_var = tk.DoubleVar(value=3.0)
        ttk.Scale(th_box, from_=1.0, to=5.0, variable=self.th_var, command=self._on_threshold).pack(fill="x", padx=12, pady=(0, 8))

        act_box = ttk.Labelframe(right, text="Actions")
        act_box.pack(fill="x", pady=(0, 12))

        self.btn_toggle = ttk.Button(act_box, text="Stop", command=self.toggle_run)
        self.btn_toggle.pack(fill="x", padx=12, pady=(8, 6))

        ttk.Button(act_box, text="Snapshot", command=self.snapshot).pack(fill="x", padx=12, pady=(0, 10))

        self.info = ttk.Label(right, text="", wraplength=360)
        self.info.pack(fill="x")

    def _set_badge(self, kind, text):
        if kind == "ok":
            self.status_badge.configure(bg="#143D1B", fg="#B6F2C2")
        elif kind == "warn":
            self.status_badge.configure(bg="#3D2E14", fg="#FFE2A8")
        else:
            self.status_badge.configure(bg="#3D1414", fg="#FFB3B3")
        self.status_badge.configure(text=text)

    def _on_mode(self):
        self.mode = self.mode_var.get()

    def _on_threshold(self, _=None):
        self.threshold_sec = float(self.th_var.get())
        self.th_label.configure(text=f"Threshold: {self.threshold_sec:.1f} s")

    def toggle_run(self):
        self.running = not self.running
        self.btn_toggle.configure(text=("Stop" if self.running else "Start"))

    def snapshot(self):
        if self.last_frame is None:
            self.info.configure(text="No frame to save.")
            return

        try:
            os.makedirs(self.snapshots_dir, exist_ok=True)
            fname = time.strftime("snapshot_%Y%m%d_%H%M%S.png")
            path = os.path.join(self.snapshots_dir, fname)

            ok = cv2.imwrite(path, self.last_frame)
            if not ok:
                self.info.configure(text="Snapshot saving failed.")
                return

            self.info.configure(text=f"Saved: {fname}")

        except Exception as e:
            # bitno za testove i robustnost alata
            self.info.configure(text=f"Snapshot failed: {e}")

    def close(self):
        # release cap (ne smije crashovati)
        try:
            if self.cap is not None:
                try:
                    self.cap.release()
                except Exception:
                    pass
        finally:
            self.cap = None

        # destroy window (ne smije crashovati)
        try:
            self.root.destroy()
        except Exception:
            pass

    def _derive_has_open_eyes(self, detections):
        # open ako postoji bar 1 oko (detekcije su list-like)
        for d in detections or []:
            eyes = d.get("eyes", [])
            try:
                return len(eyes) > 0
            except Exception:
                pass
        return False

    def update_once(self):
        """
        Single update iteration: safe for unit tests.
        """
        if not self.running:
            return

        ret, frame = self.cap.read()
        if not ret or frame is None:
            # show alert-like state in UI
            self._set_badge("alert", "NO FRAME")
            return

        self.last_frame = frame.copy()

        detections = self.detector(frame)
        has_open = self._derive_has_open_eyes(detections)

        now = self.clock()
        status, self.closed_start_time, self.last_alert_time = self.evaluator(
            has_open_eyes=has_open,
            closed_start_time=self.closed_start_time,
            current_time=now,
            mode=self.mode,
            threshold_sec=self.threshold_sec,
            last_alert_time=self.last_alert_time
        )

        if status == "open":
            self._set_badge("ok", "OPEN")
        elif status == "closed":
            self._set_badge("warn", "CLOSED")
        else:
            self._set_badge("alert", "ALERT")

        # Draw simple overlays to execute codepaths
        for det in detections:
            (x, y, w, h) = det["face"]
            cv2.rectangle(frame, (x, y), (x + w, y + h), (80, 220, 120), 2)
            for (ex, ey, ew, eh) in det.get("eyes", []):
                cv2.rectangle(frame, (x + ex, y + ey), (x + ex + ew, y + ey + eh), (120, 160, 255), 2)

        try:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb).resize(self.image_size)
            imgtk = ImageTk.PhotoImage(img)

            # mora se čuvati referenca
            self.image_label.imgtk = imgtk
            self.image_label.configure(image=imgtk)

        except Exception:
            # u test režimu/bez mainloop-a Tk ponekad baci TclError
            # ne rušimo aplikaciju
            pass

    def start(self, run_mainloop=True):
        def loop():
            self.update_once()
            self.root.after(33, loop)

        self.root.protocol("WM_DELETE_WINDOW", self.close)
        loop()
        if run_mainloop:
            self.root.mainloop()


def run_gui(run_mainloop=True):
    app = DriverMonitoringGUI()
    app.start(run_mainloop=run_mainloop)