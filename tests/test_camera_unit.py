import numpy as np
import pytest
from face_app.camera import Camera, get_frame


class FakeCap:
    def __init__(self, opened=True, ret=True, frame=None):
        self._opened = opened
        self._ret = ret
        self._frame = frame if frame is not None else np.zeros((10, 10, 3), dtype=np.uint8)
        self.released = False

    def isOpened(self):
        return self._opened

    def read(self):
        return self._ret, self._frame

    def release(self):
        self.released = True


@pytest.mark.requirement("SWR_07")
def test_camera_open_read_release_ok():
    """UT_SWR_07_02
    Camera backend must open, read and release.
    """
    cam = Camera(0, capture_factory=lambda idx: FakeCap(opened=True, ret=True))
    cam.open()
    frame = cam.read()
    assert frame is not None
    cam.release()
    assert cam.cap is None


@pytest.mark.requirement("SWR_07")
def test_camera_open_fail_raises():
    """UT_SWR_07_03
    Camera must raise if not accessible.
    """
    cam = Camera(0, capture_factory=lambda idx: FakeCap(opened=False))
    with pytest.raises(RuntimeError):
        cam.open()


@pytest.mark.requirement("SWR_07")
def test_camera_read_fail_raises():
    """UT_SWR_07_04
    Camera must raise if frame cannot be captured.
    """
    cam = Camera(0, capture_factory=lambda idx: FakeCap(opened=True, ret=False, frame=None))
    cam.open()
    with pytest.raises(RuntimeError):
        cam.read()
    cam.release()


@pytest.mark.requirement("SWR_07")
def test_get_frame_uses_camera_class(monkeypatch):
    """UT_SWR_07_05
    get_frame returns frame and releases camera.
    """
    import face_app.camera as cam_mod

    def factory(idx):
        return FakeCap(opened=True, ret=True)

    # patch cv2.VideoCapture used inside Camera default path
    monkeypatch.setattr(cam_mod.cv2, "VideoCapture", factory)

    frame = get_frame()
    assert frame is not None

@pytest.mark.requirement("SWR_07")
def test_camera_release_when_none_does_not_crash():
    """UT_SWR_07_08
    release() kad je cap None ne smije crashovati.
    """
    from face_app.camera import Camera
    cam = Camera(0, capture_factory=lambda idx: None)
    cam.release()
    assert cam.cap is None

@pytest.mark.requirement("SWR_07")
def test_camera_open_when_factory_returns_none_hits_not_cap_branch():
    """UT_SWR_07_09
    Pokriva granu: cap je None -> Camera not accessible.
    """
    cam = Camera(0, capture_factory=lambda idx: None)
    with pytest.raises(RuntimeError):
        cam.open()
