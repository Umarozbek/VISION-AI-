from datetime import datetime

from pydantic import BaseModel, Field


class OverviewResponse(BaseModel):
    entered: int
    exited: int
    inside: int
    active_cameras: int
    total_detections: int
    staff_on_duty: int


class GenderStats(BaseModel):
    male: float
    female: float
    unknown: float = 0.0


class AgeStats(BaseModel):
    age_18_25: float = Field(alias="18-25")
    age_26_35: float = Field(alias="26-35")
    age_36_50: float = Field(alias="36-50")
    age_50_plus: float = Field(alias="50+")

    model_config = {"populate_by_name": True}


class TrafficFlowPoint(BaseModel):
    hour: str
    entered: int
    exited: int
    inside: int


class RealtimeDetection(BaseModel):
    track_id: int
    camera_id: int
    camera_name: str
    x: float
    y: float
    gender: str | None
    age_group: str | None
    is_staff: bool
    event_type: str
    direction: str | None = None
    dwell_seconds: int | None = None
    zone_label: str | None = None
    timestamp: datetime


class HeatmapPoint(BaseModel):
    x: int
    y: int
    intensity: float


class HeatmapResponse(BaseModel):
    camera_id: int
    grid_size: int
    points: list[HeatmapPoint]
    max_intensity: float


class PersonEventCreate(BaseModel):
    camera_id: int
    track_id: int
    event_type: str
    gender: str | None = None
    age_group: str | None = None
    is_staff: bool = False
    confidence: float = 0.0
    x: float = 0.0
    y: float = 0.0
    direction: str | None = None
    dwell_seconds: int | None = None
    zone_label: str | None = None


class DwellRecordResponse(BaseModel):
    id: int
    camera_id: int
    track_id: int
    zone_label: str
    dwell_seconds: int
    gender: str | None
    age_group: str | None
    is_staff: bool
    entered_at: datetime
    left_at: datetime


class DirectionFlowResponse(BaseModel):
    direction: str
    count: int
    label: str


class StaffMemberResponse(BaseModel):
    id: int
    name: str
    badge_id: str
    department: str
    is_on_duty: bool
    last_seen_at: datetime | None
    last_location: str | None
    camera_id: int | None

    model_config = {"from_attributes": True}


class StaffActivityResponse(BaseModel):
    id: int
    staff_id: int
    staff_name: str
    camera_id: int
    activity: str
    duration_seconds: int
    timestamp: datetime
