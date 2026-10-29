# Plain-English description: Verifies and proves the end-to-end workflow: login, video upload, analysis status polling, Celery worker processing, and audit log generation.

import io
import json
from starlette.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database import Base, get_db
import backend.database as db_module
from backend.models import User, TargetPersona, AuditLog
from backend.auth import pwd_hasher
from worker.tasks import process_video

def main():
    print("=" * 60)
    print("VIBECHECK: END-TO-END FLOW VERIFICATION")
    print("=" * 60)

    # 1. Setup isolated database for testing the complete pipeline
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    # Create SQLite trigger equivalent to Postgres trg_audit_video_upload
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

    # Seed creator user and persona
    seed_db = TestingSessionLocal()
    creator_pass = "CreatorDevPassword123!"
    creator = User(
        user_id="11111111-1111-1111-1111-111111111111",
        email="creator@vibecheck.test",
        password_hash=pwd_hasher.hash(creator_pass),
        role="CREATOR"
    )
    persona = TargetPersona(
        persona_id=1,
        name="Gen Z Trendsetters",
        min_age=14,
        max_age=24
    )
    seed_db.add_all([creator, persona])
    seed_db.commit()
    seed_db.close()

    # Configure app and worker to use the test database session
    def override_db():
        d = TestingSessionLocal()
        try:
            yield d
        finally:
            d.close()

    app.dependency_overrides[get_db] = override_db
    db_module.SessionLocal = TestingSessionLocal
    db_module.engine = engine

    # Ensure worker also uses the test database session
    import worker.tasks as worker_tasks
    worker_tasks.db_mod.SessionLocal = TestingSessionLocal
    worker_tasks.db_mod.engine = engine

    # Mock send_task to simulate async queueing without blocking on missing Redis broker
    import backend.main
    backend.main.celery_app.send_task = lambda *args, **kwargs: None

    # Use TestClient with modern httpx2 backend
    client = TestClient(app)

    # STEP 1: Login as seed creator
    print("\n--- STEP 1: Login as seed creator ---")
    login_resp = client.post("/api/v1/auth/login", json={
        "email": "creator@vibecheck.test",
        "password": creator_pass
    })
    print(f"Status Code: {login_resp.status_code}")
    login_data = login_resp.json()
    token = login_data.get("access_token")
    print(f"Response: {json.dumps(login_data, indent=2)}")
    assert login_resp.status_code == 200 and token is not None

    headers = {"Authorization": f"Bearer {token}"}

    # STEP 2: Upload a small test MP4
    print("\n--- STEP 2: Upload small test MP4 ---")
    dummy_mp4_bytes = b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00isommp42\x00\x00\x00\x08free"
    upload_file = io.BytesIO(dummy_mp4_bytes)

    upload_resp = client.post(
        "/api/v1/videos/upload",
        headers=headers,
        data={"persona_id": 1, "caption": "Testing hook #virality"},
        files={"file": ("test_clip.mp4", upload_file, "video/mp4")}
    )
    print(f"Status Code: {upload_resp.status_code}")
    upload_data = upload_resp.json()
    video_id = upload_data.get("video_id")
    print(f"Response: {json.dumps(upload_data, indent=2)}")
    assert upload_resp.status_code == 202 and video_id is not None

    # STEP 3: Immediately call GET /analysis/{id} (Expect PROCESSING)
    print("\n--- STEP 3: GET /analysis/{id} immediately after upload ---")
    analysis_resp_1 = client.get(f"/api/v1/analysis/{video_id}", headers=headers)
    print(f"Status Code: {analysis_resp_1.status_code}")
    print(f"Response: {json.dumps(analysis_resp_1.json(), indent=2)}")
    assert analysis_resp_1.json().get("status") == "PROCESSING"

    # STEP 4: Worker processes the video
    print("\n--- STEP 4: Celery background worker processes video ---")
    worker_result = process_video(video_id)
    print(f"Worker Output: {json.dumps(worker_result, indent=2)}")

    # STEP 5: Call GET /analysis/{id} again (Expect COMPLETED with scores & critiques)
    print("\n--- STEP 5: GET /analysis/{id} after worker completes ---")
    analysis_resp_2 = client.get(f"/api/v1/analysis/{video_id}", headers=headers)
    print(f"Status Code: {analysis_resp_2.status_code}")
    analysis_data = analysis_resp_2.json()
    print(f"Response: {json.dumps(analysis_data, indent=2)}")
    assert analysis_data.get("status") == "COMPLETED"
    assert "virality_score" in analysis_data
    assert len(analysis_data.get("critiques", [])) >= 2

    # STEP 6: Check AuditLogs for both VIDEO_UPLOAD_INITIATED and ANALYSIS_PERSISTED
    print("\n--- STEP 6: Verify AuditLogs table ---")
    audit_db = TestingSessionLocal()
    logs = audit_db.query(AuditLog).order_by(AuditLog.log_id.asc()).all()
    print(f"Total AuditLogs recorded: {len(logs)}")
    for log in logs:
        print(f"  [Log #{log.log_id}] Action: {log.action_type:<24} User: {log.user_id} Timestamp: {log.timestamp}")

    actions = [log.action_type for log in logs]
    assert "VIDEO_UPLOAD_INITIATED" in actions
    assert "ANALYSIS_PERSISTED" in actions
    audit_db.close()

    print("\n" + "=" * 60)
    print("ALL 6 FLOW STEPS VERIFIED AND PASSED!")
    print("=" * 60)

if __name__ == "__main__":
    main()
