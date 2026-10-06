import asyncio
from datetime import datetime
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, verify_ai_service
from app.core.redis import redis_client
from app.core.stream_auth import get_stream_user
from app.db.session import get_db
from app.models.camera import Camera
from app.models.user import User
from app.schemas.camera import (
    CameraCreate,
    CameraInternalResponse,
    CameraResponse,
    CameraStatusUpdate,
    CameraTestRequest,
    CameraUpdate,
)
from app.services.camera_service import serialize_camera, update_camera_status
from app.utils.rtsp import build_rtsp_url

router = APIRouter()


# ── Kamera CRUD ──────────────────────────────────────────────────────────────

@router.get("/", response_model=list[CameraResponse])
def get_cameras(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    cameras = db.query(Camera).order_by(Camera.id.asc()).all()
    return [CameraResponse(**serialize_camera(c)) for c in cameras]


@router.get("/internal/active", response_model=list[CameraInternalResponse])
def get_active_cameras_internal(
    db: Session = Depends(get_db),
    _: None = Depends(verify_ai_service),
):
    cameras = (
        db.query(Camera)
        .filter(Camera.active.is_(True))
        .order_by(Camera.id.asc())
        .all()
    )
    return [CameraInternalResponse(**serialize_camera(c, include_password=True)) for c in cameras]


@router.get("/{camera_id}", response_model=CameraResponse)
def get_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    return CameraResponse(**serialize_camera(camera))


@router.post("/", response_model=CameraResponse)
def create_camera(
    payload: CameraCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    data = payload.model_dump()
    if data.get("camera_type") == "webcam":
        if data.get("device_index") is None:
            data["device_index"] = 0
    elif not data.get("rtsp_url"):
        data["rtsp_url"] = build_rtsp_url(
            data.get("ip_address"),
            data.get("port", 554),
            data.get("username"),
            data.get("password"),
            data.get("stream_path"),
        )
    camera = Camera(**data, processing_status="pending")
    db.add(camera)
    db.commit()
    db.refresh(camera)
    return CameraResponse(**serialize_camera(camera))


@router.patch("/{camera_id}", response_model=CameraResponse)
def update_camera(
    camera_id: int,
    payload: CameraUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(camera, key, value)

    if camera.camera_type != "webcam" and any(
        k in updates for k in ("ip_address", "port", "username", "password", "stream_path")
    ):
        camera.rtsp_url = build_rtsp_url(
            camera.ip_address,
            camera.port,
            camera.username,
            camera.password,
            camera.stream_path,
            camera.rtsp_url if "rtsp_url" not in updates else updates.get("rtsp_url"),
        )

    db.commit()
    db.refresh(camera)
    return CameraResponse(**serialize_camera(camera))


@router.post("/test-connection")
def test_connection(
    payload: CameraTestRequest,
    _: User = Depends(get_current_user),
):
    if payload.camera_type == "webcam":
        device_index = payload.device_index if payload.device_index is not None else 0
        label = f"webcam #{device_index}"
        try:
            import platform

            import cv2

            backend = cv2.CAP_DSHOW if platform.system() == "Windows" else cv2.CAP_ANY
            cap = cv2.VideoCapture(device_index, backend)
            ok, frame = cap.read()
            cap.release()
            if not ok or frame is None:
                return {"success": False, "message": "Webkameraga ulanib bo'lmadi", "url": label}
            h, w = frame.shape[:2]
            return {
                "success": True,
                "message": f"Ulandi! Ruxsat: {w}x{h}",
                "url": label,
                "width": w,
                "height": h,
            }
        except Exception as exc:
            return {"success": False, "message": str(exc), "url": label}

    url = build_rtsp_url(
        payload.ip_address,
        payload.port,
        payload.username,
        payload.password,
        payload.stream_path,
        payload.rtsp_url,
    )
    if not url:
        raise HTTPException(status_code=400, detail="Kamera ma'lumotlari yetarli emas")

    try:
        import cv2

        cap = cv2.VideoCapture(url, cv2.CAP_FFMPEG)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        ok, frame = cap.read()
        cap.release()
        if not ok or frame is None:
            return {"success": False, "message": "Kamera javob bermadi", "url": url.split("@")[-1]}
        h, w = frame.shape[:2]
        return {
            "success": True,
            "message": f"Ulandi! Ruxsat: {w}x{h}",
            "url": url.split("@")[-1],
            "width": w,
            "height": h,
        }
    except Exception as exc:
        return {"success": False, "message": str(exc), "url": url.split("@")[-1]}


@router.patch("/{camera_id}/status")
def update_status(
    camera_id: int,
    payload: CameraStatusUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_ai_service),
):
    update_camera_status(db, camera_id, payload.processing_status, payload.last_frame_at)
    return {"status": "ok"}


@router.delete("/{camera_id}")
def delete_camera(
    camera_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    from app.models.analytics import (
        DirectionFlow, DwellRecord, HeatmapCell, PersonEvent, TrafficSnapshot,
    )
    db.query(PersonEvent).filter(PersonEvent.camera_id == camera_id).delete()
    db.query(HeatmapCell).filter(HeatmapCell.camera_id == camera_id).delete()
    db.query(DirectionFlow).filter(DirectionFlow.camera_id == camera_id).delete()
    db.query(DwellRecord).filter(DwellRecord.camera_id == camera_id).delete()
    db.query(TrafficSnapshot).filter(TrafficSnapshot.camera_id == camera_id).delete()
    db.delete(camera)
    db.commit()
    return {"message": "deleted"}


# ── MJPEG Stream va Snapshot ─────────────────────────────────────────────────

def _placeholder_jpeg() -> bytes:
    """Kamera tayyor bo'lmasa ko'rsatiladigan qora ekran JPEG."""
    try:
        import cv2
        import numpy as np

        img = np.zeros((360, 640, 3), dtype=np.uint8)
        cv2.putText(img, "Stream yuklanmoqda...", (170, 190),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (80, 80, 80), 2)
        _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 60])
        return buf.tobytes()
    except Exception:
        return b""


async def _mjpeg_generator(camera_id: int, fps: int) -> AsyncGenerator[bytes, None]:
    """Redis dan annotated frame larni o'qib MJPEG boundary bilan yuboradi."""
    interval = 1.0 / max(fps, 1)
    redis_key = f"stream:frame:{camera_id}"
    placeholder = _placeholder_jpeg()

    import redis as _rl
    try:
        _r = _rl.from_url(settings.REDIS_URL, decode_responses=False)
        _r.ping()
    except Exception:
        _r = None

    while True:
        await asyncio.sleep(interval)

        frame_bytes = None
        if _r:
            try:
                loop = asyncio.get_event_loop()
                frame_bytes = await loop.run_in_executor(None, _r.get, redis_key)
            except Exception:
                pass

        if not frame_bytes:
            frame_bytes = placeholder
        if not frame_bytes:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes
            + b"\r\n"
        )


@router.get("/{camera_id}/stream")
async def camera_mjpeg_stream(
    camera_id: int,
    fps: int = Query(default=10, ge=1, le=25),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_stream_user),   # header + query param token
):
    """
    Kamera annotated MJPEG stream.
    frame_annotator.py tomonidan Redis ga yozilgan JPEG larni uzatadi.
    Frontend: <img src="/cameras/{id}/stream?fps=12" />
    """
    # Kamera mavjudligini tekshirish
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")
    if not camera.active:
        raise HTTPException(status_code=400, detail="Kamera faol emas")

    return StreamingResponse(
        _mjpeg_generator(camera_id, fps),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma":         "no-cache",
            "X-Accel-Buffering": "no",   # nginx buffering o'chirish
        },
    )


@router.get("/{camera_id}/snapshot")
async def camera_snapshot(
    camera_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_stream_user),
):
    """Oxirgi annotated frame ni JPEG sifatida qaytaradi (thumbnail uchun)."""
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    frame_bytes = None
    try:
        import redis as redis_lib
        r = redis_lib.from_url(settings.REDIS_URL, decode_responses=False)
        loop = asyncio.get_event_loop()
        frame_bytes = await loop.run_in_executor(
            None, r.get, f"stream:frame:{camera_id}"
        )
    except Exception:
        pass
    if not frame_bytes:
        frame_bytes = _placeholder_jpeg()
    if not frame_bytes:
        raise HTTPException(status_code=404, detail="Frame hali mavjud emas")

    return Response(
        content=frame_bytes,
        media_type="image/jpeg",
        headers={"Cache-Control": "no-cache"},
    )