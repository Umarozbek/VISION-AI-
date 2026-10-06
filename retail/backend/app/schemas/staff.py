from datetime import datetime

from pydantic import BaseModel, Field


class StaffCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    badge_id: str = Field(min_length=1, max_length=100)
    department: str = "sales"
    work_position: str | None = None


class StaffUpdate(BaseModel):
    name: str | None = None
    badge_id: str | None = None
    department: str | None = None
    work_position: str | None = None
    is_on_duty: bool | None = None


class StaffPhotoResponse(BaseModel):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class StaffCenterResponse(BaseModel):
    id: int
    name: str
    badge_id: str
    department: str
    work_position: str | None
    is_on_duty: bool
    photos: list[StaffPhotoResponse]
    checked_in_at: datetime | None
    last_seen_at: datetime | None
    last_location: str | None
    camera_id: int | None

    model_config = {"from_attributes": True}


class StaffRosterEntry(BaseModel):
    """AI service uchun — yuz tanish modelini o'qitish uchun roster."""
    id: int
    name: str
    badge_id: str
    work_position: str | None
    photo_ids: list[int]


class StaffCheckInRequest(BaseModel):
    staff_id: int
    camera_id: int | None = None
    zone_label: str | None = None
