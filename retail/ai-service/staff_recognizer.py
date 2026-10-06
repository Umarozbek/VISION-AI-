"""
StaffRecognizer — backendan xodimlar ro'yxati + har biriga tegishli bir nechta
referens rasmni olib, YuNet (yuz aniqlash) + SFace (128-o'lchamli deep yuz
embeddingi) bilan tanish shablonini tayyorlaydi va live frame'dagi odamlarni
xodim sifatida tanib oladi (mijoz emas).

Nega LBPH emas: LBPH shunchaki piksel tekstura gistogrammasini solishtiradi —
burchak/yorug'lik biroz o'zgarsa yoki ikki kishi tashqi ko'rinishda yaqin bo'lsa
(masalan bir xil ismli ikki xodim) osongina adashtiradi. SFace haqiqiy yuz
identifikatsiya tarmog'i bo'lib, kosinus o'xshashligi orqali ancha barqaror va
aniq moslashtiradi. Ikkalasi ham OpenCV Zoo'dan bepul (Apache-2.0) ONNX model.
"""

import os
import time
from pathlib import Path

import cv2
import httpx
import numpy as np

from config import AI_API_KEY, BACKEND_URL

MODEL_DIR = Path(__file__).parent / "models"
DETECTOR_MODEL = MODEL_DIR / "face_detection_yunet_2023mar.onnx"
RECOGNIZER_MODEL = MODEL_DIR / "face_recognition_sface_2021dec.onnx"

# SFace uchun OpenCV Zoo tavsiyasi: kosinus o'xshashligi > 0.363 bo'lsa FAR
# 0.001 darajasida bir xil shaxs deb hisoblanadi. Live-frame sharoitida
# (burchak/yorug'lik) biroz yumshoqroq threshold kerak, lekin false-match'larni
# kamaytirish uchun tavsiya etilganidan uncha pastga tushmaymiz.
# STAFF_FACE_THRESHOLD env orqali sozlash mumkin.
COSINE_THRESHOLD = float(os.getenv("STAFF_FACE_THRESHOLD", "0.42"))

# Eng yaqin ikki nomzod o'rtasidagi minimal farq — bundan kam bo'lsa (ya'ni bir
# necha xodim bir xil darajada mos kelsa, masalan bir xil ismli ikki kishi)
# noto'g'ri taxmin qilmasdan "tanilmadi" deb qaytaramiz.
AMBIGUITY_MARGIN = float(os.getenv("STAFF_FACE_MARGIN", "0.05"))

SYNC_INTERVAL = 30  # soniya
DETECT_INPUT_SIZE = (320, 320)


class StaffRecognizer:
    def __init__(self):
        self.headers = {"X-API-Key": AI_API_KEY}

        self.enabled = DETECTOR_MODEL.exists() and RECOGNIZER_MODEL.exists()
        self.detector = None
        self.recognizer = None
        if not self.enabled:
            print("StaffRecognizer: YuNet/SFace modellari topilmadi — yuz tanish o'chirilgan "
                  "(faqat forma rangi bo'yicha aniqlanadi)")
        else:
            try:
                self.detector = cv2.FaceDetectorYN_create(
                    str(DETECTOR_MODEL), "", DETECT_INPUT_SIZE,
                    score_threshold=0.7, nms_threshold=0.3, top_k=50,
                )
                self.recognizer = cv2.FaceRecognizerSF_create(str(RECOGNIZER_MODEL), "")
            except Exception as exc:
                print(f"StaffRecognizer: modellarni yuklashda xato: {exc}")
                self.enabled = False

        # staff_id -> {name, work_position, embedding, sample_count}
        self.roster: dict[int, dict] = {}
        self._trained = False
        self._last_sync = 0.0

    # ── Yuz aniqlash + tekislash + embedding ─────────────────────────────────

    def _best_face_row(self, bgr_image: np.ndarray):
        """YuNet bilan eng katta yuzni topadi va uning [x,y,w,h,...landmarks,score] qatorini qaytaradi."""
        if bgr_image is None or bgr_image.size == 0:
            return None
        h, w = bgr_image.shape[:2]
        if h < 20 or w < 20:
            return None
        self.detector.setInputSize((w, h))
        _, faces = self.detector.detect(bgr_image)
        if faces is None or len(faces) == 0:
            return None
        return max(faces, key=lambda f: f[2] * f[3])

    def _embedding(self, bgr_image: np.ndarray) -> np.ndarray | None:
        face_row = self._best_face_row(bgr_image)
        if face_row is None:
            return None
        aligned = self.recognizer.alignCrop(bgr_image, face_row)
        feature = self.recognizer.feature(aligned)
        return feature.flatten()

    @staticmethod
    def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        denom = float(np.linalg.norm(a) * np.linalg.norm(b))
        if denom == 0:
            return -1.0
        return float(np.dot(a, b) / denom)

    # ── Backend bilan sinxronizatsiya + o'qitish ────────────────────────────

    def maybe_sync(self):
        now = time.time()
        if now - self._last_sync < SYNC_INTERVAL:
            return
        self._last_sync = now
        self._sync()

    def _sync(self):
        try:
            resp = httpx.get(f"{BACKEND_URL}/staff/internal/roster", headers=self.headers, timeout=10.0)
            resp.raise_for_status()
            roster = resp.json()
        except httpx.HTTPError as exc:
            print(f"StaffRecognizer: roster olishda xato: {exc}")
            return

        if not self.enabled:
            self.roster = {m["id"]: m for m in roster}
            return

        new_roster: dict[int, dict] = {}

        with httpx.Client() as client:
            for member in roster:
                photo_ids = member.get("photo_ids") or []
                embeddings: list[np.ndarray] = []
                for photo_id in photo_ids:
                    try:
                        photo_resp = client.get(
                            f"{BACKEND_URL}/staff/internal/{member['id']}/photos/{photo_id}",
                            headers=self.headers, timeout=10.0,
                        )
                        if photo_resp.status_code != 200:
                            continue
                        arr = np.frombuffer(photo_resp.content, dtype=np.uint8)
                        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                        embedding = self._embedding(img)
                        if embedding is None:
                            print(f"StaffRecognizer: {member['name']} rasmida (#{photo_id}) yuz topilmadi")
                            continue
                        embeddings.append(embedding)
                    except Exception as exc:
                        print(f"StaffRecognizer: {member['name']} rasmini (#{photo_id}) o'qishda xato: {exc}")

                if embeddings:
                    # Bir necha rasmning o'rtacha embeddingi — burchak/yorug'lik
                    # farqlariga chidamliroq va o'xshash yuzlarni ajratishda aniqroq.
                    template = np.mean(np.stack(embeddings), axis=0)
                    new_roster[member["id"]] = {
                        "name": member["name"],
                        "work_position": member.get("work_position"),
                        "embedding": template,
                        "sample_count": len(embeddings),
                    }

        self.roster = new_roster
        self._trained = len(new_roster) > 0
        if self._trained:
            total_samples = sum(m["sample_count"] for m in new_roster.values())
            print(f"StaffRecognizer: {len(new_roster)} xodim, {total_samples} rasm bilan model tayyor")
        else:
            print("StaffRecognizer: hech bir xodimda foydalanarli rasm topilmadi")

    # ── Tanish ────────────────────────────────────────────────────────────────

    def recognize(self, person_crop_bgr: np.ndarray) -> dict | None:
        """Mos xodim topilsa {id, name, work_position} qaytaradi, aks holda None."""
        if not self.enabled or not self._trained:
            return None

        embedding = self._embedding(person_crop_bgr)
        if embedding is None:
            return None

        scored = sorted(
            (
                (self._cosine_similarity(embedding, member["embedding"]), staff_id, member)
                for staff_id, member in self.roster.items()
            ),
            key=lambda row: row[0],
            reverse=True,
        )
        if not scored:
            return None

        best_score, best_id, best_member = scored[0]
        if best_score < COSINE_THRESHOLD:
            return None

        if len(scored) > 1:
            second_score = scored[1][0]
            if best_score - second_score < AMBIGUITY_MARGIN:
                # Ikki (yoki ko'proq) xodim bir xil darajada mos — chalkashtirib
                # noto'g'ri taxmin qilgandan ko'ra "tanilmadi" deb qo'yamiz.
                return None

        return {
            "id": best_id,
            "name": best_member["name"],
            "work_position": best_member.get("work_position"),
        }
