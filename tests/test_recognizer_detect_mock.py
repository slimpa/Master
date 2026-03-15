import pytest
import numpy as np
import face_app.recognizer as rec


@pytest.mark.test_id("UT_SWR_01_03")
@pytest.mark.requirement("SWR_01")
def test_detect_faces_and_eyes_executes_face_and_eye_loops(monkeypatch):
    """UT_SWR_01_03
    Pokriva grane u detect_faces_and_eyes: face loop + eyes loop.
    """
    # Fake cascades: 1 face, 2 eyes
    class FakeFaceCascade:
        def detectMultiScale(self, gray, scaleFactor=1.3, minNeighbors=5):
            return [(10, 20, 30, 40)]

    class FakeEyeCascade:
        def detectMultiScale(self, roi_gray, scaleFactor=1.1, minNeighbors=5, minSize=(20, 20)):
            return [(1, 2, 3, 4), (5, 6, 7, 8)]

    monkeypatch.setattr(rec, "face_cascade", FakeFaceCascade())
    monkeypatch.setattr(rec, "eye_cascade", FakeEyeCascade())

    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    det = rec.detect_faces_and_eyes(frame)

    assert isinstance(det, list)
    assert len(det) == 1
    assert det[0]["face"] == (10, 20, 30, 40)
    assert len(det[0]["eyes"]) == 2