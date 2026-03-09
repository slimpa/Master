import pytest
from face_app.recognizer import evaluate_eye_state


@pytest.mark.requirement("SWR_03")
def test_instant_mode_cooldown_keeps_last_alert_time():
    """UT_SWR_03_06
    Instant mode: cooldown grana vraća isti last_alert_time.
    """
    status, start, last = evaluate_eye_state(
        has_open_eyes=False,
        closed_start_time=None,
        current_time=10.0,
        mode="instant",
        alert_cooldown_sec=5.0,
        last_alert_time=8.0
    )
    assert status == "alert"
    assert start is None
    assert last == 8.0  # još uvijek u cooldown-u


@pytest.mark.requirement("SWR_03")
def test_timed_mode_sets_start_when_none():
    """UT_SWR_03_07
    Timed mode: kada je start None, postavlja ga na current_time.
    """
    status, start, last = evaluate_eye_state(
        has_open_eyes=False,
        closed_start_time=None,
        current_time=2.0,
        mode="timed",
        threshold_sec=3.0
    )
    assert status == "closed"
    assert start == 2.0


@pytest.mark.requirement("SWR_03")
def test_timed_mode_alert_cooldown_keeps_last_alert_time():
    """UT_SWR_03_08
    Timed mode: alert cooldown grana vraća isti last_alert_time.
    """
    status, start, last = evaluate_eye_state(
        has_open_eyes=False,
        closed_start_time=0.0,
        current_time=10.0,
        mode="timed",
        threshold_sec=3.0,
        alert_cooldown_sec=10.0,
        last_alert_time=8.0
    )
    assert status == "alert"
    assert start == 0.0
    assert last == 8.0