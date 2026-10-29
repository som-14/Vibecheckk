<!-- Plain-English description: Cloud architecture documentation detailing the planned Microsoft Azure production deployment layout for VibeCheck. -->

# VibeCheck Planned Azure Architecture

All cloud infrastructure elements described in this document are design specifications and are marked as **Planned**.

## 1. Planned Cloud Architecture Diagram

```mermaid
flowchart TD
    subgraph Internet["Public Internet"]
        Creator["Creator Web Browser"]
    end

    subgraph AzureSub["Azure Subscription"]
        subgraph RG["Resource Group: rg-vibecheck-production-eastus (Planned)"]
            
            subgraph SecurityTier["Identity & Secrets Management"]
                KV["Azure Key Vault (Planned)<br/>- RS256 Private/Public Keys<br/>- DB Credentials<br/>- Storage Connection Strings"]
            end

            subgraph ComputeTier["Azure Container Apps Environment (Planned)"]
                BackendApp["Container App: vibecheck-backend (Planned)<br/>FastAPI API Gateway<br/>Autoscaling: 1 to 10 replicas"]
                WorkerApp["Container App: vibecheck-worker (Planned)<br/>Celery / Event Consumer<br/>Autoscaling driven by queue depth"]
            end

            subgraph MessagingTier["Enterprise Messaging"]
                ASB["Azure Service Bus (Planned)<br/>Topic: video-processing<br/>Queue: process-video-queue"]
            end

            subgraph StorageTier["Data & Content Storage"]
                BlobStorage["Azure Blob Storage (Planned)<br/>Container: raw-videos (Hot Tier)<br/>Container: thumbnails (Cool Tier)"]
                PostgresFlex["Azure Database for PostgreSQL<br/>Flexible Server (Planned)<br/>- 6 Relational Tables<br/>- Audit Logs & Views"]
                CosmosDB["Azure Cosmos DB NoSQL (Planned)<br/>- Transcripts & Frame Payloads"]
            end

            subgraph AnalyticsTier["Business Intelligence"]
                PowerBI["Power BI DirectQuery (Planned)<br/>- Hook Pacing Dashboard<br/>- Niche Virality Heatmap<br/>- Retention Drop-Off"]
            end
        end
    end

    Creator -->|HTTPS / RS256 Bearer Token| BackendApp
    BackendApp -->|Store Video MP4| BlobStorage
    BackendApp -->|Record Metadata & Audit| PostgresFlex
    BackendApp -->|Publish process_video Task| ASB
    BackendApp -->|Read Secrets / Keys| KV

    ASB -->|Pull Video Task| WorkerApp
    WorkerApp -->|Read Video Stream| BlobStorage
    WorkerApp -->|Read Secrets| KV
    WorkerApp -->|Store Structured Scores| PostgresFlex
    WorkerApp -->|Store Transcripts & Analysis JSON| CosmosDB

    PowerBI -->|DirectQuery Reporting| PostgresFlex
    PowerBI -->|Read Analytical Payloads| CosmosDB
```

## 2. Planned Azure Component Mapping

| Azure Component | Resource Name | Role / Function | Status |
|---|---|---|---|
| **Resource Group** | `rg-vibecheck-production-eastus` | Logical container for all project assets in East US | Planned |
| **Azure Container Apps (API)** | `ca-vibecheck-api` | Hosts the containerized FastAPI backend with TLS termination | Planned |
| **Azure Container Apps (Worker)** | `ca-vibecheck-worker` | Hosts background worker scale-out instances | Planned |
| **PostgreSQL Flexible Server** | `psql-vibecheck-prod` | Manages relational schema, views, audit tables, and stored procedures | Planned |
| **Azure Blob Storage** | `stgvideoanalysesprod` | High-throughput object store for video uploads and media assets | Planned |
| **Azure Cosmos DB** | `cosmos-vibecheck-transcripts` | Document store for variable-length Whisper transcripts and agent evaluations | Planned |
| **Azure Service Bus** | `sb-vibecheck-messaging` | Production asynchronous message broker replacing local Redis | Planned |
| **Azure Key Vault** | `kv-vibecheck-secrets` | Centralized hardware security module for RSA keys and database credentials | Planned |
| **Power BI Service** | `pbi-vibecheck-workspace` | Executive and creator reporting powered by DirectQuery | Planned |
