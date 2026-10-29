<!-- Plain-English description: Documentation for the VibeCheck backend API, execution instructions, dev credentials, and test commands. -->

# VibeCheck Backend API

FastAPI backend providing REST endpoints for user authentication, video uploads, virality analysis retrieval, and administrator creator metrics.

## Dev Credentials (DEV ONLY)

> [!WARNING]
> These credentials and password hashes are strictly for local testing and development. Never use in production.

- **Creator Account:**
  - **Email:** `creator@vibecheck.test`
  - **Password:** `CreatorDevPassword123!`
  - **Role:** `CREATOR`
- **Admin Account:**
  - **Email:** `admin@vibecheck.test`
  - **Password:** `AdminDevPassword123!`
  - **Role:** `ADMIN`

## Setup & Key Generation

Before running the API for the first time, generate the dev RS256 RSA keypair:
```bash
python scripts/generate_keys.py
```
This generates `jwt_rs256.key` (private key) and `jwt_rs256.key.pub` (public key).

## Running the API

To start the FastAPI backend server with hot-reload:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger documentation will be accessible at:
`http://localhost:8000/docs`

## Running the Tests

To run the complete pytest test suite covering all 8 requirements (login, wrong credentials, tampered JWT, expired JWT, non-MP4 rejection, creator video authorization, admin access, and 10 req/min rate limiting):
```bash
python -m pytest backend/tests/test_api.py -v
```

## API Endpoints

1. `POST /api/v1/auth/login` (email, password): Validates Argon2id hash, returns RS256-signed JWT with 15-minute expiration.
2. `POST /api/v1/videos/upload` (file, persona_id, caption): Accepts MP4 up to 50MB, saves to `/backend/storage`, writes to database, triggers Celery `process_video(video_id)` task, returns 202 Accepted.
3. `GET /api/v1/analysis/{id}`: Returns virality score, audience fit, and critiques. CREATOR can only access their own videos (403 otherwise); ADMIN can read all. Returns status `"PROCESSING"` if analysis is pending.
4. `GET /api/v1/metrics/view` (timeframe, niche_id): ADMIN-only endpoint reading aggregate performance metrics from `v_creator_performance_summary`.

