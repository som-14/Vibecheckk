-- This file defines stored procedures and security roles for recording virality analysis, critiques, and append-only audit logging.

-- Procedure: sp_record_virality_and_critiques
-- IMPORTANT NOTE ON TRANSACTIONS:
-- PostgreSQL does not allow explicit COMMIT or ROLLBACK statements inside a block that has an EXCEPTION handler.
-- Therefore, this procedure is written as a single unified atomic transaction without inner exception blocks or manual COMMIT/ROLLBACK.
-- If any error occurs during execution, the surrounding PostgreSQL transaction automatically rolls back all changes.

CREATE OR REPLACE PROCEDURE sp_record_virality_and_critiques(
    p_video_id UUID,
    p_virality_score NUMERIC,
    p_audience_fit NUMERIC,
    p_classification VARCHAR,
    p_critique_role VARCHAR,
    p_feedback TEXT,
    p_marker_sec NUMERIC,
    p_priority VARCHAR
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_prediction_id UUID;
    v_is_new BOOLEAN := FALSE;
    v_user_id UUID;
BEGIN
    -- 1. Check if a prediction already exists for this video
    SELECT prediction_id INTO v_prediction_id
    FROM ViralityPredictions
    WHERE video_id = p_video_id;

    -- 2. If it does not exist, insert it and mark as new
    IF v_prediction_id IS NULL THEN
        v_is_new := TRUE;
        INSERT INTO ViralityPredictions (
            video_id,
            virality_score,
            audience_fit_score,
            classification,
            created_at
        )
        VALUES (
            p_video_id,
            p_virality_score,
            p_audience_fit,
            p_classification,
            NOW()
        )
        ON CONFLICT (video_id) DO UPDATE
            SET virality_score = EXCLUDED.virality_score
        RETURNING prediction_id INTO v_prediction_id;
    END IF;

    -- 3. Insert the critique record linked to the prediction
    INSERT INTO AgentCritiques (
        prediction_id,
        agent_role,
        feedback_text,
        timestamp_marker,
        priority
    )
    VALUES (
        v_prediction_id,
        p_critique_role,
        p_feedback,
        p_marker_sec,
        p_priority
    );

    -- 4. Insert an AuditLogs record only when the prediction was newly created
    IF v_is_new THEN
        SELECT user_id INTO v_user_id
        FROM Videos
        WHERE video_id = p_video_id;

        INSERT INTO AuditLogs (
            user_id,
            action_type,
            ip_address,
            timestamp
        )
        VALUES (
            v_user_id,
            'ANALYSIS_PERSISTED',
            NULL,
            NOW()
        );
    END IF;
END;
$$;

-- Security Role & Append-Only AuditLogs:
-- An application role (app_role) is defined with append-only access to AuditLogs.
-- Granting SELECT and INSERT allows logging actions and querying history, while explicitly
-- revoking UPDATE and DELETE guarantees that audit records cannot be altered or removed.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'app_role') THEN
        CREATE ROLE app_role;
    END IF;
END
$$;

GRANT SELECT, INSERT ON AuditLogs TO app_role;
REVOKE UPDATE, DELETE ON AuditLogs FROM app_role;

