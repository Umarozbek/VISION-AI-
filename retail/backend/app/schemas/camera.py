from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.utils.rtsp import build_rtsp_url


class CameraCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    location: str = Field(min_length=1, max_length=255)
    camera_type: str = "rtsp"
    device_index: int | None = None
    ip_address: str | None = None
    port: int = 554
    username: str | None = None
    password: str | None = None
    stream_path: str | None = "Streaming/Channels/101"
    rtsp_url: str | None = None
    active: bool = True
    is_entrance: bool = False
    zone_width: int = 640
    zone_height: int = 480
    entrance_line_y: float | None = None

    @model_validator(mode="after")
    def validate_connection(self):
        if self.camera_type == "webcam":
            if self.device_index is None:
                self.device_index = 0
        elif not self.rtsp_url and not self.ip_address:
            raise ValueError("IP manzil yoki RTSP URL kiritilishi shart")
        return self


class CameraUpdate(BaseModel):
    name: str | None = None
    location: str | None = None
    camera_type: str | None = None
    device_index: int | None = None
    ip_address: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None
    stream_path: str | None = None
    rtsp_url: str | None = None
    active: bool | None = None
    is_entrance: bool | None = None
    zone_width: int | None = None
    zone_height: int | None = None
    entrance_line_y: float | None = None


class CameraResponse(BaseModel):
    id: int
    name: str
    location: str
    camera_type: str = "rtsp"
    device_index: int | None = None
    ip_address: str | None
    port: int
    username: str | None
    stream_path: str | None
    rtsp_url: str | None
    active: bool
    is_entrance: bool
    zone_width: int
    zone_height: int
    entrance_line_y: float | None
    processing_status: str
    last_frame_at: datetime | None
    created_at: datetime
    connection_url_preview: str | None = None

    model_config = {"from_attributes": True}

    @model_validator(mode="after")
    def mask_credentials(self):
        if self.connection_url_preview is not None:
            # serialize_camera allaqachon to'g'ri preview hisoblab bergan (webcam yoki rtsp)
            return self
        if self.camera_type == "webcam":
            device_index = self.device_index if self.device_index is not None else 0
            self.connection_url_preview = f"Laptop webcam (device #{device_index})"
        else:
            self.connection_url_preview = build_rtsp_url(
                self.ip_address,
                self.port,
                self.username,
                None,
                self.stream_path,
                self.rtsp_url,
            )
        return self


class CameraInternalResponse(CameraResponse):
    password: str | None = None
    resolved_rtsp_url: str | None = None

    @model_validator(mode="after")
    def resolve_url(self):
        if self.resolved_rtsp_url is not None:
            return self
        if self.camera_type == "webcam":
            device_index = self.device_index if self.device_index is not None else 0
            self.resolved_rtsp_url = f"webcam:{device_index}"
        else:
            self.resolved_rtsp_url = build_rtsp_url(
                self.ip_address,
                self.port,
                self.username,
                self.password,
                self.stream_path,
                self.rtsp_url,
            )
        return self


class CameraTestRequest(BaseModel):
    camera_type: str = "rtsp"
    device_index: int | None = None
    ip_address: str | None = None
    port: int = 554
    username: str | None = None
    password: str | None = None
    stream_path: str | None = "Streaming/Channels/101"
    rtsp_url: str | None = None


class CameraStatusUpdate(BaseModel):
    processing_status: str
    last_frame_at: datetime | None = None
