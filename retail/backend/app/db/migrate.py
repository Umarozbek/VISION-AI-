from sqlalchemy import inspect, text

from app.db.database import engine


def run_migrations() -> None:
    inspector = inspect(engine)
    if "cameras" not in inspector.get_table_names():
        return

    existing = {col["name"] for col in inspector.get_columns("cameras")}
    alterations = [
        ("ip_address", "VARCHAR(100)"),
        ("port", "INTEGER DEFAULT 554"),
        ("username", "VARCHAR(100)"),
        ("password", "VARCHAR(255)"),
        ("stream_path", "VARCHAR(255)"),
        ("entrance_line_y", "FLOAT"),
        ("processing_status", "VARCHAR(50) DEFAULT 'idle'"),
        ("last_frame_at", "TIMESTAMP"),
    ]

    with engine.begin() as conn:
        for column, col_type in alterations:
            if column not in existing:
                conn.execute(text(f"ALTER TABLE cameras ADD COLUMN {column} {col_type}"))

        if "dwell_records" not in inspector.get_table_names():
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS dwell_records (
                        id SERIAL PRIMARY KEY,
                        camera_id INTEGER REFERENCES cameras(id),
                        track_id INTEGER,
                        zone_label VARCHAR(50),
                        dwell_seconds INTEGER DEFAULT 0,
                        gender VARCHAR(20),
                        age_group VARCHAR(20),
                        is_staff BOOLEAN DEFAULT FALSE,
                        entered_at TIMESTAMP,
                        left_at TIMESTAMP
                    )
                    """
                )
            )

        if "direction_flows" not in inspector.get_table_names():
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS direction_flows (
                        id SERIAL PRIMARY KEY,
                        camera_id INTEGER REFERENCES cameras(id),
                        direction VARCHAR(20),
                        count INTEGER DEFAULT 1,
                        date TIMESTAMP
                    )
                    """
                )
            )

        person_cols = {col["name"] for col in inspector.get_columns("person_events")}
        for column, col_type in [
            ("direction", "VARCHAR(20)"),
            ("dwell_seconds", "INTEGER"),
            ("zone_label", "VARCHAR(50)"),
        ]:
            if column not in person_cols:
                conn.execute(
                    text(f"ALTER TABLE person_events ADD COLUMN {column} {col_type}")
                )

        staff_cols = {col["name"] for col in inspector.get_columns("staff_members")}
        # reference_photo / face_encoding — StaffPhoto jadvaliga ko'chirildi
        # (bitta xodim endi bir nechta referens rasm bilan aniqroq tanilishi uchun).
        if "reference_photo" in staff_cols:
            if "staff_photos" in inspector.get_table_names():
                conn.execute(
                    text(
                        """
                        INSERT INTO staff_photos (staff_id, file_path, created_at)
                        SELECT id, reference_photo, NOW() FROM staff_members
                        WHERE reference_photo IS NOT NULL
                        """
                    )
                )
            conn.execute(text("ALTER TABLE staff_members DROP COLUMN reference_photo"))
        if "face_encoding" in staff_cols:
            conn.execute(text("ALTER TABLE staff_members DROP COLUMN face_encoding"))
        if "work_position" not in staff_cols:
            conn.execute(
                text("ALTER TABLE staff_members ADD COLUMN work_position VARCHAR(100)")
            )
        if "checked_in_at" not in staff_cols:
            conn.execute(
                text("ALTER TABLE staff_members ADD COLUMN checked_in_at TIMESTAMP")
            )
