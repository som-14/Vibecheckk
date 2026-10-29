# Plain-English description: Defines the Celery background task for analyzing video virality, generating critiques, and saving results via stored procedure.

import logging
from sqlalchemy import text
import backend.database as db_mod
from backend.models import Video, ViralityPrediction, AgentCritique, AuditLog
from worker.celery_app import celery_app
from worker.mock_models import (
    mock_transcribe,
    mock_count_cuts_first_3_seconds,
    mock_compute_virality_score,
    mock_audience_fit,
    mock_generate_critiques
)

logger = logging.getLogger(__name__)

def classify_virality_score(score: float) -> str:
    # Classifies numerical virality score into: VIRAL (>=70), AVERAGE (40-69), LOW (<40)
    if score >= 70.0:
        return "VIRAL"
    elif score >= 40.0:
        return "AVERAGE"
    else:
        return "LOW"

def record_analysis_fallback(
    db,
    video_id: str,
    virality_score: float,
    audience_fit: float,
    classification: str,
    critique_role: str,
    feedback: str,
    marker_sec: float,
    priority: str
):
    # Python implementation matching the exact atomic logic of sp_record_virality_and_critiques
    # Used when running against SQLite in test environments
    prediction = db.query(ViralityPrediction).filter(ViralityPrediction.video_id == video_id).first()
    is_new = False

    if not prediction:
        is_new = True
        prediction = ViralityPrediction(
            video_id=video_id,
            virality_score=virality_score,
            audience_fit_score=audience_fit,
            classification=classification
        )
        db.add(prediction)
        db.flush()

    critique = AgentCritique(
        prediction_id=prediction.prediction_id,
        agent_role=critique_role,
        feedback_text=feedback,
        timestamp_marker=marker_sec,
        priority=priority
    )
    db.add(critique)

    if is_new:
        video = db.query(Video).filter(Video.video_id == video_id).first()
        user_id = video.user_id if video else None
        audit = AuditLog(
            user_id=user_id,
            action_type="ANALYSIS_PERSISTED"
        )
        db.add(audit)

    db.commit()

@celery_app.task(
    bind=True,
    name="process_video",
    max_retries=3,
    default_retry_delay=5
)
def process_video(self, video_id: str):
    logger.info(f"Starting analysis for video_id: {video_id}")
    try:
        # Step 1: Call mock multimodal AI models
        transcript = mock_transcribe(video_id)
        cut_count = mock_count_cuts_first_3_seconds(video_id)
        virality_score = mock_compute_virality_score(cut_count=cut_count, transcript_len=len(transcript))
        audience_fit = mock_audience_fit()
        critiques = mock_generate_critiques(virality_score=virality_score, cut_count=cut_count)

        # Step 2: Classify the virality score
        classification = classify_virality_score(virality_score)

        # Step 3: Persist results by calling the stored procedure sp_record_virality_and_critiques once per critique
        db = db_mod.SessionLocal()
        try:
            for critique in critiques:
                if db_mod.engine.dialect.name == "postgresql":
                    db.execute(
                        text("""
                            CALL sp_record_virality_and_critiques(
                                :video_id,
                                :virality_score,
                                :audience_fit,
                                :classification,
                                :critique_role,
                                :feedback,
                                :marker_sec,
                                :priority
                            )
                        """),
                        {
                            "video_id": video_id,
                            "virality_score": virality_score,
                            "audience_fit": audience_fit,
                            "classification": classification,
                            "critique_role": critique["agent_role"],
                            "feedback": critique["feedback_text"],
                            "marker_sec": critique.get("timestamp_marker"),
                            "priority": critique["priority"]
                        }
                    )
                    db.commit()
                else:
                    record_analysis_fallback(
                        db,
                        video_id=video_id,
                        virality_score=virality_score,
                        audience_fit=audience_fit,
                        classification=classification,
                        critique_role=critique["agent_role"],
                        feedback=critique["feedback_text"],
                        marker_sec=critique.get("timestamp_marker"),
                        priority=critique["priority"]
                    )
        finally:
            db.close()

        logger.info(f"Analysis completed successfully for video_id: {video_id} (Score: {virality_score}, Class: {classification})")
        return {
            "video_id": video_id,
            "virality_score": virality_score,
            "classification": classification,
            "critique_count": len(critiques)
        }

    except Exception as exc:
        logger.error(f"Task process_video failed for {video_id}: {exc}")
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task process_video for {video_id} (attempt {self.request.retries + 1} of {self.max_retries})")
            raise self.retry(exc=exc, countdown=5)
        raise exc
