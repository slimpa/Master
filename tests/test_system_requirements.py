import numpy as np
from face_app.recognizer import detect_faces_and_eyes, evaluate_eye_state


def test_system_sr01_real_time_monitoring_runs():
    """
    ST_SR_01_01
    SR_01: sistem mora raditi real-time monitoring bez crasha.
    """
    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = detect_faces_and_eyes(fake_frame)
    assert isinstance(detections, list)


def test_system_sr02_alert_after_3_seconds():
    """
    ST_SR_02_01
    SR_02: alert ako su oči zatvorene >= 3 sekunde (timed).
    """
    status, _, _ = evaluate_eye_state(False, 0, 3.0, mode="timed")
    assert status == "alert"


def test_system_sr02_no_alert_before_threshold():
    """
    ST_SR_02_02
    SR_02: nema alerta prije 3 sekunde (timed).
    """
    status, start, _ = evaluate_eye_state(False, 10, 12, mode="timed")
    assert status == "closed"
    assert start == 10


def test_system_sr02_reset_when_open():
    """
    ST_SR_02_03
    SR_02: kad se oči otvore, timer se resetuje.
    """
    status, start, _ = evaluate_eye_state(True, 5, 7, mode="timed")
    assert status == "open"
    assert start is None