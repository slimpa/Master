from face_app.recognizer import evaluate_eye_state


def test_system_mode_selection_supported():
    """
    ST_SR_03_01
    Sistem mora omogućiti izbor režima detekcije (instant/timed).
    """
    r1 = evaluate_eye_state(False, None, 0, mode="instant")
    r2 = evaluate_eye_state(False, 0, 1, mode="timed")

    # kompatibilno sa 2 ili 3 return vrijednosti
    s1 = r1[0]
    s2 = r2[0]

    assert s1 == "alert"
    assert s2 in ("closed", "alert")


def test_system_threshold_effect_in_timed_mode():
    """
    ST_SR_04_01
    Sistem mora omogućiti podešavanje praga (threshold) za timed režim.
    """
    # Ako tvoja evaluate_eye_state podržava threshold parametar, testira ga.
    # Ako NE podržava, ovo je signal da trebaš dodati parametar (vidi napomenu ispod).
    try:
        r = evaluate_eye_state(False, 0, 2.0, mode="timed", threshold_sec=3.0)
        assert r[0] == "closed"
        r = evaluate_eye_state(False, 0, 3.0, mode="timed", threshold_sec=3.0)
        assert r[0] == "alert"
    except TypeError:
        # Trenutno nema threshold parametra -> treba ga dodati u recognizer.py
        # Da test bude "pravi", ovdje eksplicitno fail-amo.
        assert False, "evaluate_eye_state nema threshold_sec parametar (potrebno za SR_04)."


def test_system_visual_status_is_generated():
    """
    ST_SR_05_01
    Sistem mora prikazivati vizuelni status (OPEN/CLOSED/ALERT) u realnom vremenu.
    """
    r_open = evaluate_eye_state(True, None, 0, mode="instant")
    r_closed = evaluate_eye_state(False, 0, 1, mode="timed")

    assert r_open[0] == "open"
    assert r_closed[0] in ("closed", "alert")