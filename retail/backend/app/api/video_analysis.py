"""
Video Analysis API
Admin uploads a video file → YOLOv8 processes every frame →
results stored in memory (job dict) → frontend polls for progress
and fetches the final report.
"""
import math
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.deps import require_admin
from app.models.user import User

router = APIRouter()

UPLOAD_DIR = Path("video_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# In-memory job store  {job_id: {...}}
_jobs: dict[str, dict] = {}

GENDER_COLORS = {"male": (255, 100, 50), "female": (50, 100, 255), "unknown": (150, 150, 150)}
AGE_BUCKETS = ["18-25", "26-35", "36-50", "50+"]


# ─────────────────────────── helpers ───────────────────────────────────────

def _classify_age(h: int) -> str:
    if h < 130:
        return "18-25"
    if h < 160:
        return "26-35"
    if h < 185:
        return "36-50"
    return "50+"


def _classify_gender(w: int, h: int) -> str:
    ratio = w / max(h, 1)
    if ratio > 0.42:
        return "male"
    if ratio < 0.35:
        return "female"
    return "unknown"


def _draw_box(frame, x1, y1, x2, y2, track_id, gender, age):
    color = GENDER_COLORS.get(gender, (150, 150, 150))
    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
    label = f"#{track_id} {gender[0].upper()} {age}"
    (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
    cv2.rectangle(frame, (x1, y1 - th - 6), (x1 + tw + 4, y1), color, -1)
    cv2.putText(frame, label, (x1 + 2, y1 - 4),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1)


def _angle_direction(dx, dy):
    angle = math.degrees(math.atan2(-dy, dx)) % 360
    dirs = [
        (0, 22.5, "east"), (22.5, 67.5, "northeast"), (67.5, 112.5, "north"),
        (112.5, 157.5, "northwest"), (157.5, 202.5, "west"),
        (202.5, 247.5, "southwest"), (247.5, 292.5, "south"),
        (292.5, 337.5, "southeast"), (337.5, 360, "east"),
    ]
    for lo, hi, name in dirs:
        if lo <= angle < hi:
            return name
    return "east"


# ─────────────────────────── processing thread ─────────────────────────────

def _process_video(job_id: str, video_path: Path, annotated_path: Path):
    job = _jobs[job_id]
    try:
        from ultralytics import YOLO
        model = YOLO("yolov8n.pt")
    except Exception as e:
        job["status"] = "failed"
        job["error"] = f"YOLO load failed: {e}"
        return

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        job["status"] = "failed"
        job["error"] = "Cannot open video file"
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(annotated_path), fourcc, fps, (width, height))

    # accumulators
    gender_counts = {"male": 0, "female": 0, "unknown": 0}
    age_counts = {b: 0 for b in AGE_BUCKETS}
    unique_tracks: set[int] = set()
    last_pos: dict[int, tuple] = {}
    direction_counts: dict[str, int] = {}
    traffic_by_second: dict[int, int] = {}   # second → person count in frame
    heatmap = np.zeros((height, width), dtype=np.float32)

    frame_idx = 0
    skip = max(1, int(fps / 10))   # process ~10 fps regardless of source fps

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_idx += 1
        second = int(frame_idx / fps)

        if frame_idx % skip != 0:
            out.write(frame)
            continue

        try:
            results = model.track(frame, persist=True, classes=[0],
                                  conf=0.4, iou=0.5, verbose=False)
            result = results[0] if results else None
        except Exception:
            out.write(frame)
            continue

        if result is None or result.boxes is None:
            out.write(frame)
            job["processed_frames"] = frame_idx
            job["progress"] = min(99, int(frame_idx / max(total_frames, 1) * 100))
            continue

        boxes = result.boxes
        ids = boxes.id
        if ids is None:
            out.write(frame)
            continue

        people_in_frame = 0
        for box, tid in zip(boxes.xyxy.cpu().numpy(), ids.cpu().numpy().astype(int)):
            x1, y1, x2, y2 = map(int, box)
            bw, bh = x2 - x1, y2 - y1
            if bw < 10 or bh < 10:
                continue

            people_in_frame += 1
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

            # heatmap
            sx, ex = max(0, cx - 20), min(width, cx + 20)
            sy, ey = max(0, cy - 40), min(height, cy + 40)
            heatmap[sy:ey, sx:ex] += 1

            # unique people
            is_new = tid not in unique_tracks
            unique_tracks.add(tid)

            # demographics (heuristic from bbox)
            gender = _classify_gender(bw, bh)
            age = _classify_age(bh)

            if is_new:
                gender_counts[gender] += 1
                age_counts[age] += 1

            # direction
            prev = last_pos.get(tid)
            last_pos[tid] = (cx, cy)
            if prev:
                dx, dy = cx - prev[0], cy - prev[1]
                if math.hypot(dx, dy) > 20:
                    d = _angle_direction(dx, dy)
                    direction_counts[d] = direction_counts.get(d, 0) + 1

            _draw_box(frame, x1, y1, x2, y2, tid, gender, age)

        traffic_by_second[second] = max(traffic_by_second.get(second, 0), people_in_frame)

        # overlay stats on frame
        cv2.rectangle(frame, (0, 0), (220, 55), (0, 0, 0), -1)
        cv2.putText(frame, f"People: {people_in_frame}", (5, 18),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1)
        cv2.putText(frame, f"Unique: {len(unique_tracks)}", (5, 38),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 200, 255), 1)

        out.write(frame)
        job["processed_frames"] = frame_idx
        job["progress"] = min(99, int(frame_idx / max(total_frames, 1) * 100))

    cap.release()
    out.release()

    # normalise heatmap to 0-100 grid
    total = int(sum(gender_counts.values())) or 1
    gender_pct = {k: round(v / total * 100, 1) for k, v in gender_counts.items()}

    total_age = int(sum(age_counts.values())) or 1
    age_pct = {k: round(v / total_age * 100, 1) for k, v in age_counts.items()}

    # traffic timeline (group by 5-second buckets for readability)
    bucket = 5
    timeline: list[dict] = []
    if traffic_by_second:
        max_sec = max(traffic_by_second.keys())
        for s in range(0, max_sec + bucket, bucket):
            vals = [traffic_by_second.get(s + i, 0) for i in range(bucket)]
            timeline.append({
                "time": f"{s // 60:02d}:{s % 60:02d}",
                "people": max(vals),
            })

    # normalise heatmap to list of {x,y,intensity}
    hm_norm = heatmap / (heatmap.max() + 1e-6)
    hm_small = cv2.resize(hm_norm, (20, 20))
    heatmap_points = []
    for gy in range(20):
        for gx in range(20):
            v = float(hm_small[gy, gx])
            if v > 0.05:
                heatmap_points.append({"x": gx, "y": gy, "intensity": round(v, 3)})

    job.update({
        "status": "done",
        "progress": 100,
        "finished_at": datetime.utcnow().isoformat(),
        "result": {
            "total_unique_people": len(unique_tracks),
            "total_frames": total_frames,
            "duration_seconds": round(total_frames / max(fps, 1), 1),
            "fps": round(fps, 1),
            "resolution": f"{width}x{height}",
            "gender": gender_pct,
            "age": age_pct,
            "directions": direction_counts,
            "traffic_timeline": timeline,
            "heatmap": heatmap_points,
        },
    })


# ─────────────────────────── routes ────────────────────────────────────────

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    _: User = Depends(require_admin),
):
    allowed = {".mp4", ".avi", ".mov", ".mkv", ".wmv"}
    suffix = Path(file.filename or "video.mp4").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(400, f"Unsupported format. Allowed: {', '.join(allowed)}")

    job_id = str(uuid.uuid4())[:8]
    video_path = UPLOAD_DIR / f"{job_id}_input{suffix}"
    annotated_path = UPLOAD_DIR / f"{job_id}_annotated.mp4"

    content = await file.read()
    if len(content) > 500 * 1024 * 1024:   # 500 MB limit
        raise HTTPException(413, "File too large (max 500 MB)")

    video_path.write_bytes(content)

    _jobs[job_id] = {
        "job_id": job_id,
        "filename": file.filename,
        "status": "processing",
        "progress": 0,
        "processed_frames": 0,
        "started_at": datetime.utcnow().isoformat(),
        "finished_at": None,
        "result": None,
        "error": None,
        "annotated_path": str(annotated_path),
    }

    t = threading.Thread(
        target=_process_video,
        args=(job_id, video_path, annotated_path),
        daemon=True,
    )
    t.start()

    return {"job_id": job_id, "status": "processing"}


@router.get("/jobs")
def list_jobs(_: User = Depends(require_admin)):
    return [
        {k: v for k, v in job.items() if k != "annotated_path"}
        for job in sorted(_jobs.values(), key=lambda j: j["started_at"], reverse=True)
    ]


@router.get("/jobs/{job_id}")
def get_job(job_id: str, _: User = Depends(require_admin)):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {k: v for k, v in job.items() if k != "annotated_path"}


@router.get("/jobs/{job_id}/video")
def download_annotated_video(job_id: str, _: User = Depends(require_admin)):
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job["status"] != "done":
        raise HTTPException(400, "Video not ready yet")
    path = Path(job["annotated_path"])
    if not path.exists():
        raise HTTPException(404, "Annotated video file not found")
    return FileResponse(
        str(path),
        media_type="video/mp4",
        filename=f"analysis_{job_id}.mp4",
    )


@router.delete("/jobs/{job_id}")
def delete_job(job_id: str, _: User = Depends(require_admin)):
    job = _jobs.pop(job_id, None)
    if not job:
        raise HTTPException(404, "Job not found")
    for key in ("annotated_path",):
        p = Path(job.get(key, ""))
        if p.exists():
            p.unlink(missing_ok=True)
    input_files = list(UPLOAD_DIR.glob(f"{job_id}_input*"))
    for f in input_files:
        f.unlink(missing_ok=True)
    return {"deleted": job_id}
