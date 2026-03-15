import pytest
import numpy as np
from face_app.recognizer import detect_faces_and_eyes


# ===============================
# UNIT TESTS – SWR_01, SWR_02 (Recognizer)
# ===============================


@pytest.mark.requirement("SWR_01")
def test_detect_faces_and_eyes_returns_list():
    """
    UT_SWR_01_01
    Funkcija mora vratiti listu detekcija.
    """
    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = detect_faces_and_eyes(fake_frame)
    assert isinstance(detections, list)


@pytest.mark.requirement("SWR_01")
def test_detect_faces_and_eyes_handles_empty_frame():
    """
    UT_SWR_01_02
    Mora stabilno obraditi frame bez exceptiona.
    """
    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = detect_faces_and_eyes(fake_frame)
    assert detections is not None


@pytest.mark.requirement("SWR_02")
def test_each_detection_contains_required_fields():
    """
    UT_SWR_02_01
    Svaka detekcija mora sadržavati face i eyes.
    """
    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = detect_faces_and_eyes(fake_frame)

    for d in detections:
        assert "face" in d
        assert "eyes" in d
        assert isinstance(d["eyes"], list)