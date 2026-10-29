-- This file defines triggers for automated audit logging upon video upload.

CREATE OR REPLACE FUNCTION fn_audit_video_upload()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert an audit log entry for the new video upload.
    -- Note: ip_address is left NULL because inet_client_addr() returns the backend connection IP rather than the end-user's client IP.
    INSERT INTO AuditLogs (user_id, action_type, ip_address, timestamp)
    VALUES (NEW.user_id, 'VIDEO_UPLOAD_INITIATED', NULL, NOW());
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_audit_video_upload ON Videos;

CREATE TRIGGER trg_audit_video_upload
AFTER INSERT ON Videos
FOR EACH ROW
EXECUTE FUNCTION fn_audit_video_upload();

