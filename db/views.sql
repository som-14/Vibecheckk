-- This file defines analytical views for tracking creator performance in VibeCheck.

CREATE OR REPLACE VIEW v_creator_performance_summary AS
SELECT
    u.user_id,
    u.email,
    COUNT(vp.prediction_id) AS total_videos_analyzed,
    COALESCE(ROUND(AVG(vp.virality_score), 2), 0.00) AS mean_virality_score,
    COUNT(CASE WHEN vp.classification = 'VIRAL' THEN 1 END) AS viral_hit_count,
    COALESCE(
        ROUND(
            (COUNT(CASE WHEN vp.classification = 'VIRAL' THEN 1 END)::NUMERIC / NULLIF(COUNT(vp.prediction_id), 0)) * 100.0,
            2
        ),
        0.00
    ) AS viral_success_rate_pct
FROM Users u
LEFT JOIN Videos v ON u.user_id = v.user_id
LEFT JOIN ViralityPredictions vp ON v.video_id = vp.video_id
WHERE u.role = 'CREATOR'
GROUP BY u.user_id, u.email;

