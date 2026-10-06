from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    location: Mapped[str] = mapped_column(String(255))
    camera_type: Mapped[str] = mapped_column(String(20), default="rtsp")
    device_index: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(100), nullable=True)
    port: Mapped[int] = mapped_column(Integer, default=554)
    username: Mapped[str | None] = mapped_column(String(100), nullable=True)
    password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stream_path: Mapped[str | None] = mapped_column(
        String(255), nullable=True, default="Streaming/Channels/101"
    )
    rtsp_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_entrance: Mapped[bool] = mapped_column(Boolean, default=False)
    zone_width: Mapped[int] = mapped_column(Integer, default=640)
    zone_height: Mapped[int] = mapped_column(Integer, default=480)
    entrance_line_y: Mapped[float | None] = mapped_column(nullable=True)
    processing_status: Mapped[str] = mapped_column(String(50), default="idle")
    last_frame_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
