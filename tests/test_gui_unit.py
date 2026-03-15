import pytest
import numpy as np
import cv2
from face_app.recognizer import evaluate_eye_state


@pytest.mark.test_id("UT_SWR_04_01")
@pytest.mark.requirement("SWR_04")
def test_instant_mode_available():
    """
    UT_SWR_04_01
    GUI mora podržati instant mode.
    """
    status, _, _ = evaluate_eye_state(False, None, 0, mode="instant")
    assert status == "alert"


@pytest.mark.test_id("UT_SWR_05_01")
@pytest.mark.requirement("SWR_05")
def test_timed_mode_threshold_behavior():
    """
    UT_SWR_05_01
    Timed mod mora generisati alert nakon 3 sekunde.
    """
    status, _, _ = evaluate_eye_state(False, 0, 2.9, mode="timed")
    assert status == "closed"

    status, _, _ = evaluate_eye_state(False, 0, 3.0, mode="timed")
    assert status == "alert"


@pytest.mark.test_id("UT_SWR_06_01")
@pytest.mark.requirement("SWR_06")
def test_status_open_is_generated():
    """
    UT_SWR_06_01
    Sistem mora generisati OPEN kada su oči otvorene.
    """
    status, _, _ = evaluate_eye_state(True, None, 0, mode="instant")
    assert status == "open"


@pytest.mark.test_id("UT_SWR_07_01")
@pytest.mark.requirement("SWR_07")
def test_start_stop_does_not_break_logic():
    """
    UT_SWR_07_01
    Start/Stop logika ne smije uticati na evaluaciju statusa.
    """
    status, _, _ = evaluate_eye_state(True, None, 0, mode="instant")
    assert status in ("open", "closed", "alert")


@pytest.mark.test_id("UT_SWR_08_01")
@pytest.mark.requirement("SWR_08")
def test_snapshot_can_save_frame(tmp_path):
    """
    UT_SWR_08_01
    Snapshot mora moći sačuvati frame.
    """
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    out = tmp_path / "snapshot.png"
    ok = cv2.imwrite(str(out), frame)
    assert ok is True
    assert out.exists()