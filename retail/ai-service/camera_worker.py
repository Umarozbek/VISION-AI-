import threading
import time

import cv2
import httpx
import numpy as np

from analytics_engine import (
    DirectionAnalyzer,
    DwellTracker,
    LineCrossingCounter,
    zone_label_from_point,
)
from config import BACKEND_URL, DEMOGRAPHIC_INTERVAL, FRAME_SKIP, MIN_DWELL_SECONDS
from demographics import DemographicsAnalyzer
from detector import PersonDetector
from face_detector import FaceDetector
from frame_annotator import FrameAnnotator
from publisher import EventPublisher
from rtsp_reader import RTSPCapture
from webcam_reader import WebcamCapture

# Annotator uchun max o'lcham — katta frameni kichiklashtiradi
STREAM_MAX_WIDTH = 1280


STAFF_CHECKIN_COOLDOWN = 300  # soniya — bir xodim uchun qayta check-in yubormaslik
STAFF_CHECK_INTERVAL = 15     # necha frame'da bir marta yuzni qayta tekshirish


class CameraWorker(threading.Thread):
    def __init__(self, camera: dict, detector: PersonDetector, publisher: EventPublisher,
                 staff_recognizer=None):
        super().__init__(daemon=True)
        self.camera = camera
        self.detector = detector
        self.publisher = publisher
        self.staff_recognizer = staff_recognizer
        self.running = True
        self.frame_count = 0
        self.active_tracks: set[int] = set()
        self._zone_width: int = camera.get("zone_width") or 640
        self._zone_height: int = camera.get("zone_height") or 480

        height = camera.get("zone_height") or 480
        line_y = camera.get("entrance_line_y") or (height * 0.5)
        self.line_counter = LineCrossingCounter(line_y)
        self.dwell_tracker = DwellTracker(MIN_DWELL_SECONDS)
        self.direction_analyzer = DirectionAnalyzer()
        self.demographics = DemographicsAnalyzer()
        self.demo_frames: dict[int, int] = {}
        self.face_detector = FaceDetector()
        self.annotator = FrameAnnotator(camera["id"])

        # Xodim tanish — track_id bo'yicha keshlash (har frame qayta hisoblamaslik uchun)
        self.staff_match_cache: dict[int, dict | None] = {}
        self.staff_check_frames: dict[int, int] = {}
        self._last_checkin_at: dict[int, float] = {}   # staff_id -> time.time()

        # Batch publish uchun
        self._batch: list[dict] = []
        self._batch_size = 10

    @property
    def camera_id(self):
        return self.camera["id"]

    def stop(self):
        self.running = False

    def _resize_for_stream(self, frame: np.ndarray) -> np.ndarray:
        """Stream uchun frame ni kichiklashtiradi (original o'zgarmaydi)."""
        h, w = frame.shape[:2]
        if w <= STREAM_MAX_WIDTH:
            return frame
        scale = STREAM_MAX_WIDTH / w
        new_w = STREAM_MAX_WIDTH
        new_h = int(h * scale)
        return cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    def _flush_batch(self, client: httpx.Client) -> None:
        """To'plangan eventlarni batch holida yuboradi."""
        if not self._batch:
            return
        try:
            client.post(
                f"{BACKEND_URL}/analytics/events/batch",
                json=self._batch,
                headers={"X-API-Key": self.publisher.headers["X-API-Key"]},
                timeout=10.0,
            )
        except httpx.HTTPError:
            pass
        self._batch.clear()

    def run(self):
        if self.camera.get("camera_type") == "webcam":
            device_index = self.camera.get("device_index") or 0
            print(f"Camera {self.camera_id} ({self.camera['name']}): webkamera #{device_index} ulanmoqda")
            capture = WebcamCapture(device_index)
        else:
            url = self.camera.get("resolved_rtsp_url")
            if not url:
                print(f"Camera {self.camera_id}: RTSP URL yo'q")
                return
            print(f"Camera {self.camera_id} ({self.camera['name']}): ulanmoqda -> {url.split('@')[-1]}")
            capture = RTSPCapture(url)

        with httpx.Client() as client:
            self.publisher.update_status(client, self.camera_id, "connecting")

            while self.running:
                frame = capture.read()
                if frame is None:
                    self.publisher.update_status(client, self.camera_id, "error")
                    time.sleep(2)
                    continue

                self.frame_count += 1
                if self.frame_count % 30 == 0:
                    self.publisher.update_status(client, self.camera_id, "processing")

                if self.frame_count % FRAME_SKIP != 0:
                    continue

                h, w = frame.shape[:2]
                # Thread-safe: instance variable ga yoz, camera dict ga emas
                self._zone_width = w
                self._zone_height = h

                result = self.detector.track(frame)
                if result is None or result.boxes is None:
                    stream_frame = self._resize_for_stream(frame)
                    self.annotator.annotate_and_publish(stream_frame, [])
                    continue

                current_ids: set[int] = set()
                frame_detections: list[dict] = []

                for box in result.boxes:
                    if box.id is None:
                        continue
                    track_id = int(box.id.item())
                    current_ids.add(track_id)
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    conf = float(box.conf[0]) if box.conf is not None else 0.0
                    cx = (x1 + x2) / 2
                    cy = (y1 + y2) / 2

                    face_bbox = self._detect_face(frame, (x1, y1, x2, y2))

                    demo_count = self.demo_frames.get(track_id, 0)
                    demographics = self.demographics.cache.get(track_id, {})
                    if demo_count % DEMOGRAPHIC_INTERVAL == 0:
                        demographics = self.demographics.analyze(
                            frame, (x1, y1, x2, y2), track_id
                        )
                    self.demo_frames[track_id] = demo_count + 1

                    zone = zone_label_from_point(cx, cy, w, h)
                    gender = demographics.get("gender")
                    age_group = demographics.get("age_group")

                    staff_match = self._match_staff(track_id, frame, (x1, y1, x2, y2))
                    is_staff = staff_match is not None or self._detect_staff(frame, (x1, y1, x2, y2))

                    if staff_match is not None:
                        self._maybe_check_in(client, staff_match, zone)

                    # Stream annotation uchun
                    frame_detections.append({
                        "track_id": track_id,
                        "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                        "face_bbox": face_bbox,
                        "gender": gender,
                        "age_group": age_group,
                        "is_staff": is_staff,
                        "staff_name": staff_match["name"] if staff_match else None,
                        "staff_position": staff_match["work_position"] if staff_match else None,
                        "confidence": round(conf, 2),
                        "zone_label": zone,
                    })

                    payload = {
                        "camera_id": self.camera_id,
                        "track_id": track_id,
                        "event_type": "track",
                        "gender": gender,
                        "age_group": age_group,
                        "is_staff": is_staff,
                        "staff_id": staff_match["id"] if staff_match else None,
                        "staff_name": staff_match["name"] if staff_match else None,
                        "staff_position": staff_match["work_position"] if staff_match else None,
                        "confidence": round(conf, 2),
                        "x": cx,
                        "y": cy,
                        "zone_label": zone,
                    }

                    # Redis ga real-time broadcast (WebSocket uchun)
                    self.publisher.broadcast(payload)

                    # Batch ga qo'sh (HTTP uchun)
                    self._batch.append(payload)

                    if self.camera.get("is_entrance"):
                        crossing = self.line_counter.check(track_id, cy)
                        if crossing:
                            cross_payload = {**payload, "event_type": crossing}
                            self.publisher.broadcast(cross_payload)
                            self._batch.append(cross_payload)

                    direction = self.direction_analyzer.check(track_id, cx, cy)
                    if direction:
                        dir_payload = {**payload, "event_type": "direction", "direction": direction}
                        self.publisher.broadcast(dir_payload)
                        self._batch.append(dir_payload)

                    self.dwell_tracker.update(track_id, zone, demographics)

                # Batch yuborish
                if len(self._batch) >= self._batch_size:
                    self._flush_batch(client)

                # Resize qilib annotate
                stream_frame = self._resize_for_stream(frame)
                # Bbox larni ham scale qilish
                if stream_frame.shape[1] != w:
                    scale = stream_frame.shape[1] / w
                    scaled_dets = []
                    for d in frame_detections:
                        face = d["face_bbox"]
                        scaled_dets.append({
                            **d,
                            "x1": int(d["x1"] * scale),
                            "y1": int(d["y1"] * scale),
                            "x2": int(d["x2"] * scale),
                            "y2": int(d["y2"] * scale),
                            "face_bbox": [int(v * scale) for v in face] if face else None,
                        })
                    self.annotator.annotate_and_publish(stream_frame, scaled_dets)
                else:
                    self.annotator.annotate_and_publish(stream_frame, frame_detections)

                lost = self.active_tracks - current_ids
                for track_id in lost:
                    dwell = self.dwell_tracker.finalize_lost(track_id)
                    if dwell:
                        dwell_payload = {
                            "camera_id": self.camera_id,
                            "track_id": track_id,
                            "event_type": "dwell",
                            "gender": dwell.get("gender"),
                            "age_group": dwell.get("age_group"),
                            "is_staff": False,
                            "confidence": 0.0,
                            "x": 0,
                            "y": 0,
                            "zone_label": dwell["zone_label"],
                            "dwell_seconds": dwell["dwell_seconds"],
                        }
                        self._batch.append(dwell_payload)
                    self.line_counter.remove(track_id)
                    self.direction_analyzer.remove(track_id)
                    self.demographics.clear_track(track_id)
                    self.demo_frames.pop(track_id, None)
                    self.staff_match_cache.pop(track_id, None)
                    self.staff_check_frames.pop(track_id, None)

                self.active_tracks = current_ids
                # Har frame oxirida ham flush
                self._flush_batch(client)

        capture.release()
        with httpx.Client() as client:
            self.publisher.update_status(client, self.camera_id, "stopped")

    def _detect_face(self, frame, bbox) -> list[int] | None:
        """Odam bbox ichida YuNet bilan yuzni topadi va frame-koordinatalarida
        [x1, y1, x2, y2] qaytaradi. Staff/demographics'dan mustaqil — roster yoki
        boshqa modelga bog'liq emas."""
        x1, y1, x2, y2 = bbox
        crop = frame[max(0, y1):y2, max(0, x1):x2]
        if crop.size == 0:
            return None
        face = self.face_detector.detect(crop)
        if face is None:
            return None
        fx, fy, fw, fh = face
        return [x1 + fx, y1 + fy, x1 + fx + fw, y1 + fy + fh]

    def _detect_staff(self, frame, bbox) -> bool:
        x1, y1, x2, y2 = bbox
        upper = frame[y1 : y1 + int((y2 - y1) * 0.4), x1:x2]
        if upper.size == 0:
            return False
        hsv = cv2.cvtColor(upper, cv2.COLOR_BGR2HSV)
        blue_mask = cv2.inRange(hsv, (90, 50, 50), (130, 255, 255))
        blue_ratio = float(np.count_nonzero(blue_mask)) / blue_mask.size
        return blue_ratio > 0.15

    def _match_staff(self, track_id: int, frame, bbox) -> dict | None:
        """Staff Center'da yuklangan rasm bilan yuzni solishtirib xodimni tanib oladi.
        Har track uchun natija keshlanadi — har STAFF_CHECK_INTERVAL frame'da qayta tekshiriladi."""
        if not self.staff_recognizer:
            return None

        seen = self.staff_check_frames.get(track_id, 0)
        if seen % STAFF_CHECK_INTERVAL != 0 and track_id in self.staff_match_cache:
            self.staff_check_frames[track_id] = seen + 1
            return self.staff_match_cache[track_id]
        self.staff_check_frames[track_id] = seen + 1

        x1, y1, x2, y2 = bbox
        crop = frame[max(0, y1):y2, max(0, x1):x2]
        try:
            match = self.staff_recognizer.recognize(crop) if crop.size else None
        except Exception:
            match = None
        self.staff_match_cache[track_id] = match
        return match

    def _maybe_check_in(self, client: httpx.Client, staff_match: dict, zone: str) -> None:
        """Xodim o'ziga biriktirilgan ish o'rniga kirsa backendga check-in yuboradi
        (cooldown bilan — har safar emas)."""
        work_position = staff_match.get("work_position")
        if not work_position or work_position != zone:
            return

        staff_id = staff_match["id"]
        last = self._last_checkin_at.get(staff_id, 0.0)
        if time.time() - last < STAFF_CHECKIN_COOLDOWN:
            return
        self._last_checkin_at[staff_id] = time.time()

        try:
            client.post(
                f"{BACKEND_URL}/staff/internal/check-in",
                json={"staff_id": staff_id, "camera_id": self.camera_id, "zone_label": zone},
                headers={"X-API-Key": self.publisher.headers["X-API-Key"]},
                timeout=5.0,
            )
            print(f"Camera {self.camera_id}: {staff_match['name']} ish o'rniga keldi ({zone})")
        except httpx.HTTPError:
            pass