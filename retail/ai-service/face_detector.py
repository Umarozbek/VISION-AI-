"""
FaceDetector — YuNet asosida umumiy yuz ANIQLASH (detection), tanish (recognition) emas.

Bu klass StaffRecognizer'dan mustaqil ishlaydi: xodimlar ro'yxati (roster) kerak
emas, SFace embedding hisoblanmaydi — faqat "bu yerda yuz bormi va u qayerda"
degan savolga javob beradi. StaffRecognizer o'zining alohida YuNet instansiyasini
saqlashda qoladi, chunki ikkala xususiyat lifecycle bo'yicha mustaqil bo'lishi kerak
(yuz aniqlash roster sync'ga bog'liq bo'lmasligi kerak).
"""

from pathlib import Path

import cv2
import numpy as np

MODEL_DIR = Path(__file__).parent / "models"
DETECTOR_MODEL = MODEL_DIR / "face_detection_yunet_2023mar.onnx"

DETECT_INPUT_SIZE = (320, 320)
SCORE_THRESHOLD = 0.7
NMS_THRESHOLD = 0.3
TOP_K = 50


class FaceDetector:
    """Berilgan (odatda odam bbox ichidan kesilgan) rasm ichida eng katta yuzni topadi."""

    def __init__(self):
        self.enabled = DETECTOR_MODEL.exists()
        self.detector = None
        if not self.enabled:
            print("FaceDetector: YuNet modeli topilmadi — yuz aniqlash o'chirilgan")
            return
        try:
            self.detector = cv2.FaceDetectorYN_create(
                str(DETECTOR_MODEL), "", DETECT_INPUT_SIZE,
                score_threshold=SCORE_THRESHOLD, nms_threshold=NMS_THRESHOLD, top_k=TOP_K,
            )
        except Exception as exc:
            print(f"FaceDetector: modelni yuklashda xato: {exc}")
            self.enabled = False

    def detect(self, bgr_image: np.ndarray) -> tuple[int, int, int, int] | None:
        """bgr_image ichidagi eng katta yuzning (x, y, w, h) qatorini qaytaradi,
        topilmasa None."""
        if not self.enabled or bgr_image is None or bgr_image.size == 0:
            return None
        h, w = bgr_image.shape[:2]
        if h < 20 or w < 20:
            return None
        self.detector.setInputSize((w, h))
        _, faces = self.detector.detect(bgr_image)
        if faces is None or len(faces) == 0:
            return None
        best = max(faces, key=lambda f: f[2] * f[3])
        x, y, fw, fh = best[:4]
        return int(x), int(y), int(fw), int(fh)
