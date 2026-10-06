from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.analytics import DirectionFlow, DwellRecord
from app.models.user import User
from app.schemas.dashboard import DirectionFlowResponse, DwellRecordResponse

router = APIRouter()

DIRECTION_LABELS = {
    "north": "Shimol",
    "south": "Janub",
    "east": "Sharq",
    "west": "G'arb",
    "northeast": "Shimoli-sharq",
    "northwest": "Shimoli-g'arb",
    "southeast": "Janubi-sharq",
    "southwest": "Janubi-g'arb",
}


@router.get("/dwell-time", response_model=list[DwellRecordResponse])
def dwell_time(
    camera_id: int | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    query = db.query(DwellRecord).filter(DwellRecord.left_at >= today)
    if camera_id:
        query = query.filter(DwellRecord.camera_id == camera_id)
    return query.order_by(DwellRecord.dwell_seconds.desc()).limit(limit).all()


@router.get("/dwell-summary")
def dwell_summary(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    rows = (
        db.query(
            DwellRecord.zone_label,
            func.avg(DwellRecord.dwell_seconds),
            func.count(DwellRecord.id),
        )
        .filter(DwellRecord.left_at >= today, DwellRecord.is_staff.is_(False))
        .group_by(DwellRecord.zone_label)
        .all()
    )
    return [
        {
            "zone": zone,
            "avg_dwell_seconds": int(avg or 0),
            "avg_dwell_minutes": round((avg or 0) / 60, 1),
            "visitors": count,
        }
        for zone, avg, count in rows
    ]


@router.get("/direction-flow", response_model=list[DirectionFlowResponse])
def direction_flow(
    camera_id: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    query = db.query(
        DirectionFlow.direction,
        func.sum(DirectionFlow.count),
    ).filter(DirectionFlow.date >= today)
    if camera_id:
        query = query.filter(DirectionFlow.camera_id == camera_id)
    rows = query.group_by(DirectionFlow.direction).all()
    return [
        DirectionFlowResponse(
            direction=direction,
            count=int(count or 0),
            label=DIRECTION_LABELS.get(direction, direction),
        )
        for direction, count in rows
    ]


@router.get("/zone-popularity")
def zone_popularity(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    since = datetime.utcnow() - timedelta(hours=24)
    rows = (
        db.query(
            DwellRecord.zone_label,
            func.count(DwellRecord.id),
            func.sum(DwellRecord.dwell_seconds),
        )
        .filter(DwellRecord.left_at >= since, DwellRecord.is_staff.is_(False))
        .group_by(DwellRecord.zone_label)
        .order_by(func.sum(DwellRecord.dwell_seconds).desc())
        .all()
    )
    return [
        {
            "zone": zone,
            "visits": visits,
            "total_dwell_minutes": round((total or 0) / 60, 1),
        }
        for zone, visits, total in rows
    ]
