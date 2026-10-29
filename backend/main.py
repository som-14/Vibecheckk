# Plain-English description: Main FastAPI application defining exactly 4 core endpoints: auth login, video upload, analysis retrieval, and admin metrics.

import uuid
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, status, File, UploadFile, Form, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

import os
from fastapi.middleware.cors import CORSMiddleware
from backend.config import MAX_UPLOAD_SIZE, STORAGE_DIR
from backend.database import get_db
from backend.models import User, Video, ViralityPrediction, AgentCritique
from backend.auth import (
    verify_password,
    create_access_token,
    get_current_user,
    RequireRoles
)
from backend.rate_limiter import IPRateLimiterMiddleware
from backend.celery_client import celery_app

# Initialize FastAPI application
app = FastAPI(
    title="VibeCheck API",
    description="Backend API for Multimodal Virality Engine",
    version="1.0.0"
)

# Configure CORS for frontend origin only
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Apply rate limiting middleware (10 requests per minute per IP)
app.add_middleware(IPRateLimiterMiddleware, max_requests=10, window_seconds=60)

# Global exception handler to prevent leaking stack traces or sensitive details
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Log error internally without exposing traceback to client
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."}
    )

# Pydantic schema for login request
class LoginRequest(BaseModel):
    email: str
    password: str

# 1. POST /api/v1/auth/login
@app.post("/api/v1/auth/login", status_code=status.HTTP_200_OK)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    # Parameterized query to look up user by email
    user = db.query(User).filter(User.email == request.email).first()

    # Verify user exists and password hash matches Argon2id
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate RS256-signed JWT token with 15-minute expiry
    access_token = create_access_token(
        data={"sub": user.user_id, "email": user.email, "role": user.role}
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in_minutes": 15
    }

# 2. POST /api/v1/videos/upload
@app.post("/api/v1/videos/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_video(
    file: UploadFile = File(...),
    persona_id: int = Form(...),
    caption: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Validate file format: only MP4 allowed
    filename = file.filename or ""
    if not filename.lower().endswith(".mp4"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only MP4 video files are accepted."
        )

    # Read content to check file size limit (50MB)
    contents = await file.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size exceeds the maximum limit of 50MB."
        )

    # Generate unique video ID
    video_id = str(uuid.uuid4())

    # MOCK for Azure Blob: Save file to local backend storage
    dest_path = STORAGE_DIR / f"{video_id}.mp4"
    with open(dest_path, "wb") as f:
        f.write(contents)

    blob_url = f"/backend/storage/{video_id}.mp4"

    # Insert Videos row using parameterized ORM query
    new_video = Video(
        video_id=video_id,
        user_id=current_user.user_id,
        persona_id=persona_id,
        blob_url=blob_url,
        caption=caption,
        duration_seconds=15  # Default estimated duration
    )
    db.add(new_video)
    db.commit()
    db.refresh(new_video)

    # Enqueue background Celery processing task (must not crash if worker is missing)
    try:
        celery_app.send_task("process_video", args=[str(video_id)])
    except Exception:
        pass

    return {
        "video_id": str(video_id),
        "status": "QUEUED"
    }

# 3. GET /api/v1/analysis/{id}
@app.get("/api/v1/analysis/{id}", status_code=status.HTTP_200_OK)
def get_analysis(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Fetch video record
    video = db.query(Video).filter(Video.video_id == id).first()
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video not found."
        )

    # Authorization check: CREATOR can only read their own videos; ADMIN can read all
    if current_user.role == "CREATOR" and video.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to view this analysis."
        )

    # Fetch virality prediction record
    prediction = db.query(ViralityPrediction).filter(ViralityPrediction.video_id == id).first()
    if not prediction:
        return {
            "video_id": id,
            "status": "PROCESSING"
        }

    # Fetch critiques for this prediction
    critiques = db.query(AgentCritique).filter(AgentCritique.prediction_id == prediction.prediction_id).all()

    return {
        "video_id": id,
        "status": "COMPLETED",
        "virality_score": float(prediction.virality_score),
        "audience_fit_score": float(prediction.audience_fit_score),
        "classification": prediction.classification,
        "critiques": [
            {
                "critique_id": c.critique_id,
                "agent_role": c.agent_role,
                "feedback_text": c.feedback_text,
                "timestamp_marker": float(c.timestamp_marker) if c.timestamp_marker is not None else None,
                "priority": c.priority
            }
            for c in critiques
        ]
    }

# 4. GET /api/v1/metrics/view
@app.get("/api/v1/metrics/view", status_code=status.HTTP_200_OK)
def get_metrics_view(
    timeframe: Optional[str] = "7d",
    niche_id: Optional[int] = None,
    current_user: User = Depends(RequireRoles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    # Reads aggregated creator performance metrics from view v_creator_performance_summary
    query = text("""
        SELECT
            user_id,
            email,
            total_videos_analyzed,
            mean_virality_score,
            viral_hit_count,
            viral_success_rate_pct
        FROM v_creator_performance_summary
    """)
    rows = db.execute(query).mappings().all()

    return [
        {
            "user_id": str(r["user_id"]),
            "email": r["email"],
            "total_videos_analyzed": int(r["total_videos_analyzed"]),
            "mean_virality_score": float(r["mean_virality_score"]),
            "viral_hit_count": int(r["viral_hit_count"]),
            "viral_success_rate_pct": float(r["viral_success_rate_pct"])
        }
        for r in rows
    ]
