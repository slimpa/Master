import numpy as np
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


def test_gui_snapshot_no_frame_message(tmp_path):
    """UT_SWR_08_02
    Snapshot grana kada nema last_frame.
    """
    root = tk.Tk()
    root.withdraw()

    gui = DriverMonitoringGUI(
        root=root,
        capture_factory=lambda idx: FakeCap(opened=True),
        snapshots_dir=str(tmp_path),
    )

    gui.last_frame = None
    gui.snapshot()
    assert "No frame" in gui.info.cget("text")

    gui.close()


def test_gui_mode_and_threshold_handlers_update_state():
    """UT_SWR_05_02
    _on_mode i _on_threshold ažuriraju internal state.
    """
    root = tk.Tk()
    root.withdraw()

    gui = DriverMonitoringGUI(root=root, capture_factory=lambda idx: FakeCap(opened=True))

    gui.mode_var.set("timed")
    gui._on_mode()
    assert gui.mode == "timed"

    gui.th_var.set(4.2)
    gui._on_threshold()
    assert abs(gui.threshold_sec - 4.2) < 0.01
    assert "4.2" in gui.th_label.cget("text")

    gui.close()


def test_gui_toggle_run_changes_button_text():
    """UT_SWR_07_07
    toggle_run mijenja running stanje i tekst dugmeta.
    """
    root = tk.Tk()
    root.withdraw()

    gui = DriverMonitoringGUI(root=root, capture_factory=lambda idx: FakeCap(opened=True))
    assert gui.running is True

    gui.toggle_run()
    assert gui.running is False
    assert gui.btn_toggle.cget("text") == "Start"

    gui.toggle_run()
    assert gui.running is True
    assert gui.btn_toggle.cget("text") == "Stop"

    gui.close()