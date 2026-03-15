import numpy as np
import pytest
import tkinter as tk
from face_app.gui import DriverMonitoringGUI


class FakeCap:
    def __init__(self, opened=True, frames=None):
        self._opened = opened
        self.frames = frames or [(True, np.zeros((50, 50, 3), dtype=np.uint8))]
        self.i = 0

    def isOpened(self):
        return self._opened

    def read(self):
        if self.i >= len(self.frames):
            return False, None
        v = self.frames[self.i]
        self.i += 1
        return v

    def release(self):
        pass

    def set(self, *_):
        return True


@pytest.mark.test_id("UT_SWR_04_02")
@pytest.mark.requirement("SWR_04")
def test_gui_init_camera_not_accessible():
    """UT_SWR_04_02
    GUI must raise when camera not accessible.
    """
    root = tk.Tk()
    root.withdraw()

    with pytest.raises(RuntimeError):
        DriverMonitoringGUI(root=root, capture_factory=lambda idx: FakeCap(opened=False))

    root.destroy()


@pytest.mark.test_id("IT_SYS_01_04")
@pytest.mark.requirement("SYS_01")
def test_gui_update_once_open_closed_alert_paths(tmp_path):
    """IT_SYS_01_04
    GUI update_once must handle OPEN/CLOSED/ALERT and snapshot.
    """
    root = tk.Tk()
    root.withdraw()

    # fake detections: first open (has eyes), then closed (no eyes), then no frame
    def detector_open(_frame):
        return [{"face": (0, 0, 10, 10), "eyes": [(1, 1, 2, 2)]}]

    def detector_closed(_frame):
        return [{"face": (0, 0, 10, 10), "eyes": []}]

    # evaluator that cycles statuses
    states = ["open", "closed", "alert"]

    def evaluator(has_open_eyes, closed_start_time, current_time, mode="instant", threshold_sec=3.0, last_alert_time=None, **_):
        s = states.pop(0)
        if s == "open":
            return "open", None, last_alert_time
        if s == "closed":
            return "closed", current_time if closed_start_time is None else closed_start_time, last_alert_time
        return "alert", closed_start_time, current_time

    cap = FakeCap(opened=True, frames=[
        (True, np.zeros((50, 50, 3), dtype=np.uint8)),  # OPEN
        (True, np.zeros((50, 50, 3), dtype=np.uint8)),  # CLOSED
        (True, np.zeros((50, 50, 3), dtype=np.uint8)),  # ALERT (evaluator)
        (False, None),  # tek nakon toga NO FRAME (opciono)
    ])

    gui = DriverMonitoringGUI(
        root=root,
        capture_factory=lambda idx: cap,
        detector=detector_open,
        evaluator=evaluator,
        clock=lambda: 10.0,
        snapshots_dir=str(tmp_path),
    )

    # OPEN
    gui.update_once()
    assert gui.status_badge.cget("text") == "OPEN"

    # change detector -> CLOSED
    gui.detector = detector_closed
    gui.update_once()
    assert gui.status_badge.cget("text") == "CLOSED"

    # ALERT
    gui.update_once()
    assert gui.status_badge.cget("text") == "ALERT"

    # snapshot should work (has last_frame)
    gui.snapshot()

    gui.close()


@pytest.mark.test_id("UT_SWR_07_06")
@pytest.mark.requirement("SWR_07")
def test_gui_stop_prevents_update():
    """UT_SWR_07_06
    Stop should prevent update_once from doing work.
    """
    root = tk.Tk()
    root.withdraw()

    cap = FakeCap(opened=True)
    gui = DriverMonitoringGUI(root=root, capture_factory=lambda idx: cap)

    gui.running = False
    gui.update_once()  # should not crash or change badge
    gui.close()