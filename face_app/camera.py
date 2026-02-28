import cv2


class Camera:
    def __init__(self, device_index=0, capture_factory=None):
        self.device_index = device_index
        self.capture_factory = capture_factory or cv2.VideoCapture
        self.cap = None

    def open(self):
        self.cap = self.capture_factory(self.device_index)
        if not self.cap or not self.cap.isOpened():
            self.release()
            raise RuntimeError("Camera not accessible")

    def read(self):
        if self.cap is None:
            raise RuntimeError("Camera not opened")

        ret, frame = self.cap.read()
        if not ret or frame is None:
            raise RuntimeError("Failed to capture frame")
        return frame

    def release(self):
        if self.cap is not None:
            try:
                self.cap.release()
            finally:
                self.cap = None


def get_frame():
    """
    Captures a single frame from default camera.
    """
    cam = Camera(0)
    cam.open()
    try:
        return cam.read()
    finally:
        cam.release()