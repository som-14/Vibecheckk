# Plain-English description: Initializes a local SQLite database with tables, triggers, and seed data for local API and frontend testing.

from sqlalchemy import create_engine, text
from backend.database import Base
from backend.models import User, TargetPersona
from backend.auth import pwd_hasher

def init_db(db_url="sqlite:///./vibecheck_dev.db"):
    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)

    # SQLite trigger matching Postgres trg_audit_video_upload
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TRIGGER IF NOT EXISTS trg_audit_video_upload
            AFTER INSERT ON videos
            FOR EACH ROW
            BEGIN
                INSERT INTO auditlogs (user_id, action_type, ip_address, timestamp)
                VALUES (NEW.user_id, 'VIDEO_UPLOAD_INITIATED', NULL, datetime('now'));
            END;
        """))
        conn.commit()

    from sqlalchemy.orm import sessionmaker
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed users with real Argon2id password hashes
    creator_hash = pwd_hasher.hash("CreatorDevPassword123!")
    admin_hash = pwd_hasher.hash("AdminDevPassword123!")

    # Check existing
    if not session.query(User).filter_by(email="creator@vibecheck.test").first():
        creator = User(
            user_id="11111111-1111-1111-1111-111111111111",
            email="creator@vibecheck.test",
            password_hash=creator_hash,
            role="CREATOR"
        )
        session.add(creator)

    if not session.query(User).filter_by(email="admin@vibecheck.test").first():
        admin = User(
            user_id="22222222-2222-2222-2222-222222222222",
            email="admin@vibecheck.test",
            password_hash=admin_hash,
            role="ADMIN"
        )
        session.add(admin)

    if not session.query(TargetPersona).filter_by(persona_id=1).first():
        p1 = TargetPersona(persona_id=1, name="Gen Z Trendsetters", min_age=14, max_age=24)
        p2 = TargetPersona(persona_id=2, name="Millennial Techies", min_age=25, max_age=40)
        p3 = TargetPersona(persona_id=3, name="General Casual Viewers", min_age=18, max_age=65)
        session.add_all([p1, p2, p3])

    session.commit()
    session.close()
    print("Local database initialized successfully at", db_url)

if __name__ == "__main__":
    init_db()

