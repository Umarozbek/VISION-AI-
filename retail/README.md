# Retail Analytics Platform

A retail analytics system that works with real IP cameras.

## Features

- **RTSP Camera Integration** — Connect using an IP address, username, and password (Hikvision, Dahua, Uniview).
- **YOLOv8n** — Free person detection and tracking.
- **Entry/Exit Counting** — Count people crossing a line at the entrance.
- **Age and Gender Estimation** — Free OpenCV DNN models.
- **Staff Detection** — Identify staff based on uniform color (blue uniforms).
- **Dwell Time Analysis** — Measure how long people stay in specific zones.
- **Movement Direction Analysis** — Analyze the most common movement directions.
- **Heatmap** — Real-time visualization of traffic across different zones.

## Getting Started

```bash
docker compose up --build
```

| Service | URL |
|---------|-----|
| Dashboard | http://localhost:5173 |
| API Documentation | http://localhost:8000/docs |

**Login:** `admin` / `admin123`

## Adding a Camera

1. Go to Dashboard → **Cameras** → **Add Camera**.
2. Fill in the required fields:
   - **IP Address** — For example, `192.168.1.64`
   - **Username / Password** — Camera administrator credentials
   - **Camera Type** — Hikvision, Dahua, or Other
3. Click **Test Connection**.
4. Click **Save** — The AI service will automatically connect within 10 seconds.

### Default RTSP Stream Paths

| Brand | Stream Path |
|-------|-------------|
| Hikvision | `Streaming/Channels/101` |
| Dahua | `cam/realmonitor?channel=1&subtype=0` |
| Uniview | `media/video1` |

### Entrance Camera

Enable the **Entrance Camera** switch. The AI system will count people entering and exiting and perform age, gender, and staff analysis.

## Free AI Models

| Model | Purpose |
|-------|---------|
| YOLOv8n | Person detection and tracking |
| OpenCV Age/Gender Net | Age and gender estimation |
| ByteTrack (Ultralytics) | Maintaining tracking IDs |

## Important Notes

- The camera and server must be on the **same network**.
- The camera IP address must be correct for the Docker container to connect to it.
- The YOLO model is downloaded on the first launch (approximately 6 MB).
- The AI service status is displayed on camera cards: `processing`, `connecting`, `error`.

## Architecture

```text
IP Camera (RTSP)
      │
      ▼
AI Service (YOLOv8 + Tracking)
      │ POST /analytics/events
      ▼
FastAPI Backend → PostgreSQL
      │ WebSocket
      ▼
React Dashboard (MUI + Redux)
```

## Project Creators

This Retail Analytics Platform was developed by:

### 1. GAFFOROV SUNNATBEK GAFUROVICH

**Responsibilities:**
- Backend Development
- Dashboard Frontend Development
- AI Development and Integration
- Computer Vision and People Analytics
- Camera Integration and Tracking Systems

### 2. AZAMJONOV MUKHAMMADALI AKMALJON UGLI

**Responsibilities:**
- Project Development and Implementation

---

**Project:** Retail Analytics Platform  
**Technologies:** FastAPI, Python, React, MUI, Redux, PostgreSQL, OpenCV, YOLOv8, ByteTrack, Docker, RTSP
