from datetime import datetime

from sqlalchemy.orm import Session

from app.models.camera import Camera
from app.utils.rtsp import build_rtsp_url


def serialize_camera(camera: Camera, include_password: bool = False) -> dict:
    if camera.camera_type == "webcam":
        device_index = camera.device_index if camera.device_index is not None else 0
        preview = f"Laptop webcam (device #{device_index})"
        resolved = f"webcam:{device_index}"
    else:
        preview = build_rtsp_url(
            camera.ip_address,
            camera.port,
            camera.username,
            None,
            camera.stream_path,
            camera.rtsp_url,
        )
        resolved = build_rtsp_url(
            camera.ip_address,
            camera.port,
            camera.username,
            camera.password,
            camera.stream_path,
            camera.rtsp_url,
        )

    data = {
        "id": camera.id,
        "name": camera.name,
        "location": camera.location,
        "camera_type": camera.camera_type,
        "device_index": camera.device_index,
        "ip_address": camera.ip_address,
        "port": camera.port,
        "username": camera.username,
        "stream_path": camera.stream_path,
        "rtsp_url": camera.rtsp_url,
        "active": camera.active,
        "is_entrance": camera.is_entrance,
        "zone_width": camera.zone_width,
        "zone_height": camera.zone_height,
        "entrance_line_y": camera.entrance_line_y,
        "processing_status": camera.processing_status,
        "last_frame_at": camera.last_frame_at,
        "created_at": camera.created_at,
        "connection_url_preview": preview,
        "resolved_rtsp_url": resolved,
    }
    if include_password:
        data["password"] = camera.password
    return data


def update_camera_status(
    db: Session,
    camera_id: int,
    status: str,
    last_frame_at: datetime | None = None,
) -> None:
    camera = db.query(Camera).filter(Camera.id == camera_id).first()
    if not camera:
        return
    camera.processing_status = status
    if last_frame_at:
        camera.last_frame_at = last_frame_at
    db.commit()
