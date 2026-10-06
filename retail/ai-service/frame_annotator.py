"""
FrameAnnotator — detection natijalarini frame ustiga chizib,
Redis ga JPEG sifatida saqlaydi.
"""

import cv2
import numpy as np
import redis

from config import REDIS_URL

COLORS = {
    "male":    (235, 99,  72),
    "female":  (180, 75, 236),
    "unknown": (140, 140, 140),
    "staff":   (50,  200, 100),
}
FACE_COLOR = (0, 230, 255)  # person box ranglaridan ajralib turadigan sariq-zangori

FONT = cv2.FONT_HERSHEY_SIMPLEX


class FrameAnnotator:
    def __init__(self, camera_id: int, max_fps: int = 12):
        self.camera_id = camera_id
        self._redis_key = f"stream:frame:{camera_id}"
        self._ttl = 10   # 10 soniya TTL
        # decode_responses=False — binary JPEG uchun
        self._redis = redis.from_url(REDIS_URL, decode_responses=False)

    def annotate_and_publish(self, frame: np.ndarray, detections: list[dict]) -> None:
        canvas = frame.copy()
        h, w = canvas.shape[:2]

        for det in detections:
            x1 = int(det.get("x1", 0))
            y1 = int(det.get("y1", 0))
            x2 = int(det.get("x2", w))
            y2 = int(det.get("y2", h))
            track_id  = det.get("track_id", 0)
            gender    = det.get("gender") or "unknown"
            age_group = det.get("age_group") or ""
            is_staff  = det.get("is_staff", False)
            staff_name = det.get("staff_name")
            staff_position = det.get("staff_position")
            conf      = det.get("confidence", 0.0)
            zone      = det.get("zone_label", "")

            color = COLORS["staff"] if is_staff else COLORS.get(gender, COLORS["unknown"])

            cv2.rectangle(canvas, (x1, y1), (x2, y2), color, 2)

            label_parts = []
            if is_staff:
                label_parts.append(staff_name if staff_name else "XODIM")
                if staff_position:
                    label_parts.append(staff_position)
            else:
                if gender != "unknown":
                    label_parts.append(gender[:1].upper())
                if age_group:
                    label_parts.append(age_group)
            label_parts.append(f"#{track_id}")
            label = "  ".join(label_parts)

            (tw, th), _ = cv2.getTextSize(label, FONT, 0.45, 1)
            lx1, ly1 = x1, max(0, y1 - th - 6)
            lx2, ly2 = x1 + tw + 8, y1
            cv2.rectangle(canvas, (lx1, ly1), (lx2, ly2), color, cv2.FILLED)
            cv2.putText(canvas, label, (lx1 + 4, ly2 - 3),
                        FONT, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

            if conf > 0:
                cv2.putText(canvas, f"{conf:.0%}", (x2 - 38, y2 - 4),
                            FONT, 0.38, color, 1, cv2.LINE_AA)
            if zone:
                cv2.putText(canvas, zone, (x1 + 4, y2 - 4),
                            FONT, 0.35, (200, 200, 200), 1, cv2.LINE_AA)

            face_bbox = det.get("face_bbox")
            if face_bbox:
                fx1, fy1, fx2, fy2 = (int(v) for v in face_bbox)
                cv2.rectangle(canvas, (fx1, fy1), (fx2, fy2), FACE_COLOR, 1)
                cv2.putText(canvas, "FACE", (fx1, max(0, fy1 - 4)),
                            FONT, 0.35, FACE_COLOR, 1, cv2.LINE_AA)

        # CAM label
        cv2.putText(canvas, f"CAM {self.camera_id}", (8, 22),
                    FONT, 0.55, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(canvas, f"CAM {self.camera_id}", (8, 22),
                    FONT, 0.55, (220, 220, 220), 1, cv2.LINE_AA)

        # Odam soni
        person_count = sum(1 for d in detections if not d.get("is_staff"))
        staff_count  = sum(1 for d in detections if d.get("is_staff"))
        count_label  = f"Mijoz: {person_count}  Xodim: {staff_count}"
        cv2.putText(canvas, count_label, (8, h - 10),
                    FONT, 0.5, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.putText(canvas, count_label, (8, h - 10),
                    FONT, 0.5, (255, 255, 255), 1, cv2.LINE_AA)

        try:
            _, jpeg_buf = cv2.imencode(".jpg", canvas, [cv2.IMWRITE_JPEG_QUALITY, 72])
            self._redis.setex(self._redis_key, self._ttl, jpeg_buf.tobytes())
        except Exception as exc:
            print(f"FrameAnnotator Redis xato (cam {self.camera_id}): {exc}")