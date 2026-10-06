from sqlalchemy.orm import Session

from app.core.redis import set_json
from app.core.security import hash_password
from app.models.analytics import StaffMember
from app.models.user import User


def seed_database(db: Session) -> None:
    if db.query(User).first():
        return

    admin = User(
        username="admin",
        email="admin@retail.uz",
        password_hash=hash_password("admin123"),
        role="admin",
    )
    operator = User(
        username="operator",
        email="operator@retail.uz",
        password_hash=hash_password("operator123"),
        role="operator",
    )
    db.add_all([admin, operator])

    staff_members = [
        StaffMember(
            name="Aziza Karimova",
            badge_id="STF-001",
            department="sales",
            is_on_duty=True,
            last_location="Kassa zonasi",
        ),
        StaffMember(
            name="Javohir Tursunov",
            badge_id="STF-002",
            department="security",
            is_on_duty=True,
            last_location="Kirish eshigi",
        ),
        StaffMember(
            name="Dilnoza Rahimova",
            badge_id="STF-003",
            department="sales",
            is_on_duty=True,
            last_location="Elektronika bo'limi",
        ),
        StaffMember(
            name="Bobur Mirzayev",
            badge_id="STF-004",
            department="warehouse",
            is_on_duty=False,
            last_location="Ombor xonasi",
        ),
    ]
    db.add_all(staff_members)
    db.commit()

    from app.services.analytics_service import (
        get_age_stats,
        get_gender_stats,
        get_overview,
        get_traffic_flow,
    )

    set_json("stats:overview", get_overview(db), ex=3600)
    set_json("stats:gender", get_gender_stats(db), ex=3600)
    set_json("stats:age", get_age_stats(db), ex=3600)
    set_json("stats:traffic_flow", get_traffic_flow(db), ex=3600)
