<!-- Plain-English description: High-level system design document for VibeCheck, detailing the system architecture, API specifications, and asynchronous queue trade-offs. -->

# VibeCheck System Design

## 1. System Architecture

```mermaid
flowchart TD
    subgraph ClientLayer["Client Layer"]
        Client["Next.js Web Client<br/>(React 18 / Pages Router)"]
    end

    subgraph APILayer["API Gateway & Service Layer"]
        FastAPI["FastAPI Backend<br/>(REST API / SQLAlchemy)"]
    end

    subgraph StorageLayer["Data & Messaging Tier"]
        Postgres[("PostgreSQL 15<br/>(Metadata, Analysis, Auditing)")]
        RedisQueue[("Redis Queue<br/>(Asynchronous Task Broker)")]
        BlobStorage[("Local / Blob Storage<br/>(Raw MP4 Video Files)")]
    end

    subgraph WorkerLayer["Processing Layer"]
        Worker["Celery Worker<br/>(Multimodal Analysis Pipeline)"]
    end

    Client -->|1. Authenticate & Upload| FastAPI
    FastAPI -->|2. Store Metadata| Postgres
    FastAPI -->|3. Store Video File| BlobStorage
    FastAPI -->|4. Enqueue Task| RedisQueue
    RedisQueue -->|5. Consume Task| Worker
    Worker -->|6. Fetch Video / Mock Models| Worker
    Worker -->|7. Persist Scores & Critiques| Postgres
    Client -->|8. Poll Analysis Status (every 3s)| FastAPI
    FastAPI -->|9. Read Results| Postgres
```

## 2. API Endpoints

| Method | Endpoint | Request Payload | Response Status | Status | Description |
|---|---|---|---|---|---|
| `POST` | `/api/v1/auth/login` | `{"email": "string", "password": "string"}` | `200 OK` / `401 Unauthorized` | Implemented | Verifies Argon2id password hash, returns RS256-signed JWT valid for 15 minutes. |
| `POST` | `/api/v1/videos/upload` | `multipart/form-data`<br/>(`file`: MP4 file, `persona_id`: int, `caption`: string) | `202 Accepted` / `400` / `413` | Implemented | Validates MP4 extension, enforces 50MB limit, writes to storage, creates `Videos` record, enqueues `process_video`. |
| `GET` | `/api/v1/analysis/{id}` | Path param: `id` (UUID)<br/>Header: `Bearer <token>` | `200 OK` / `403` / `404` | Implemented | Returns `"status": "PROCESSING"` if pending, or score, audience fit, and critiques if completed. Creators can only access their own videos; Admins can access all. |
| `GET` | `/api/v1/metrics/view` | Query: `timeframe`, `niche_id`<br/>Header: `Bearer <token>` (Admin) | `200 OK` / `403 Forbidden` | Implemented | Queries `v_creator_performance_summary` for creator performance analytics. Restricted to ADMIN role. |

## 3. Trade-Off Analysis: Asynchronous Queue vs. Synchronous Request

Video evaluation requires executing multimodal analysis models (transcription, cut detection, viral metric computation, and multi-agent critique generation). In production, this pipeline takes **18 to 45 seconds** per short video.

### Why an Asynchronous Queue Beats a Synchronous Request
1. **Prevents Gateway Timeouts (HTTP 504):** Reverse proxies, load balancers, and cloud gateways typically have request timeouts set to 30 or 60 seconds. A synchronous pipeline risks frequent 504 Gateway Timeout errors under slight load or longer videos.
2. **Eliminates Thread Exhaustion:** In a synchronous request model, web server worker threads remain blocked for the full 45 seconds waiting for AI inferences to finish. This rapidly exhausts thread pools and prevents other users from logging in or viewing dashboards.
3. **Decoupled Scaling:** Queue consumers (workers) scale independently based on message backlog length, completely isolated from web traffic spikes.
4. **Resilience & Retries:** Tasks that fail due to transient model timeouts or service disruptions can be retried automatically (up to 3 times) without forcing the end user to restart the upload.

### The Trade-off & Cost
- **Eventual Consistency:** The response is not immediate. The upload endpoint returns `202 Accepted` with a `video_id` in milliseconds.
- **Client Polling Overhead:** The client must manage polling (querying `GET /api/v1/analysis/{id}` every 3 seconds) until the analysis transitions from `PROCESSING` to `COMPLETED`.
