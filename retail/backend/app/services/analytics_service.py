from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.redis import get_json
from app.models.analytics import HeatmapCell, PersonEvent, StaffMember, TrafficSnapshot
from app.models.camera import Camera


def get_overview(db: Session) -> dict:
    cached = get_json("stats:overview")
    if cached:
        cached["active_cameras"] = db.query(Camera).filter(Camera.active.is_(True)).count()
        cached["staff_on_duty"] = (
            db.query(StaffMember).filter(StaffMember.is_on_duty.is_(True)).count()
        )
        return cached

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    entered = (
        db.query(func.count(PersonEvent.id))
        .filter(
            PersonEvent.event_type == "enter",
            PersonEvent.timestamp >= today,
            PersonEvent.is_staff.is_(False),
        )
        .scalar()
        or 0
    )
    exited = (
        db.query(func.count(PersonEvent.id))
        .filter(
            PersonEvent.event_type == "exit",
            PersonEvent.timestamp >= today,
            PersonEvent.is_staff.is_(False),
        )
        .scalar()
        or 0
    )
    total_detections = (
        db.query(func.count(PersonEvent.id))
        .filter(PersonEvent.timestamp >= today)
        .scalar()
        or 0
    )

    return {
        "entered": entered,
        "exited": exited,
        "inside": max(entered - exited, 0),
        "active_cameras": db.query(Camera).filter(Camera.active.is_(True)).count(),
        "total_detections": total_detections,
        "staff_on_duty": db.query(StaffMember)
        .filter(StaffMember.is_on_duty.is_(True))
        .count(),
    }


def get_gender_stats(db: Session) -> dict:
    cached = get_json("stats:gender")
    if cached:
        return cached

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    rows = (
        db.query(PersonEvent.gender, func.count(PersonEvent.id))
        .filter(
            PersonEvent.timestamp >= today,
            PersonEvent.is_staff.is_(False),
            PersonEvent.gender.isnot(None),
        )
        .group_by(PersonEvent.gender)
        .all()
    )
    total = sum(count for _, count in rows) or 1
    stats = {"male": 0.0, "female": 0.0, "unknown": 0.0}
    for gender, count in rows:
        key = gender if gender in stats else "unknown"
        stats[key] = round(count / total * 100, 1)
    return stats


def get_age_stats(db: Session) -> dict:
    cached = get_json("stats:age")
    if cached:
        return cached

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    rows = (
        db.query(PersonEvent.age_group, func.count(PersonEvent.id))
        .filter(
            PersonEvent.timestamp >= today,
            PersonEvent.is_staff.is_(False),
            PersonEvent.age_group.isnot(None),
        )
        .group_by(PersonEvent.age_group)
        .all()
    )
    total = sum(count for _, count in rows) or 1
    buckets = {"18-25": 0.0, "26-35": 0.0, "36-50": 0.0, "50+": 0.0}
    for age_group, count in rows:
        if age_group in buckets:
            buckets[age_group] = round(count / total * 100, 1)
    return buckets


def get_traffic_flow(db: Session, hours: int = 24) -> list[dict]:
    cached = get_json("stats:traffic_flow")
    if cached:
        return cached[-hours:]

    now = datetime.utcnow()
    start = now - timedelta(hours=hours)
    snapshots = (
        db.query(TrafficSnapshot)
        .filter(TrafficSnapshot.date >= start)
        .order_by(TrafficSnapshot.date.asc())
        .all()
    )

    if snapshots:
        return [
            {
                "hour": s.date.strftime("%H:00"),
                "entered": s.entered,
                "exited": s.exited,
                "inside": s.inside,
            }
            for s in snapshots
        ]

    flow = []
    for i in range(hours):
        hour_dt = start + timedelta(hours=i)
        entered = (
            db.query(func.count(PersonEvent.id))
            .filter(
                PersonEvent.event_type == "enter",
                PersonEvent.timestamp >= hour_dt,
                PersonEvent.timestamp < hour_dt + timedelta(hours=1),
                PersonEvent.is_staff.is_(False),
            )
            .scalar()
            or 0
        )
        exited = (
            db.query(func.count(PersonEvent.id))
            .filter(
                PersonEvent.event_type == "exit",
                PersonEvent.timestamp >= hour_dt,
                PersonEvent.timestamp < hour_dt + timedelta(hours=1),
                PersonEvent.is_staff.is_(False),
            )
            .scalar()
            or 0
        )
        flow.append(
            {
                "hour": hour_dt.strftime("%H:00"),
                "entered": entered,
                "exited": exited,
                "inside": max(entered - exited, 0),
            }
        )
    return flow


def get_heatmap(db: Session, camera_id: int, grid_size: int = 20) -> dict:
    cached = get_json(f"heatmap:{camera_id}")
    if cached:
        return cached

    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    cells = (
        db.query(HeatmapCell)
        .filter(
            HeatmapCell.camera_id == camera_id,
            HeatmapCell.date >= today,
        )
        .all()
    )

    if not cells:
        events = (
            db.query(PersonEvent)
            .filter(
                PersonEvent.camera_id == camera_id,
                PersonEvent.timestamp >= today,
                PersonEvent.is_staff.is_(False),
            )
            .all()
        )
        camera = db.query(Camera).filter(Camera.id == camera_id).first()
        width = camera.zone_width if camera else 640
        height = camera.zone_height if camera else 480
        cell_w = width / grid_size
        cell_h = height / grid_size
        grid: dict[tuple[int, int], float] = {}
        for event in events:
            gx = min(int(event.x / cell_w), grid_size - 1)
            gy = min(int(event.y / cell_h), grid_size - 1)
            grid[(gx, gy)] = grid.get((gx, gy), 0) + 1

        points = [{"x": x, "y": y, "intensity": v} for (x, y), v in grid.items()]
        max_intensity = max((p["intensity"] for p in points), default=1.0)
        return {
            "camera_id": camera_id,
            "grid_size": grid_size,
            "points": points,
            "max_intensity": max_intensity,
        }

    points = [{"x": c.grid_x, "y": c.grid_y, "intensity": c.intensity} for c in cells]
    max_intensity = max((p["intensity"] for p in points), default=1.0)
    return {
        "camera_id": camera_id,
        "grid_size": grid_size,
        "points": points,
        "max_intensity": max_intensity,
    }


def _query_recent_detections(db: Session, limit: int) -> list[dict]:
    """Har doim DB dan yangi ma'lumot oladi — Redis keshiga yozishdan oldin
    shu funksiya ishlatiladi (aks holda kesh o'zini o'zi takrorlab qolib ketardi)."""
    events = (
        db.query(PersonEvent, Camera.name)
        .join(Camera, Camera.id == PersonEvent.camera_id)
        .order_by(PersonEvent.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "track_id": event.track_id,
            "camera_id": event.camera_id,
            "camera_name": camera_name,
            "x": event.x,
            "y": event.y,
            "gender": event.gender,
            "age_group": event.age_group,
            "is_staff": event.is_staff,
            "event_type": event.event_type,
            "direction": event.direction,
            "zone_label": event.zone_label,
            "dwell_seconds": event.dwell_seconds,
            "timestamp": event.timestamp.isoformat(),
        }
        for event, camera_name in events
    ]


def get_recent_detections(db: Session, limit: int = 50) -> list[dict]:
    cached = get_json("detections:live")
    if cached:
        return cached[:limit]
    return _query_recent_detections(db, limit)
