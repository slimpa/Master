import numpy as np
import tkinter as tk
import pytest
from face_app.gui import DriverMonitoringGUI


class FakeCap:
    def __init__(self, opened=True):
        self._opened = opened

    def isOpened(self):
        return self._opened

    def read(self):
        return True, np.zeros((50, 50, 3), dtype=np.uint8)

    def release(self):
        pass

    # namjerno baci exception da pokrije try/except oko cap.set
    def set(self, *_):
        raise RuntimeError("set failed")


@pytest.mark.requirement("SWR_06")
def test_gui_theme_use_exception_branch(monkeypatch):
    """UT_SWR_06_02
    Pokriva try/except oko style.theme_use.
    """
    import face_app.gui as g

    root = tk.Tk()
    root.withdraw()

    # patch ttk.Style().theme_use da baci exception
    real_style = g.ttk.Style

    class BadStyle(real_style):
        def theme_use(self, *_):
            raise RuntimeError("theme failed")

    monkeypatch.setattr(g.ttk, "Style", BadStyle)

    gui = DriverMonitoringGUI(root=root, capture_factory=lambda idx: FakeCap(opened=True))
    gui.close()


@pytest.mark.requirement("SWR_06")
def test_gui_cap_set_exception_branch():
    """UT_SWR_06_03
    Pokriva try/except oko cap.set.
    """
    root = tk.Tk()
    root.withdraw()

    gui = DriverMonitoringGUI(root=root, capture_factory=lambda idx: FakeCap(opened=True))
    # samo init je dovoljan da prođe kroz cap.set try/except
    gui.close()


@pytest.mark.requirement("SWR_06")
def test_gui_close_destroy_exception_branch(monkeypatch):
    """UT_SWR_06_04
    Pokriva close() granu gdje root.destroy baci exception.
    """
    root = tk.Tk()
    root.withdraw()

    gui = DriverMonitoringGUI(root=root, capture_factory=lambda idx: FakeCap(opened=True))

    # natjeraj destroy da baci exception
    monkeypatch.setattr(gui.root, "destroy", lambda: (_ for _ in ()).throw(RuntimeError("destroy failed")))

    # close ne smije crashovati
    gui.close()


@pytest.mark.requirement("SWR_08")
def test_gui_snapshot_makedirs_exception_branch(monkeypatch, tmp_path):
    """UT_SWR_08_03
    Pokriva snapshot() granu gdje os.makedirs baci exception.
    """
    root = tk.Tk()
    root.withdraw()

    gui = DriverMonitoringGUI(root=root, capture_factory=lambda idx: FakeCap(opened=True), snapshots_dir=str(tmp_path))

    # osiguraj last_frame da snapshot uđe u makedirs granu
    gui.last_frame = np.zeros((50, 50, 3), dtype=np.uint8)

    import face_app.gui as g
    monkeypatch.setattr(g.os, "makedirs", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("mkdir failed")))

    # snapshot ne smije crashovati (info može ostati star)
    gui.snapshot()

    gui.close()