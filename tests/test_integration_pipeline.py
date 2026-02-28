import numpy as np
from face_app.recognizer import detect_faces_and_eyes, evaluate_eye_state


def _has_open_eyes_from_detections(detections):
    if not detections:
        return False
    for d in detections:
        eyes = d.get("eyes", [])
        try:
            return len(eyes) > 0
        except Exception:
            pass
    return False


def test_face_eye_pipeline_runs_end_to_end():
    """
    IT_SYS_01_01
    Integracija: detect_faces_and_eyes + evaluate_eye_state ne smije crashovati.
    """
    fake_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    detections = detect_faces_and_eyes(fake_frame)

    assert detections is not None
    assert isinstance(detections, list)

    has_open = _has_open_eyes_from_detections(detections)

    status, start, _ = evaluate_eye_state(has_open, None, 1, mode="instant")
    assert status in ("open", "closed", "alert")
    assert start is None


def test_sys02_face_without_eyes_is_closed():
    """
    IT_SYS_02_01
    Ako postoji lice bez očiju, tretira se kao zatvorene oči.
    """
    detections = [{"face": (0, 0, 100, 100), "eyes": []}]
    has_open = _has_open_eyes_from_detections(detections)
    assert has_open is False


def test_sys03_alert_after_threshold():
    """
    IT_SYS_03_01
    Generiše alert nakon praga u timed modu.
    """
    status, _, _ = evaluate_eye_state(False, 0, 4, mode="timed")
    assert status == "alert"


def test_monitoring_loop_triggers_alert():
    """
    IT_SYS_01_02
    Petlja kroz vrijeme: zatvorene oči -> alert nakon praga.
    """
    closed_start = None
    last_alert = None
    status = None

    for t in range(0, 5):
        status, closed_start, last_alert = evaluate_eye_state(False, closed_start, t, mode="timed")

    assert status == "alert"


def test_monitoring_loop_open_resets_timer():
    """
    IT_SYS_01_03
    Ako se oči otvore prije praga, timer se resetuje.
    """
    closed_start = None
    last_alert = None

    for t in range(0, 2):
        status, closed_start, last_alert = evaluate_eye_state(False, closed_start, t, mode="timed")
        assert status in ("closed", "alert")

    status, closed_start, last_alert = evaluate_eye_state(True, closed_start, 2, mode="timed")
    assert status == "open"
    assert closed_start is None


def test_time_tracking_logic():
    """
    IT_SYS_04_01
    Sistem mora pratiti trajanje zatvorenih očiju.
    """
    status, start, _ = evaluate_eye_state(
        has_open_eyes=False,
        closed_start_time=0,
        current_time=4,
        mode="timed"
    )
    assert status == "alert"
    assert start == 0


def test_mode_switching():
    """
    IT_SYS_05_01
    Sistem mora podržavati prebacivanje između modova.
    """
    status1, _, _ = evaluate_eye_state(False, None, 0, mode="instant")
    status2, start2, _ = evaluate_eye_state(False, 0, 1, mode="timed")

    assert status1 == "alert"
    assert status2 in ("closed", "alert")
    assert start2 == 0


def test_threshold_integration():
    """
    IT_SYS_06_01
    Sistem mora primjenjivati vremenski prag.
    """
    status, _, _ = evaluate_eye_state(False, 0, 2, mode="timed")
    assert status == "closed"

    status, _, _ = evaluate_eye_state(False, 0, 4, mode="timed")
    assert status == "alert"


def test_visual_feedback_integration():
    """
    IT_SYS_07_01
    Sistem mora generisati validan status string.
    """
    status, _, _ = evaluate_eye_state(True, None, 0, mode="instant")
    assert status in ("open", "closed", "alert")