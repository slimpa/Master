import cv2

FACE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
EYE_CASCADE_PATH = cv2.data.haarcascades + "haarcascade_eye.xml"

face_cascade = cv2.CascadeClassifier(FACE_CASCADE_PATH)
eye_cascade = cv2.CascadeClassifier(EYE_CASCADE_PATH)


def detect_faces_and_eyes(frame):
    """
    Detects faces and eyes in a frame.

    Returns:
        list of dicts:
        [
            {
                "face": (x, y, w, h),
                "eyes": [(ex, ey, ew, eh), ...]  # list-like
            }
        ]
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5
    )

    detections = []

    for (x, y, w, h) in faces:
        roi_gray = gray[y:y + h, x:x + w]

        eyes = eye_cascade.detectMultiScale(
            roi_gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(20, 20)
        )

        # osiguraj "list-like" za testove i GUI
        eyes_list = list(eyes) if eyes is not None else []

        detections.append({
            "face": (x, y, w, h),
            "eyes": eyes_list
        })

    return detections


def evaluate_eye_state(
    has_open_eyes,
    closed_start_time,
    current_time,
    mode="instant",
    threshold_sec=3.0,
    alert_cooldown_sec=1.0,
    last_alert_time=None
):
    """
    Returns:
        (status, closed_start_time, last_alert_time)

    status: "open" | "closed" | "alert"
    mode:
        - "instant": alert immediately if no open eyes
        - "timed": alert after threshold_sec
    """
    if has_open_eyes:
        return "open", None, last_alert_time

    if mode == "instant":
        # cooldown da ne "treperi"
        if last_alert_time is None or (current_time - last_alert_time) >= alert_cooldown_sec:
            return "alert", None, current_time
        return "alert", None, last_alert_time

    # timed mode
    if closed_start_time is None:
        return "closed", current_time, last_alert_time

    elapsed = current_time - closed_start_time
    if elapsed >= threshold_sec:
        if last_alert_time is None or (current_time - last_alert_time) >= alert_cooldown_sec:
            return "alert", closed_start_time, current_time
        return "alert", closed_start_time, last_alert_time

    return "closed", closed_start_time, last_alert_time