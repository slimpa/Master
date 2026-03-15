import pytest
from face_app.recognizer import evaluate_eye_state


@pytest.mark.test_id("UT_SWR_03_01")
@pytest.mark.requirement("SWR_03")
def test_instant_mode_alert_when_closed():
    """UT_SWR_03_01
    Instant mod odmah generiše alert kada su oči zatvorene.
    """
    status, start_time, last_alert = evaluate_eye_state(False, None, 10, mode="instant")
    assert status == "alert"
    assert start_time is None


@pytest.mark.test_id("UT_SWR_03_02")
@pytest.mark.requirement("SWR_03")
def test_instant_mode_open_when_open():
    """UT_SWR_03_02
    Instant mod vraća open kada su oči otvorene.
    """
    status, start_time, last_alert = evaluate_eye_state(True, None, 10, mode="instant")
    assert status == "open"
    assert start_time is None


@pytest.mark.test_id("UT_SWR_03_03")
@pytest.mark.requirement("SWR_03")
def test_timed_mode_no_alert_before_threshold():
    """UT_SWR_03_03
    Timed mod ne smije generisati alert prije 3 sekunde.
    """
    status, start_time, last_alert = evaluate_eye_state(False, 5, 7, mode="timed")
    assert status == "closed"
    assert start_time == 5


@pytest.mark.test_id("UT_SWR_03_04")
@pytest.mark.requirement("SWR_03")
def test_timed_mode_alert_at_threshold():
    """UT_SWR_03_04
    Timed mod mora generisati alert kada su oči zatvorene >= 3 sekunde.
    """
    status, _, last_alert = evaluate_eye_state(False, 5, 8, mode="timed")  # 3s tačno
    assert status == "alert"


@pytest.mark.test_id("UT_SWR_03_05")
@pytest.mark.requirement("SWR_03")
def test_timed_mode_resets_when_open():
    """UT_SWR_03_05
    Ako se oči otvore, timer se mora resetovati.
    """
    status, start_time, last_alert = evaluate_eye_state(True, 5, 9, mode="timed")
    assert status == "open"
    assert start_time is None