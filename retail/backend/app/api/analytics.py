from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import verify_ai_service
from app.core.redis import set_json
from app.db.session import get_db
from app.models.analytics import (
    DirectionFlow,
    DwellRecord,
    HeatmapCell,
    PersonEvent,
    TrafficSnapshot,
)
from app.schemas.dashboard import PersonEventCreate
from app.services.analytics_service import (
    _query_recent_detections,
    get_age_stats,
    get_gender_stats,
    get_overview,
    get_traffic_flow,
)
from app.websocket.manager import manager

router = APIRouter(dependencies=[Depends(verify_ai_service)])


def _upsert_heatmap(db: Session, camera_id: int, x: float, y: float, width: int, height: int):
    grid_size = 20
    gx = min(int(x / (width / grid_size)), grid_size - 1)
    gy = min(int(y / (height / grid_size)), grid_size - 1)
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    cell = (
        db.query(HeatmapCell)
        .filter(
            HeatmapCell.camera_id == camera_id,
            HeatmapCell.grid_x == gx,
            HeatmapCell.grid_y == gy,
            HeatmapCell.date >= today,
        )
        .first()
    )
    if cell:
        cell.intensity += 1.0
    else:
        db.add(
            HeatmapCell(
                camera_id=camera_id,
                grid_x=gx,
                grid_y=gy,
                intensity=1.0,
                date=today,
            )
        )


def _upsert_direction(db: Session, camera_id: int, direction: str):
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    row = (
        db.query(DirectionFlow)
        .filter(
            DirectionFlow.camera_id == camera_id,
            DirectionFlow.direction == direction,
            DirectionFlow.date >= today,
        )
        .first()
    )
    if row:
        row.count += 1
    else:
        db.add(
            DirectionFlow(
                camera_id=camera_id,
                direction=direction,
                count=1,
                date=today,
            )
        )


@router.post("/events")
async def ingest_event(
    payload: PersonEventCreate,
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    event = PersonEvent(
        camera_id=payload.camera_id,
        track_id=payload.track_id,
        event_type=payload.event_type,
        gender=payload.gender,
        age_group=payload.age_group,
        is_staff=payload.is_staff,
        confidence=payload.confidence,
        x=payload.x,
        y=payload.y,
        direction=payload.direction,
        dwell_seconds=payload.dwell_seconds,
        zone_label=payload.zone_label,
        timestamp=now,
    )
    db.add(event)

    if payload.event_type in ("enter", "exit"):
        hour = now.replace(minute=0, second=0, microsecond=0)
        snapshot = (
            db.query(TrafficSnapshot)
            .filter(
                TrafficSnapshot.date == hour,
                TrafficSnapshot.camera_id.is_(None),
            )
            .first()
        )
        if not snapshot:
            snapshot = TrafficSnapshot(
                camera_id=None,
                entered=0,
                exited=0,
                inside=0,
                hour=hour.hour,
                date=hour,
            )
            db.add(snapshot)

        if payload.event_type == "enter" and not payload.is_staff:
            snapshot.entered += 1
            snapshot.inside += 1
        elif payload.event_type == "exit" and not payload.is_staff:
            snapshot.exited += 1
            snapshot.inside = max(snapshot.inside - 1, 0)

    if payload.event_type == "track":
        from app.models.camera import Camera

        camera = db.query(Camera).filter(Camera.id == payload.camera_id).first()
        if camera:
            _upsert_heatmap(
                db,
                payload.camera_id,
                payload.x,
                payload.y,
                camera.zone_width,
                camera.zone_height,
            )

    if payload.event_type == "direction" and payload.direction:
        _upsert_direction(db, payload.camera_id, payload.direction)

    if payload.event_type == "dwell" and payload.dwell_seconds and payload.zone_label:
        db.add(
            DwellRecord(
                camera_id=payload.camera_id,
                track_id=payload.track_id,
                zone_label=payload.zone_label,
                dwell_seconds=payload.dwell_seconds,
                gender=payload.gender,
                age_group=payload.age_group,
                is_staff=payload.is_staff,
                entered_at=now,
                left_at=now,
            )
        )

    db.commit()

    overview = get_overview(db)
    set_json("stats:overview", overview, ex=3600)
    set_json("stats:gender", get_gender_stats(db), ex=3600)
    set_json("stats:age", get_age_stats(db), ex=3600)
    set_json("stats:traffic_flow", get_traffic_flow(db), ex=3600)
    detections = _query_recent_detections(db, 50)
    set_json("detections:live", detections, ex=60)

    await manager.broadcast(
        {
            "type": "detection",
            "data": {**payload.model_dump(), "timestamp": now.isoformat()},
        }
    )
    await manager.broadcast({"type": "overview", "data": overview})

    return {"status": "ok"}


@router.post("/events/batch")
async def ingest_events_batch(
    payloads: list[PersonEventCreate],
    db: Session = Depends(get_db),
):
    for payload in payloads:
        await ingest_event(payload, db)
    return {"status": "ok", "count": len(payloads)}
