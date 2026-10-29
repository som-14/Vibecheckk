# Plain-English description: Defines SQLAlchemy ORM models corresponding to the 6 core database tables.

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    Text,
    DateTime,
    ForeignKey,
    BigInteger,
    CheckConstraint
)
from sqlalchemy.orm import relationship
from backend.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)

    __table_args__ = (
        CheckConstraint("role IN ('CREATOR', 'ADMIN')", name="chk_user_role"),
    )

    videos = relationship("Video", back_populates="user")


class TargetPersona(Base):
    __tablename__ = "targetpersonas"

    persona_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    min_age = Column(Integer, nullable=False)
    max_age = Column(Integer, nullable=False)

    __table_args__ = (
        CheckConstraint("min_age >= 13", name="chk_persona_min_age"),
        CheckConstraint("max_age <= 99", name="chk_persona_max_age"),
    )

    videos = relationship("Video", back_populates="persona")


class Video(Base):
    __tablename__ = "videos"

    video_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    persona_id = Column(Integer, ForeignKey("targetpersonas.persona_id"), nullable=True)
    blob_url = Column(Text, nullable=False)
    caption = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("duration_seconds BETWEEN 3 AND 180", name="chk_video_duration"),
    )

    user = relationship("User", back_populates="videos")
    persona = relationship("TargetPersona", back_populates="videos")
    prediction = relationship("ViralityPrediction", back_populates="video", uselist=False, cascade="all, delete-orphan")


class ViralityPrediction(Base):
    __tablename__ = "viralitypredictions"

    prediction_id = Column(String(36), primary_key=True, default=generate_uuid)
    video_id = Column(String(36), ForeignKey("videos.video_id", ondelete="CASCADE"), unique=True, nullable=False)
    virality_score = Column(Numeric(5, 2), nullable=False)
    audience_fit_score = Column(Numeric(5, 2), nullable=False)
    classification = Column(String(20), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        CheckConstraint("virality_score BETWEEN 0 AND 100", name="chk_virality_score"),
        CheckConstraint("classification IN ('VIRAL', 'AVERAGE', 'LOW')", name="chk_virality_classification"),
    )

    video = relationship("Video", back_populates="prediction")
    critiques = relationship("AgentCritique", back_populates="prediction", cascade="all, delete-orphan")


class AgentCritique(Base):
    __tablename__ = "agentcritiques"

    critique_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    prediction_id = Column(String(36), ForeignKey("viralitypredictions.prediction_id", ondelete="CASCADE"), nullable=False)
    agent_role = Column(String(100), nullable=False)
    feedback_text = Column(Text, nullable=False)
    timestamp_marker = Column(Numeric(6, 2), nullable=True)
    priority = Column(String(20), nullable=False)

    __table_args__ = (
        CheckConstraint("priority IN ('CRITICAL', 'MEDIUM', 'INFO')", name="chk_critique_priority"),
    )

    prediction = relationship("ViralityPrediction", back_populates="critiques")


class AuditLog(Base):
    __tablename__ = "auditlogs"

    log_id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True)
    action_type = Column(String(100), nullable=False)
    ip_address = Column(String(45), nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

