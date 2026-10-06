from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, verify_ai_service
from app.core.stream_auth import get_stream_user
from app.core.zones import ZONE_LABELS
from app.db.session import get_db
from app.models.analytics import StaffActivity, StaffMember, StaffPhoto
from app.models.user import User
from app.schemas.dashboard import StaffActivityResponse, StaffMemberResponse
from app.schemas.staff import (
    StaffCenterResponse,
    StaffCheckInRequest,
    StaffCreate,
    StaffPhotoResponse,
    StaffRosterEntry,
    StaffUpdate,
)

router = APIRouter()

PHOTO_DIR = Path("staff_photos")
PHOTO_DIR.mkdir(exist_ok=True)

# Bitta xodim uchun ko'pi bilan nechta referens rasm — bir nechtasi turli
# burchak/yorug'lik ostida embeddinglarni o'rtachalab tanishni aniqlashtiradi,
# ayniqsa bir-biriga o'xshash yoki bir xil ismli xodimlarni ajratishda.
MAX_PHOTOS_PER_STAFF = 5


def _serialize_center(member: StaffMember) -> StaffCenterResponse:
    return StaffCenterResponse(
        id=member.id,
        name=member.name,
        badge_id=member.badge_id,
        department=member.department,
        work_position=member.work_position,
        is_on_duty=member.is_on_duty,
        photos=[StaffPhotoResponse.model_validate(p) for p in member.photos],
        checked_in_at=member.checked_in_at,
        last_seen_at=member.last_seen_at,
        last_location=member.last_location,
        camera_id=member.camera_id,
    )


# ── Staff Center — ish o'rinlari ro'yxati ───────────────────────────────────

@router.get("/zones")
def get_zones(_: User = Depends(get_current_user)):
    return {"zones": ZONE_LABELS}


# ── Staff Center — CRUD ──────────────────────────────────────────────────────

@router.get("/center", response_model=list[StaffCenterResponse])
def list_staff_center(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    members = db.query(StaffMember).order_by(StaffMember.name.asc()).all()
    return [_serialize_center(m) for m in members]


@router.post("/center", response_model=StaffCenterResponse)
def create_staff_center(
    payload: StaffCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    if db.query(StaffMember).filter(StaffMember.badge_id == payload.badge_id).first():
        raise HTTPException(status_code=400, detail="Bu badge ID allaqachon mavjud")
    member = StaffMember(
        name=payload.name,
        badge_id=payload.badge_id,
        department=payload.department,
        work_position=payload.work_position,
        is_on_duty=False,
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return _serialize_center(member)


@router.patch("/center/{staff_id}", response_model=StaffCenterResponse)
def update_staff_center(
    staff_id: int,
    payload: StaffUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    member = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Xodim topilmadi")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(member, key, value)
    db.commit()
    db.refresh(member)
    return _serialize_center(member)


@router.delete("/center/{staff_id}")
def delete_staff_center(
    staff_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    member = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Xodim topilmadi")
    for photo in member.photos:
        photo_path = Path(photo.file_path)
        if photo_path.exists():
            photo_path.unlink(missing_ok=True)
    db.query(StaffActivity).filter(StaffActivity.staff_id == staff_id).delete()
    db.delete(member)
    db.commit()
    return {"message": "deleted"}


# ── Rasm yuklash / ko'rsatish ────────────────────────────────────────────────

def _decode_and_validate_face(content: bytes):
    """Rasmni dekodlaydi va unda aniq bitta yuz borligini tekshiradi (tezkor
    Haar-cascade tekshiruvi — chuqur embedding AI-service tomonida hisoblanadi).
    Guruh fotosi yoki yuzsiz rasm keyinchalik tanish sifatini buzmasligi uchun
    bu yerda rad etiladi."""
    import cv2
    import numpy as np

    arr = np.frombuffer(content, dtype=np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Rasmni o'qib bo'lmadi")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
    if len(faces) == 0:
        raise HTTPException(status_code=400, detail="Rasmda yuz aniqlanmadi — aniqroq, yorug' rasm tanlang")
    if len(faces) > 1:
        raise HTTPException(
            status_code=400,
            detail="Rasmda bir nechta yuz aniqlandi — faqat bitta odam tushgan rasm yuklang",
        )
    return img


@router.post("/center/{staff_id}/photos", response_model=StaffCenterResponse)
async def add_staff_photo(
    staff_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    member = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Xodim topilmadi")
    if len(member.photos) >= MAX_PHOTOS_PER_STAFF:
        raise HTTPException(
            status_code=400,
            detail=f"Bitta xodim uchun ko'pi bilan {MAX_PHOTOS_PER_STAFF} ta rasm yuklash mumkin",
        )

    allowed = {".jpg", ".jpeg", ".png", ".webp"}
    suffix = Path(file.filename or "photo.jpg").suffix.lower()
    if suffix not in allowed:
        raise HTTPException(status_code=400, detail="Rasm formati: jpg, png yoki webp")

    content = await file.read()
    if len(content) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Rasm hajmi 8 MB dan katta bo'lmasligi kerak")

    import cv2

    img = _decode_and_validate_face(content)

    photo = StaffPhoto(staff_id=staff_id, file_path="")
    db.add(photo)
    db.flush()  # photo.id ni olish uchun

    dest = PHOTO_DIR / f"{staff_id}_{photo.id}.jpg"
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    if not ok:
        db.rollback()
        raise HTTPException(status_code=400, detail="Rasmni saqlab bo'lmadi")
    dest.write_bytes(buf.tobytes())
    photo.file_path = str(dest)

    db.commit()
    db.refresh(member)
    return _serialize_center(member)


@router.delete("/center/{staff_id}/photos/{photo_id}", response_model=StaffCenterResponse)
def delete_staff_photo(
    staff_id: int,
    photo_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    member = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Xodim topilmadi")
    photo = db.query(StaffPhoto).filter(
        StaffPhoto.id == photo_id, StaffPhoto.staff_id == staff_id
    ).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Rasm topilmadi")

    path = Path(photo.file_path)
    if path.exists():
        path.unlink(missing_ok=True)
    db.delete(photo)
    db.commit()
    db.refresh(member)
    return _serialize_center(member)


@router.get("/center/{staff_id}/photos/{photo_id}")
def get_staff_photo(
    staff_id: int,
    photo_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_stream_user),
):
    photo = db.query(StaffPhoto).filter(
        StaffPhoto.id == photo_id, StaffPhoto.staff_id == staff_id
    ).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Rasm mavjud emas")
    path = Path(photo.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Rasm fayli topilmadi")
    return FileResponse(path, media_type="image/jpeg")


# ── AI-service uchun ichki endpointlar ───────────────────────────────────────

@router.get("/internal/roster", response_model=list[StaffRosterEntry])
def get_roster(
    db: Session = Depends(get_db),
    _: None = Depends(verify_ai_service),
):
    members = db.query(StaffMember).all()
    return [
        StaffRosterEntry(
            id=m.id, name=m.name, badge_id=m.badge_id,
            work_position=m.work_position, photo_ids=[p.id for p in m.photos],
        )
        for m in members
    ]


@router.get("/internal/{staff_id}/photos/{photo_id}")
def get_roster_photo(
    staff_id: int,
    photo_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_ai_service),
):
    photo = db.query(StaffPhoto).filter(
        StaffPhoto.id == photo_id, StaffPhoto.staff_id == staff_id
    ).first()
    if not photo:
        raise HTTPException(status_code=404, detail="Rasm mavjud emas")
    path = Path(photo.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Rasm fayli topilmadi")
    return FileResponse(path, media_type="image/jpeg")


@router.post("/internal/check-in")
def staff_check_in(
    payload: StaffCheckInRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_ai_service),
):
    """AI-service xodim o'z ish o'rniga kirganini aniqlaganda chaqiradi."""
    member = db.query(StaffMember).filter(StaffMember.id == payload.staff_id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Xodim topilmadi")

    now = datetime.utcnow()
    member.is_on_duty = True
    member.checked_in_at = now
    member.last_seen_at = now
    if payload.zone_label:
        member.last_location = payload.zone_label
    if payload.camera_id:
        member.camera_id = payload.camera_id

    if payload.camera_id:
        db.add(StaffActivity(
            staff_id=member.id,
            camera_id=payload.camera_id,
            activity="check_in",
            duration_seconds=0,
            timestamp=now,
        ))

    db.commit()
    return {"status": "ok", "staff_id": member.id, "checked_in_at": now.isoformat()}


# ── Eski (Staff Monitoring) endpointlar — o'zgarishsiz ──────────────────────

@router.get("/members", response_model=list[StaffMemberResponse])
def list_staff(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return db.query(StaffMember).order_by(StaffMember.name.asc()).all()


@router.get("/monitoring")
def staff_monitoring(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    members = db.query(StaffMember).all()
    on_duty = [m for m in members if m.is_on_duty]
    off_duty = [m for m in members if not m.is_on_duty]

    return {
        "total": len(members),
        "on_duty": len(on_duty),
        "off_duty": len(off_duty),
        "members": [
            {
                "id": m.id,
                "name": m.name,
                "badge_id": m.badge_id,
                "department": m.department,
                "is_on_duty": m.is_on_duty,
                "last_seen_at": m.last_seen_at.isoformat() if m.last_seen_at else None,
                "last_location": m.last_location,
                "camera_id": m.camera_id,
            }
            for m in members
        ],
    }


@router.get("/activities", response_model=list[StaffActivityResponse])
def staff_activities(
    limit: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rows = (
        db.query(StaffActivity, StaffMember.name)
        .join(StaffMember, StaffMember.id == StaffActivity.staff_id)
        .order_by(StaffActivity.timestamp.desc())
        .limit(limit)
        .all()
    )
    return [
        StaffActivityResponse(
            id=activity.id,
            staff_id=activity.staff_id,
            staff_name=staff_name,
            camera_id=activity.camera_id,
            activity=activity.activity,
            duration_seconds=activity.duration_seconds,
            timestamp=activity.timestamp,
        )
        for activity, staff_name in rows
    ]


@router.patch("/members/{staff_id}/duty")
def toggle_duty(
    staff_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    member = db.query(StaffMember).filter(StaffMember.id == staff_id).first()
    if not member:
        return {"error": "not found"}
    member.is_on_duty = not member.is_on_duty
    member.last_seen_at = datetime.utcnow()
    db.commit()
    return {"id": staff_id, "is_on_duty": member.is_on_duty}
