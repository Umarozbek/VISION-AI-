from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class PersonEvent(Base):
    __tablename__ = "person_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id"), index=True)
    track_id: Mapped[int] = mapped_column(Integer, index=True)
    event_type: Mapped[str] = mapped_column(String(50))
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    age_group: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    x: Mapped[float] = mapped_column(Float, default=0.0)
    y: Mapped[float] = mapped_column(Float, default=0.0)
    direction: Mapped[str | None] = mapped_column(String(20), nullable=True)
    dwell_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    zone_label: Mapped[str | None] = mapped_column(String(50), nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )

    camera = relationship("Camera")


class TrafficSnapshot(Base):
    __tablename__ = "traffic_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    camera_id: Mapped[int | None] = mapped_column(
        ForeignKey("cameras.id"), nullable=True, index=True
    )
    entered: Mapped[int] = mapped_column(Integer, default=0)
    exited: Mapped[int] = mapped_column(Integer, default=0)
    inside: Mapped[int] = mapped_column(Integer, default=0)
    hour: Mapped[int] = mapped_column(Integer, index=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)


class HeatmapCell(Base):
    __tablename__ = "heatmap_cells"

    id: Mapped[int] = mapped_column(primary_key=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id"), index=True)
    grid_x: Mapped[int] = mapped_column(Integer)
    grid_y: Mapped[int] = mapped_column(Integer)
    intensity: Mapped[float] = mapped_column(Float, default=0.0)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)


class DwellRecord(Base):
    __tablename__ = "dwell_records"

    id: Mapped[int] = mapped_column(primary_key=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id"), index=True)
    track_id: Mapped[int] = mapped_column(Integer, index=True)
    zone_label: Mapped[str] = mapped_column(String(50))
    dwell_seconds: Mapped[int] = mapped_column(Integer, default=0)
    gender: Mapped[str | None] = mapped_column(String(20), nullable=True)
    age_group: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False)
    entered_at: Mapped[datetime] = mapped_column(DateTime)
    left_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class DirectionFlow(Base):
    __tablename__ = "direction_flows"

    id: Mapped[int] = mapped_column(primary_key=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id"), index=True)
    direction: Mapped[str] = mapped_column(String(20), index=True)
    count: Mapped[int] = mapped_column(Integer, default=1)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)


class StaffMember(Base):
    __tablename__ = "staff_members"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    badge_id: Mapped[str] = mapped_column(String(100), unique=True)
    department: Mapped[str] = mapped_column(String(100), default="sales")
    is_on_duty: Mapped[bool] = mapped_column(Boolean, default=True)
    work_position: Mapped[str | None] = mapped_column(String(100), nullable=True)
    checked_in_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    camera_id: Mapped[int | None] = mapped_column(
        ForeignKey("cameras.id"), nullable=True
    )

    photos: Mapped[list["StaffPhoto"]] = relationship(
        order_by="StaffPhoto.id", cascade="all, delete-orphan"
    )


class StaffPhoto(Base):
    """Bitta xodimning bir nechta referens yuz rasmi — turli burchak/yorug'lik
    ostida olingan bir necha rasm embeddinglarni o'rtachalab aniqroq va bir-biriga
    o'xshash xodimlarni chalkashtirmaydigan tanish modelini beradi."""
    __tablename__ = "staff_photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    staff_id: Mapped[int] = mapped_column(
        ForeignKey("staff_members.id", ondelete="CASCADE"), index=True
    )
    file_path: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class StaffActivity(Base):
    __tablename__ = "staff_activities"

    id: Mapped[int] = mapped_column(primary_key=True)
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff_members.id"), index=True)
    camera_id: Mapped[int] = mapped_column(ForeignKey("cameras.id"))
    activity: Mapped[str] = mapped_column(String(100))
    duration_seconds: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, index=True
    )
