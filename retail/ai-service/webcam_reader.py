import platform
import time

import cv2

MAX_RECONNECT_DELAY = 30   # maksimal kutish vaqti (soniya)


class WebcamCapture:
    """Laptop/USB webkamera uchun — device index orqali ulanadi (RTSP emas)."""

    def __init__(self, device_index: int):
        self.device_index = device_index
        self.cap = None
        self._reconnect_delay = 1.0
        self._connect()

    def _connect(self):
        if self.cap:
            self.cap.release()
        # Windows'da CAP_DSHOW ancha tezroq va barqaror ochiladi
        backend = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY
        self.cap = cv2.VideoCapture(self.device_index, backend)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def read(self):
        if not self.cap or not self.cap.isOpened():
            time.sleep(self._reconnect_delay)
            self._reconnect_delay = min(self._reconnect_delay * 2, MAX_RECONNECT_DELAY)
            self._connect()
            return None

        ok, frame = self.cap.read()
        if not ok or frame is None:
            time.sleep(0.5)
            return None

        self._reconnect_delay = 1.0
        return frame

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None
