import time

import httpx

from camera_worker import CameraWorker
from config import AI_API_KEY, BACKEND_URL, CAMERA_POLL_INTERVAL
from detector import PersonDetector
from publisher import EventPublisher
from staff_recognizer import StaffRecognizer


class CameraManager:
    def __init__(self):
        self.workers: dict[int, CameraWorker] = {}
        self.detector = PersonDetector()
        self.publisher = EventPublisher()
        self.staff_recognizer = StaffRecognizer()
        self.headers = {"X-API-Key": AI_API_KEY}

    def _fetch_cameras(self) -> list[dict]:
        try:
            response = httpx.get(
                f"{BACKEND_URL}/cameras/internal/active",
                headers=self.headers,
                timeout=10.0,
            )
            response.raise_for_status()
            cameras = response.json()
            return [c for c in cameras if c.get("resolved_rtsp_url")]
        except httpx.HTTPError as exc:
            print(f"Kameralarni olishda xato: {exc}")
            return []

    def sync(self):
        self.staff_recognizer.maybe_sync()

        cameras = self._fetch_cameras()
        active_ids = {c["id"] for c in cameras}

        for cam_id in list(self.workers.keys()):
            if cam_id not in active_ids:
                print(f"Camera {cam_id}: to'xtatilmoqda")
                self.workers[cam_id].stop()
                del self.workers[cam_id]

        for camera in cameras:
            cam_id = camera["id"]
            if cam_id not in self.workers:
                print(f"Camera {cam_id}: ishga tushirilmoqda ({camera['name']})")
                worker = CameraWorker(camera, self.detector, self.publisher, self.staff_recognizer)
                self.workers[cam_id] = worker
                worker.start()

    def run_forever(self):
        print("AI Camera Manager ishga tushdi — backend dan kameralar olinadi")
        while True:
            self.sync()
            time.sleep(CAMERA_POLL_INTERVAL)
