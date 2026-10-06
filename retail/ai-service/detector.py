import numpy as np
from ultralytics import YOLO

from config import YOLO_MODEL


class PersonDetector:
    def __init__(self):
        self.model = YOLO(YOLO_MODEL)

    def track(self, frame: np.ndarray):
        results = self.model.track(
            frame,
            persist=True,
            classes=[0],
            conf=0.45,
            iou=0.5,
            verbose=False,
        )
        return results[0] if results else None
