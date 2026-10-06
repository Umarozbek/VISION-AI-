import os
import time

import cv2

from config import RTSP_TRANSPORT

MAX_RECONNECT_DELAY = 30   # maksimal kutish vaqti (soniya)


class RTSPCapture:
    def __init__(self, url: str):
        self.url = url
        self.cap = None
        self._reconnect_delay = 1.0
        self._connect()

    def _connect(self):
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = f"rtsp_transport;{RTSP_TRANSPORT}"
        if self.cap:
            self.cap.release()
        self.cap = cv2.VideoCapture(self.url, cv2.CAP_FFMPEG)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

    def read(self):
        if not self.cap or not self.cap.isOpened():
            time.sleep(self._reconnect_delay)
            # Exponential backoff — har urinishda ikki baravar kutish
            self._reconnect_delay = min(self._reconnect_delay * 2, MAX_RECONNECT_DELAY)
            self._connect()
            return None

        ok, frame = self.cap.read()
        if not ok or frame is None:
            time.sleep(0.5)
            self._connect()
            return None

        # Muvaffaqiyatli o'qildi — delay ni reset qil
        self._reconnect_delay = 1.0
        return frame

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None