import cv2
import numpy as np
import os

AGE_BUCKETS = [(0, 25, "18-25"), (26, 35, "26-35"), (36, 50, "36-50"), (51, 120, "50+")]

BASE_DIR = os.path.dirname(__file__)
MODEL_DIR = os.path.join(BASE_DIR, "models")
PROTO_DIR = os.path.join(BASE_DIR, "model_defs")


class DemographicsAnalyzer:
    def __init__(self):
        self.age_net = None
        self.gender_net = None
        self.cache: dict[int, dict] = {}
        self._face_detector = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        self._load_models()

    def _load_models(self):
        try:
            age_proto   = f"{PROTO_DIR}/age_deploy.prototxt"
            age_model   = f"{MODEL_DIR}/age_net.caffemodel"
            gender_proto = f"{PROTO_DIR}/gender_deploy.prototxt"
            gender_model = f"{MODEL_DIR}/gender_net.caffemodel"

            if all(os.path.exists(p) for p in [age_proto, age_model, gender_proto, gender_model]):
                self.age_net    = cv2.dnn.readNet(age_model, age_proto)
                self.gender_net = cv2.dnn.readNet(gender_model, gender_proto)
                print("Demographics modellari yuklandi")
            else:
                print("Demographics modellari topilmadi — None qaytariladi")
        except Exception as exc:
            print(f"Demographics models not loaded: {exc}")

    def _find_face(self, person_crop: np.ndarray) -> np.ndarray | None:
        """Odam bbox ichidan aynan yuzni topadi — shu orqali gender/age modeliga
        butun gavda emas, faqat yuz beriladi (model tor yuz kroplarida o'qitilgan)."""
        if person_crop is None or person_crop.size == 0:
            return None
        gray = cv2.cvtColor(person_crop, cv2.COLOR_BGR2GRAY)
        faces = self._face_detector.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
        )
        if len(faces) == 0:
            return None
        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
        # Yuz atrofida озgina margin qoldiramiz — peshona/iyak kesilib qolmasin
        pad_x, pad_y = int(w * 0.15), int(h * 0.15)
        ph, pw = person_crop.shape[:2]
        fx1, fy1 = max(0, x - pad_x), max(0, y - pad_y)
        fx2, fy2 = min(pw, x + w + pad_x), min(ph, y + h + pad_y)
        return person_crop[fy1:fy2, fx1:fx2]

    def _preprocess_face(self, crop: np.ndarray):
        if crop is None or crop.size == 0:
            return None
        h, w = crop.shape[:2]
        if h < 40 or w < 40:
            return None
        face = cv2.resize(crop, (227, 227))
        blob = cv2.dnn.blobFromImage(
            face, scalefactor=1.0, size=(227, 227),
            mean=(78.4263377603, 87.7689143744, 114.895847746),
            swapRB=False,
        )
        return blob

    def analyze(self, frame: np.ndarray, bbox: tuple, track_id: int) -> dict:
        if track_id in self.cache:
            return self.cache[track_id]

        x1, y1, x2, y2 = bbox
        crop = frame[max(0, y1):y2, max(0, x1):x2]
        if crop.size == 0:
            return {}

        gender = None
        age_group = None

        if self.age_net and self.gender_net:
            face = self._find_face(crop)
            blob = self._preprocess_face(face) if face is not None else None
            if blob is not None:
                try:
                    self.gender_net.setInput(blob)
                    gender_idx = int(self.gender_net.forward().argmax())
                    gender = "male" if gender_idx == 0 else "female"

                    self.age_net.setInput(blob)
                    age_idx = int(self.age_net.forward().argmax())
                    age_ranges = ["18-25", "26-35", "36-50", "50+"]
                    age_group = age_ranges[min(age_idx, len(age_ranges) - 1)]
                except Exception:
                    pass  # model xato bersa None qaytariladi
        # Fallback YO'Q — model bo'lmasa None qaytariladi (noto'g'ri ma'lumot bermaslik)

        result = {"gender": gender, "age_group": age_group}
        self.cache[track_id] = result
        return result

    def clear_track(self, track_id: int):
        self.cache.pop(track_id, None)