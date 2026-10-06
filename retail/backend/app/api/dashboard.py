from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.dashboard import (
    AgeStats,
    GenderStats,
    HeatmapResponse,
    OverviewResponse,
    RealtimeDetection,
    TrafficFlowPoint,
)
from app.services.analytics_service import (
    get_age_stats,
    get_gender_stats,
    get_heatmap,
    get_overview,
    get_recent_detections,
    get_traffic_flow,
)

router = APIRouter()


@router.get("/overview", response_model=OverviewResponse)
def overview(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_overview(db)


@router.get("/gender", response_model=GenderStats)
def gender_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_gender_stats(db)


@router.get("/age")
def age_stats(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_age_stats(db)


@router.get("/traffic-flow", response_model=list[TrafficFlowPoint])
def traffic_flow(
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_traffic_flow(db, hours)


@router.get("/realtime", response_model=list[RealtimeDetection])
def realtime(
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_recent_detections(db, limit)


@router.get("/heatmap/{camera_id}", response_model=HeatmapResponse)
def heatmap(
    camera_id: int,
    grid_size: int = Query(default=20, ge=5, le=50),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return get_heatmap(db, camera_id, grid_size)
