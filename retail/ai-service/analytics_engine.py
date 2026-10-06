import math
import time
from datetime import datetime, timezone


DIRECTIONS = [
    ("east", 22.5, 67.5),
    ("northeast", 67.5, 112.5),
    ("north", 112.5, 157.5),
    ("northwest", 157.5, 202.5),
    ("west", 202.5, 247.5),
    ("southwest", 247.5, 292.5),
    ("south", 292.5, 337.5),
    ("southeast", 337.5, 360.0),
    ("southeast", 0.0, 22.5),
]


class LineCrossingCounter:
    def __init__(self, line_y: float):
        self.line_y = line_y
        self.sides: dict[int, str] = {}

    def check(self, track_id: int, cy: float) -> str | None:
        side = "above" if cy < self.line_y else "below"
        prev = self.sides.get(track_id)
        self.sides[track_id] = side
        if prev and prev != side:
            if prev == "above" and side == "below":
                return "enter"
            if prev == "below" and side == "above":
                return "exit"
        return None

    def remove(self, track_id: int):
        self.sides.pop(track_id, None)


class DwellTracker:
    def __init__(self, min_dwell_seconds: int = 5):
        self.min_dwell = min_dwell_seconds
        self.tracks: dict[int, dict] = {}

    def update(self, track_id: int, zone_label: str, demographics: dict) -> dict | None:
        now = time.time()
        if track_id not in self.tracks:
            self.tracks[track_id] = {
                "zone": zone_label,
                "started": now,
                "last_seen": now,
                "demographics": demographics,
            }
            return None

        track = self.tracks[track_id]
        track["last_seen"] = now
        track["zone"] = zone_label
        if demographics:
            track["demographics"] = demographics
        return None

    def finalize_lost(self, track_id: int) -> dict | None:
        track = self.tracks.pop(track_id, None)
        if not track:
            return None
        dwell = int(track["last_seen"] - track["started"])
        if dwell < self.min_dwell:
            return None
        return {
            "zone_label": track["zone"],
            "dwell_seconds": dwell,
            **track.get("demographics", {}),
        }


class DirectionAnalyzer:
    def __init__(self, min_distance: float = 25.0):
        self.min_distance = min_distance
        self.last_pos: dict[int, tuple[float, float]] = {}

    def _angle_to_direction(self, angle: float) -> str:
        angle = angle % 360
        for name, low, high in DIRECTIONS:
            if low <= angle < high:
                return name
        return "east"

    def check(self, track_id: int, cx: float, cy: float) -> str | None:
        prev = self.last_pos.get(track_id)
        self.last_pos[track_id] = (cx, cy)
        if not prev:
            return None

        dx = cx - prev[0]
        dy = prev[1] - cy
        dist = math.hypot(dx, dy)
        if dist < self.min_distance:
            return None

        angle = math.degrees(math.atan2(dy, dx))
        if angle < 0:
            angle += 360
        return self._angle_to_direction(angle)

    def remove(self, track_id: int):
        self.last_pos.pop(track_id, None)


def zone_label_from_point(x: float, y: float, width: int, height: int, grid: int = 4) -> str:
    col = min(int(x / (width / grid)), grid - 1)
    row = min(int(y / (height / grid)), grid - 1)
    zone_names = [
        ["A1-kirish", "A2-markaz", "A3-o'ng", "A4-chap"],
        ["B1-old", "B2-markaz", "B3-o'ng", "B4-chap"],
        ["C1-kassa", "C2-markaz", "C3-o'ng", "C4-chap"],
        ["D1-arka", "D2-markaz", "D3-o'ng", "D4-chiqish"],
    ]
    return zone_names[row][col]
