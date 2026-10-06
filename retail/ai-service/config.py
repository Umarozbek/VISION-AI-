import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
AI_API_KEY = os.getenv("AI_SERVICE_API_KEY", "ai-service-internal-key")
CAMERA_POLL_INTERVAL = int(os.getenv("CAMERA_POLL_INTERVAL", "10"))
YOLO_MODEL = os.getenv("YOLO_MODEL", "yolov8n.pt")
FRAME_SKIP = int(os.getenv("FRAME_SKIP", "2"))
DEMOGRAPHIC_INTERVAL = int(os.getenv("DEMOGRAPHIC_INTERVAL", "45"))
MIN_DWELL_SECONDS = int(os.getenv("MIN_DWELL_SECONDS", "5"))
RTSP_TRANSPORT = os.getenv("RTSP_TRANSPORT", "tcp")
