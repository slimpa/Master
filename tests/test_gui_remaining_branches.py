import numpy as np
import tkinter as tk
import pytest
from face_app.gui import DriverMonitoringGUI


class FakeCap:
    def __init__(self, opened=True, frames=None, raise_on_release=False):
        self._opened = opened
        self.frames = frames or [(True, np.zeros((50, 50, 3), dtype=np.uint8))]
        self.i = 0
        self.raise_on_release = raise_on_release

    def isOpened(self):
        return self._opened

    def read(self):
        if self.i >= len(self.frames):
            return False, None
        v = self.frames[self.i]
        self.i += 1
        return v

    def release(self):
        if self.raise_on_release:
            raise RuntimeError("release failed")

    def set(self, *_):
        return True


def test_gui_update_once_no_frame_branch():
    """UT_SWR_06_05
    Pokriva NO FRAME granu u update_once().
    """
    root = tk.Tk()
    root.withdraw()

    cap = FakeCap(opened=True, frames=[(False, None)])
    gui = DriverMonitoringGUI(root=root, capture_factory=lambda idx: cap)

    gui.update_once()
    assert gui.status_badge.cget("text") == "NO FRAME"

    gui.close()


def test_gui_snapshot_imwrite_fail_branch(monkeypatch, tmp_path):
    """UT_SWR_08_04
    Pokriva snapshot granu gdje cv2.imwrite vrati False.
    """
    root = tk.Tk()
    root.withdraw()

    gui = DriverMonitoringGUI(root=root, capture_factory=lambda idx: FakeCap(opened=True), snapshots_dir=str(tmp_path))
    gui.last_frame = np.zeros((50, 50, 3), dtype=np.uint8)

    import face_app.gui as g
    monkeypatch.setattr(g.cv2, "imwrite", lambda *a, **k: False)

    gui.snapshot()
    assert "failed" in gui.info.cget("text").lower()

    gui.close()


def test_gui_close_release_exception_branch(monkeypatch):
    """UT_SWR_06_06
    Pokriva close() granu gdje cap.release() baci exception.
    """
    root = tk.Tk()
    root.withdraw()

    cap = FakeCap(opened=True, raise_on_release=True)
    gui = DriverMonitoringGUI(root=root, capture_factory=lambda idx: cap)

    # close ne smije crashovati ni ako release baci exception
    gui.close()


def test_gui_start_without_mainloop_covers_protocol_and_loop_setup(monkeypatch):
    """UT_SWR_06_07
    Pokriva start(run_mainloop=False) grane: protocol + loop scheduling.
    """
    root = tk.Tk()
    root.withdraw()

    gui = DriverMonitoringGUI(root=root, capture_factory=lambda idx: FakeCap(opened=True))

    # spriječi stvarno zakazivanje after poziva (da test bude brz i determinističan)
    called = {"protocol": False, "after": 0}

    def fake_protocol(*args, **kwargs):
        called["protocol"] = True

    def fake_after(ms, func):
        called["after"] += 1
        # ne zovi func() da ne uđe u rekurziju

    monkeypatch.setattr(gui.root, "protocol", fake_protocol)
    monkeypatch.setattr(gui.root, "after", fake_after)

    gui.start(run_mainloop=False)

    assert called["protocol"] is True
    assert called["after"] >= 1

    gui.close()