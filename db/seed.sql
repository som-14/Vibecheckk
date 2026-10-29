-- This file seeds initial sample data: 2 users (1 CREATOR, 1 ADMIN), 3 personas, and 1 sample video.

-- 1. Seed Users (1 CREATOR, 1 ADMIN) with real Argon2id password hashes for testing
-- Dev Passwords:
-- creator@vibecheck.test -> CreatorDevPassword123!
-- admin@vibecheck.test   -> AdminDevPassword123!
INSERT INTO Users (user_id, email, password_hash, role)
VALUES
    ('11111111-1111-1111-1111-111111111111', 'creator@vibecheck.test', '$argon2id$v=19$m=65536,t=3,p=4$PUW56YtEJRIEEkSgBBuZVQ$pCbefVvmHLp02mVA/8hUJBUKQgubQFe6o2FlKnmuCB0', 'CREATOR'),
    ('22222222-2222-2222-2222-222222222222', 'admin@vibecheck.test', '$argon2id$v=19$m=65536,t=3,p=4$WFFGlKvQfR+v9Kd6vefVqQ$F0lFmMNkLg4Xl8vuY293W6CHgty8qqkI4ylHohPFjWE', 'ADMIN')
ON CONFLICT (email) DO UPDATE
SET password_hash = EXCLUDED.password_hash;

-- 2. Seed Target Personas (3 target demographics)
INSERT INTO TargetPersonas (persona_id, name, min_age, max_age)
VALUES
    (1, 'Gen Z Trendsetters', 14, 24),
    (2, 'Millennial Techies', 25, 40),
    (3, 'General Casual Viewers', 18, 65)
ON CONFLICT (persona_id) DO NOTHING;

-- 3. Seed Sample Video (associated with the CREATOR user and Persona 1)
INSERT INTO Videos (video_id, user_id, persona_id, blob_url, caption, duration_seconds, uploaded_at)
VALUES
    (
        '33333333-3333-3333-3333-333333333333',
        '11111111-1111-1111-1111-111111111111',
        1,
        'https://storage.vibecheck.test/videos/sample_hook_test.mp4',
        'Check out my new hook strategy! #growth #vibes',
        24,
        NOW()
    )
ON CONFLICT (video_id) DO NOTHING;
