# Plain-English description: Comprehensive test suite for VibeCheck backend API covering auth, role checks, upload validation, and rate limiting.

import io
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.database import Base, get_db
from backend.models import User, TargetPersona, Video, ViralityPrediction, AgentCritique
from backend.auth import create_access_token

# Test database setup (SQLite in-memory for fast, isolated tests)
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Seed user credentials and real Argon2id password hashes
CREATOR_PASS = "CreatorDevPassword123!"
ADMIN_PASS = "AdminDevPassword123!"
CREATOR_HASH = "$argon2id$v=19$m=65536,t=3,p=4$PUW56YtEJRIEEkSgBBuZVQ$pCbefVvmHLp02mVA/8hUJBUKQgubQFe6o2FlKnmuCB0"
ADMIN_HASH = "$argon2id$v=19$m=65536,t=3,p=4$WFFGlKvQfR+v9Kd6vefVqQ$F0lFmMNkLg4Xl8vuY293W6CHgty8qqkI4ylHohPFjWE"

@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    # Create all schema tables in test database
    Base.metadata.create_all(bind=engine)

    # Create analytical view for metrics
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE VIEW IF NOT EXISTS v_creator_performance_summary AS
            SELECT
                u.user_id,
                u.email,
                COUNT(vp.prediction_id) AS total_videos_analyzed,
                COALESCE(ROUND(AVG(vp.virality_score), 2), 0.00) AS mean_virality_score,
                COUNT(CASE WHEN vp.classification = 'VIRAL' THEN 1 END) AS viral_hit_count,
                COALESCE(
                    ROUND(
                        (COUNT(CASE WHEN vp.classification = 'VIRAL' THEN 1 END) * 100.0 / NULLIF(COUNT(vp.prediction_id), 0)),
                        2
                    ),
                    0.00
                ) AS viral_success_rate_pct
            FROM users u
            LEFT JOIN videos v ON u.user_id = v.user_id
            LEFT JOIN viralitypredictions vp ON v.video_id = vp.video_id
            WHERE u.role = 'CREATOR'
            GROUP BY u.user_id, u.email;
        """))
        conn.commit()

    # Seed initial test data with pre-calculated real Argon2id hashes
    db = TestingSessionLocal()
    try:
        # User 1: Creator 1
        creator1 = User(
            user_id="11111111-1111-1111-1111-111111111111",
            email="creator@vibecheck.test",
            password_hash=CREATOR_HASH,
            role="CREATOR"
        )
        # User 2: Creator 2
        creator2 = User(
            user_id="22222222-2222-2222-2222-222222222222",
            email="creator2@vibecheck.test",
            password_hash=CREATOR_HASH,
            role="CREATOR"
        )
        # User 3: Admin
        admin = User(
            user_id="33333333-3333-3333-3333-333333333333",
            email="admin@vibecheck.test",
            password_hash=ADMIN_HASH,
            role="ADMIN"
        )
        persona = TargetPersona(
            persona_id=1,
            name="Gen Z Trendsetters",
            min_age=14,
            max_age=24
        )
        db.add_all([creator1, creator2, admin, persona])
        db.commit()

        # Seed Video 1 owned by Creator 1
        video1 = Video(
            video_id="44444444-4444-4444-4444-444444444444",
            user_id=creator1.user_id,
            persona_id=1,
            blob_url="/backend/storage/sample.mp4",
            caption="Sample Viral Hook",
            duration_seconds=20
        )
        db.add(video1)
        db.commit()

        # Seed Virality Prediction & Critique for Video 1
        pred1 = ViralityPrediction(
            prediction_id="55555555-5555-5555-5555-555555555555",
            video_id=video1.video_id,
            virality_score=88.50,
            audience_fit_score=92.00,
            classification="VIRAL"
        )
        db.add(pred1)
        db.commit()

        critique1 = AgentCritique(
            critique_id=1,
            prediction_id=pred1.prediction_id,
            agent_role="Pacing Evaluator",
            feedback_text="Strong 3-second visual hook. Keeps viewer attention high.",
            timestamp_marker=2.5,
            priority="INFO"
        )
        db.add(critique1)
        db.commit()

    finally:
        db.close()

    yield

    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

# a) Login success
def test_login_success(client):
    response = client.post("/api/v1/auth/login", json={
        "email": "creator@vibecheck.test",
        "password": CREATOR_PASS
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in_minutes"] == 15

# b) Login failure (401)
def test_login_failure_wrong_password(client):
    response = client.post("/api/v1/auth/login", json={
        "email": "creator@vibecheck.test",
        "password": "WrongPassword123!"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

# c) Tampered JWT rejected
def test_tampered_jwt_rejected(client):
    # Obtain valid token
    token = create_access_token(data={"sub": "11111111-1111-1111-1111-111111111111", "role": "CREATOR"})
    # Tamper with the signature portion
    tampered_token = token[:-6] + "XYZ123"

    response = client.get(
        "/api/v1/analysis/44444444-4444-4444-4444-444444444444",
        headers={"Authorization": f"Bearer {tampered_token}"}
    )
    assert response.status_code == 401
    assert "Invalid or tampered token" in response.json()["detail"]

# d) Expired JWT rejected
def test_expired_jwt_rejected(client):
    # Generate token already expired in the past
    expired_token = create_access_token(
        data={"sub": "11111111-1111-1111-1111-111111111111", "role": "CREATOR"},
        expires_delta=timedelta(seconds=-60)
    )

    response = client.get(
        "/api/v1/analysis/44444444-4444-4444-4444-444444444444",
        headers={"Authorization": f"Bearer {expired_token}"}
    )
    assert response.status_code == 401
    assert "Token has expired" in response.json()["detail"]

# e) Upload of a non-MP4 file rejected (400)
def test_upload_non_mp4_rejected(client):
    token = create_access_token(data={"sub": "11111111-1111-1111-1111-111111111111", "role": "CREATOR"})
    fake_file = io.BytesIO(b"This is a text file, not a video.")

    response = client.post(
        "/api/v1/videos/upload",
        headers={"Authorization": f"Bearer {token}"},
        data={"persona_id": 1, "caption": "Test video"},
        files={"file": ("malicious.txt", fake_file, "text/plain")}
    )
    assert response.status_code == 400
    assert "Only MP4 video files are accepted" in response.json()["detail"]

# f) Creator gets 403 on another user's video
def test_creator_cannot_access_other_creator_video(client):
    # Creator 2 attempts to access Creator 1's video (video_id 4444...)
    token_creator2 = create_access_token(data={"sub": "22222222-2222-2222-2222-222222222222", "role": "CREATOR"})

    response = client.get(
        "/api/v1/analysis/44444444-4444-4444-4444-444444444444",
        headers={"Authorization": f"Bearer {token_creator2}"}
    )
    assert response.status_code == 403
    assert "Forbidden" in response.json()["detail"]

# g) Admin can read any video
def test_admin_can_read_any_video(client):
    token_admin = create_access_token(data={"sub": "33333333-3333-3333-3333-333333333333", "role": "ADMIN"})

    response = client.get(
        "/api/v1/analysis/44444444-4444-4444-4444-444444444444",
        headers={"Authorization": f"Bearer {token_admin}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["virality_score"] == 88.5
    assert len(data["critiques"]) == 1
    assert data["critiques"][0]["agent_role"] == "Pacing Evaluator"

# h) The 11th request in a minute returns 429
def test_rate_limiting_11th_request_returns_429(client):
    unique_ip = "198.51.100.42"
    headers = {"X-Forwarded-For": unique_ip}

    # Send 10 requests that pass through the rate limiter
    for _ in range(10):
        res = client.get("/api/v1/metrics/view", headers=headers)
        # Even unauthorized (401), request counts toward rate limiter
        assert res.status_code == 401

    # 11th request must be rate limited to 429
    res_11 = client.get("/api/v1/metrics/view", headers=headers)
    assert res_11.status_code == 429
    assert "Too Many Requests" in res_11.json()["detail"]
