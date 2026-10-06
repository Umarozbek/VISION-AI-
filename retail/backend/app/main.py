from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, auth, cameras, dashboard, insights, staff, users, video_analysis, websocket
from app.core.config import settings
from app.db.database import Base, engine
from app.db.init_db import seed_database
from app.db.migrate import run_migrations
from app.db.session import SessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    run_migrations()
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="Retail Analytics API",
    description="Real-time retail analytics: person detection, traffic flow, heatmap, staff monitoring",
    version="2.0.0",
    lifespan=lifespan,
)

origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(cameras.router, prefix="/cameras", tags=["Cameras"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])
app.include_router(insights.router, prefix="/insights", tags=["Insights"])
app.include_router(staff.router, prefix="/staff", tags=["Staff"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
app.include_router(video_analysis.router, prefix="/video-analysis", tags=["Video Analysis"])


@app.get("/")
def root():
    return {"status": "running", "service": "Retail Analytics API", "version": "2.0.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}
