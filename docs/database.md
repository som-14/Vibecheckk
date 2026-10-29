<!-- Plain-English description: This document specifies the database design, entity-relationship diagram, 3NF normalization justification, and indexing rationale for VibeCheck. -->

# VibeCheck Database Documentation

## 1. Entity-Relationship Diagram (ERD)

```mermaid
erDiagram
    Users ||--o{ Videos : "uploads"
    Users ||--o{ AuditLogs : "generates"
    TargetPersonas ||--o{ Videos : "targeted_by"
    Videos ||--|| ViralityPredictions : "evaluates"
    ViralityPredictions ||--o{ AgentCritiques : "receives"

    Users {
        uuid user_id PK
        string email UK
        string password_hash
        string role
    }

    TargetPersonas {
        int persona_id PK
        string name
        int min_age
        int max_age
    }

    Videos {
        uuid video_id PK
        uuid user_id FK
        int persona_id FK
        string blob_url
        string caption
        int duration_seconds
        timestamptz uploaded_at
    }

    ViralityPredictions {
        uuid prediction_id PK
        uuid video_id FK,UK
        numeric virality_score
        numeric audience_fit_score
        string classification
        timestamptz created_at
    }

    AgentCritiques {
        bigint critique_id PK
        uuid prediction_id FK
        string agent_role
        string feedback_text
        numeric timestamp_marker
        string priority
    }

    AuditLogs {
        bigint log_id PK
        uuid user_id FK
        string action_type
        inet ip_address
        timestamptz timestamp
    }
```

## 2. Third Normal Form (3NF) Justification

The VibeCheck schema adheres to Third Normal Form (3NF) standards:

1. **First Normal Form (1NF)**: All attributes hold atomic, scalar values (no nested lists or arrays), each table contains a well-defined primary key, and rows are uniquely identifiable with no repeating column groups.
2. **Second Normal Form (2NF)**: Meeting 1NF, every non-key column is fully functionally dependent on the complete primary key of its table, with no partial key dependencies.
3. **Third Normal Form (3NF)**: Meeting 2NF, no non-key attribute transitively depends on any other non-key attribute. Attributes belong strictly to their core entities: user credentials reside in `Users`, demographic constraints in `TargetPersonas`, video metadata in `Videos`, quantitative virality metrics in `ViralityPredictions`, and individual qualitative assessments in `AgentCritiques`.

## 3. Index Strategy

- `idx_videos_user_upload`: Accelerates creator dashboard queries retrieving videos filtered by `user_id` and ordered chronologically by `uploaded_at DESC`.
- `idx_pred_class_score`: Accelerates virality dashboard queries filtering by `classification` (e.g., 'VIRAL') and sorting by `virality_score`, while covering `video_id` to eliminate heap lookups.
- `idx_users_email`: Accelerates lookup by email during login and authentication (the UNIQUE constraint establishes an automatic backing index; this explicit index documents and ensures indexed access without conflict).

