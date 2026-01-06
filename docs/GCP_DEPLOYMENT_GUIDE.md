# Google Cloud Platform Deployment Guide for A2A Multi-Agent System

**Version:** 2.0
**Last Updated:** December 31, 2025
**Target Platform:** Google Cloud Platform (Vertex AI + Cloud Run)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Deployment Architecture Overview](#deployment-architecture-overview)
3. [Deployment Options Comparison](#deployment-options-comparison)
4. [Cloud Run Deployment (Recommended)](#cloud-run-deployment-recommended)
5. [Vertex AI Agent Engine Deployment](#vertex-ai-agent-engine-deployment)
6. [A2A Protocol Production Requirements](#a2a-protocol-production-requirements)
7. [Service-by-Service Deployment Guide](#service-by-service-deployment-guide)
8. [Database Migration](#database-migration)
9. [Security & Authentication](#security--authentication)
10. [Observability & Monitoring](#observability--monitoring)
11. [Cost Analysis](#cost-analysis)
12. [Migration Checklist](#migration-checklist)
13. [References](#references)

---

## Executive Summary

This guide provides comprehensive instructions for deploying the Agentic Jarvis multi-agent system to Google Cloud Platform using production-ready configurations aligned with Google's official A2A protocol recommendations.

### Key Highlights

- **Production-Ready A2A Deployment**: Google ADK v1.0.0+ is production-ready as of May 2025
- **A2A Protocol v0.3**: Latest version with gRPC support and security card signing
- **Two Primary Deployment Paths**:
  - **Cloud Run** (Recommended for flexibility): Containerized microservices with full control
  - **Vertex AI Agent Engine**: Managed runtime optimized for ADK agents (GA in 2025)
- **150+ Organizations** supporting A2A protocol (Google, Salesforce, ServiceNow, PayPal, etc.)

### Current Architecture

```
┌─────────────────────────────────────────┐
│   6 FastAPI Services (Local)            │
├─────────────────────────────────────────┤
│ Auth Service          :9998             │
│ Registry Service      :8003             │
│ Tickets Agent         :8080             │
│ FinOps Agent          :8081             │
│ Oxygen Agent          :8082             │
│ Web UI                :9999             │
└─────────────────────────────────────────┘
```

### Target GCP Architecture

```
┌────────────────────────────────────────────────────────────┐
│                   Google Cloud Platform                     │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐                                           │
│  │ Cloud Load  │ ──┐                                       │
│  │  Balancer   │   │                                       │
│  └─────────────┘   │                                       │
│         │           │                                       │
│         │           │  ┌──────────────────────────────┐   │
│         │           └──│   Cloud Armor (WAF/DDoS)     │   │
│         │              └──────────────────────────────┘   │
│         │                                                  │
│    ┌────┴───────────────────────────────────────┐        │
│    │        Cloud Run Services (Serverless)     │        │
│    ├───────────────────────────────────────────┤        │
│    │ auth-service        (internal + IAM)       │        │
│    │ registry-service    (internal + IAM)       │        │
│    │ tickets-agent       (A2A + IAM)            │        │
│    │ finops-agent        (A2A + IAM)            │        │
│    │ oxygen-agent        (A2A + IAM)            │        │
│    │ web-ui              (public)               │        │
│    └─────────────┬──────────────────────────────┘        │
│                  │                                         │
│         ┌────────┴─────────┐                              │
│         │   VPC Network    │                              │
│         │ (Private Access) │                              │
│         └────────┬─────────┘                              │
│                  │                                         │
│    ┌─────────────┴──────────────┐                        │
│    │  Cloud SQL PostgreSQL      │                        │
│    │  (Managed Database)        │                        │
│    └────────────────────────────┘                        │
│                                                            │
│    ┌────────────────────────────┐                        │
│    │  Secret Manager            │                        │
│    │  (API Keys, JWT Secret)    │                        │
│    └────────────────────────────┘                        │
│                                                            │
│    ┌────────────────────────────┐                        │
│    │  Artifact Registry         │                        │
│    │  (Docker Images)           │                        │
│    └────────────────────────────┘                        │
│                                                            │
│    ┌────────────────────────────┐                        │
│    │  Cloud Monitoring          │                        │
│    │  Cloud Logging             │                        │
│    │  Cloud Trace               │                        │
│    └────────────────────────────┘                        │
│                                                            │
│    ┌────────────────────────────┐                        │
│    │  Vertex AI                 │                        │
│    │  (Gemini 2.5 Flash)        │                        │
│    └────────────────────────────┘                        │
└────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture Overview

### Architecture Principles

1. **Microservices Pattern**: Each agent and service deployed independently
2. **A2A Protocol Compliance**: Agent cards at `/.well-known/agent-card.json`
3. **Zero-Trust Security**: Service-to-service IAM authentication
4. **Serverless-First**: Auto-scaling with Cloud Run
5. **Observability**: Cloud Trace for distributed tracing across A2A calls

### GCP Services Used

| Service | Purpose | Cost Model |
|---------|---------|------------|
| **Cloud Run** | Containerized agent hosting | Pay-per-use (CPU, Memory, Requests) |
| **Cloud SQL** | PostgreSQL database | Instance + Storage |
| **Secret Manager** | Secure credential storage | Per secret/access |
| **Artifact Registry** | Docker image storage | Storage-based |
| **Cloud Load Balancer** | Traffic routing | Data processed |
| **Cloud Armor** | DDoS/WAF protection | Rules + Requests |
| **Cloud Monitoring** | Observability | Log volume |
| **Vertex AI** | Gemini model access | Token-based |

---

## Deployment Options Comparison

### Option 1: Cloud Run (Recommended)

**Best For**: Production deployments requiring flexibility, control, and cost optimization

✅ **Advantages**:
- Full control over container configuration
- Flexible autoscaling (0-1000 instances)
- Direct VPC egress (no connector required in 2025)
- Native Cloud Armor integration via Load Balancer
- ADK deployment with single command: `adk deploy cloud_run`
- Supports multi-container deployments (sidecars for OTel)
- Cold start optimization: 30-40% reduction with startup CPU boost
- Free tier: 2M requests/month, 180K vCPU-seconds, 360K GiB-seconds

❌ **Considerations**:
- Requires Docker expertise
- Manual orchestration of multiple services
- Cold starts (mitigable with min-instances)
- VPS 50%+ cheaper for sustained traffic

**Use Cases**:
- Multi-agent A2A architectures (like Agentic Jarvis)
- Bursty or unpredictable traffic
- Need for custom networking (VPC)
- Integration with existing GCP infrastructure

### Option 2: Vertex AI Agent Engine

**Best For**: Rapid deployment with managed sessions and memory

✅ **Advantages**:
- Fully managed runtime (no Docker needed)
- Built-in sessions + Memory Bank (GA in 2025)
- One-command deployment: `adk deploy agent_engine`
- Automatic tracing, logging, monitoring
- Enterprise SRE controls
- 7 global regions available
- Free tier available

❌ **Considerations**:
- Less flexible than Cloud Run (opinionated)
- Doesn't include ADK web UI by default
- Relatively new service (needs maturity - Aug 2025 assessment)
- Limited customization of runtime environment

**Use Cases**:
- Single-agent deployments
- Need for managed memory/sessions
- Teams without DevOps resources
- Prototypes requiring quick deployment

### Recommendation for Agentic Jarvis

**Use Cloud Run** because:
1. **6 independent services**: Auth, Registry, 3 agents, Web UI
2. **Custom networking**: Service-to-service authentication
3. **Existing FastAPI architecture**: Already containerized
4. **A2A requirements**: Need control over agent card endpoints
5. **JWT authentication**: Custom middleware integration

Agent Engine is better suited for **single-agent** deployments or when you need managed memory services.

---

## Cloud Run Deployment (Recommended)

### Prerequisites

```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Install ADK CLI (optional, for adk deploy command)
pip install google-adk[a2a]

# Login and set project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  sql-component.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  cloudtrace.googleapis.com \
  cloudprofiler.googleapis.com \
  compute.googleapis.com
```

### 1. Setup Artifact Registry

```bash
# Create Docker repository
gcloud artifacts repositories create agentic-jarvis \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker images for Agentic Jarvis agents"

# Configure Docker authentication
gcloud auth configure-docker us-central1-docker.pkg.dev
```

### 2. Setup Secret Manager

```bash
# Create secrets
echo -n "YOUR_GOOGLE_API_KEY" | gcloud secrets create google-api-key --data-file=-
echo -n "YOUR_JWT_SECRET" | gcloud secrets create jwt-secret-key --data-file=-

# Grant Cloud Run access (replace with your Cloud Run service account)
gcloud secrets add-iam-policy-binding google-api-key \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding jwt-secret-key \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 3. Setup Cloud SQL PostgreSQL

```bash
# Create Cloud SQL instance (Enterprise edition)
gcloud sql instances create agentic-jarvis-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1 \
  --availability-type=zonal \
  --backup-start-time=03:00 \
  --storage-type=SSD \
  --storage-size=10GB \
  --storage-auto-increase \
  --edition=enterprise

# Set root password
gcloud sql users set-password postgres \
  --instance=agentic-jarvis-db \
  --password=YOUR_DB_PASSWORD

# Create application database
gcloud sql databases create jarvis \
  --instance=agentic-jarvis-db

# Create database user
gcloud sql users create jarvis_app \
  --instance=agentic-jarvis-db \
  --password=YOUR_APP_PASSWORD

# Store connection string in Secret Manager
gcloud secrets create db-connection-string \
  --data-file=- <<EOF
postgresql://jarvis_app:YOUR_APP_PASSWORD@/jarvis?host=/cloudsql/YOUR_PROJECT_ID:us-central1:agentic-jarvis-db
EOF
```

### 4. Build and Push Docker Images

#### Option A: Manual Build (Full Control)

Create Dockerfiles for each service (see [Service-by-Service Guide](#service-by-service-deployment-guide)):

```bash
# Set variables
PROJECT_ID="your-project-id"
REGION="us-central1"
REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/agentic-jarvis"

# Build and push all services
services=("auth-service" "registry-service" "tickets-agent" "finops-agent" "oxygen-agent" "web-ui")

for service in "${services[@]}"; do
  docker build -t ${REGISTRY}/${service}:latest -f ${service}/Dockerfile .
  docker push ${REGISTRY}/${service}:latest
done
```

#### Option B: ADK Deploy (Simplified)

For agent services using ADK:

```bash
cd tickets_agent_service
adk deploy cloud_run \
  --project=$PROJECT_ID \
  --region=us-central1 \
  --service-name=tickets-agent \
  --memory=1Gi \
  --cpu=1 \
  --max-instances=10 \
  --min-instances=0
```

**Note**: ADK's `adk deploy cloud_run` automatically:
- Bundles your agent code
- Creates container configuration
- Builds Docker image
- Pushes to Artifact Registry
- Deploys to Cloud Run

### 5. Deploy Services to Cloud Run

#### A. Auth Service (Internal)

```bash
gcloud run deploy auth-service \
  --image=us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/auth-service:latest \
  --platform=managed \
  --region=us-central1 \
  --port=9998 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=5 \
  --ingress=internal-and-cloud-load-balancing \
  --no-allow-unauthenticated \
  --set-secrets=JWT_SECRET_KEY=jwt-secret-key:latest \
  --update-env-vars=LOG_LEVEL=INFO,CORS_ORIGINS=*
```

#### B. Registry Service (Internal)

```bash
gcloud run deploy registry-service \
  --image=us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/registry-service:latest \
  --platform=managed \
  --region=us-central1 \
  --port=8003 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=5 \
  --ingress=internal-and-cloud-load-balancing \
  --no-allow-unauthenticated \
  --add-cloudsql-instances=$PROJECT_ID:us-central1:agentic-jarvis-db \
  --set-secrets=DB_CONNECTION_STRING=db-connection-string:latest \
  --update-env-vars=LOG_LEVEL=INFO
```

#### C. Tickets Agent (A2A Endpoint)

```bash
gcloud run deploy tickets-agent \
  --image=us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/tickets-agent:latest \
  --platform=managed \
  --region=us-central1 \
  --port=8080 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=20 \
  --cpu-boost \
  --ingress=internal-and-cloud-load-balancing \
  --no-allow-unauthenticated \
  --add-cloudsql-instances=$PROJECT_ID:us-central1:agentic-jarvis-db \
  --set-secrets=GOOGLE_API_KEY=google-api-key:latest,DB_CONNECTION_STRING=db-connection-string:latest \
  --update-env-vars=LOG_LEVEL=INFO,AUTH_SERVICE_URL=https://auth-service-xxx.run.app
```

#### D. FinOps Agent (A2A Endpoint)

```bash
gcloud run deploy finops-agent \
  --image=us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/finops-agent:latest \
  --platform=managed \
  --region=us-central1 \
  --port=8081 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=20 \
  --cpu-boost \
  --ingress=internal-and-cloud-load-balancing \
  --no-allow-unauthenticated \
  --add-cloudsql-instances=$PROJECT_ID:us-central1:agentic-jarvis-db \
  --set-secrets=GOOGLE_API_KEY=google-api-key:latest,DB_CONNECTION_STRING=db-connection-string:latest \
  --update-env-vars=LOG_LEVEL=INFO,AUTH_SERVICE_URL=https://auth-service-xxx.run.app
```

#### E. Oxygen Agent (A2A Endpoint)

```bash
gcloud run deploy oxygen-agent \
  --image=us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/oxygen-agent:latest \
  --platform=managed \
  --region=us-central1 \
  --port=8082 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=20 \
  --cpu-boost \
  --ingress=internal-and-cloud-load-balancing \
  --no-allow-unauthenticated \
  --add-cloudsql-instances=$PROJECT_ID:us-central1:agentic-jarvis-db \
  --set-secrets=GOOGLE_API_KEY=google-api-key:latest,DB_CONNECTION_STRING=db-connection-string:latest \
  --update-env-vars=LOG_LEVEL=INFO,AUTH_SERVICE_URL=https://auth-service-xxx.run.app
```

#### F. Web UI (Public)

```bash
gcloud run deploy web-ui \
  --image=us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/web-ui:latest \
  --platform=managed \
  --region=us-central1 \
  --port=9999 \
  --memory=512Mi \
  --cpu=1 \
  --min-instances=1 \
  --max-instances=10 \
  --ingress=all \
  --allow-unauthenticated \
  --update-env-vars=REGISTRY_SERVICE_URL=https://registry-service-xxx.run.app
```

### 6. Configure IAM Permissions

```bash
# Get service account emails
AUTH_SA=$(gcloud run services describe auth-service --region=us-central1 --format='value(spec.template.spec.serviceAccountName)')
REGISTRY_SA=$(gcloud run services describe registry-service --region=us-central1 --format='value(spec.template.spec.serviceAccountName)')
TICKETS_SA=$(gcloud run services describe tickets-agent --region=us-central1 --format='value(spec.template.spec.serviceAccountName)')
FINOPS_SA=$(gcloud run services describe finops-agent --region=us-central1 --format='value(spec.template.spec.serviceAccountName)')
OXYGEN_SA=$(gcloud run services describe oxygen-agent --region=us-central1 --format='value(spec.template.spec.serviceAccountName)')
WEB_SA=$(gcloud run services describe web-ui --region=us-central1 --format='value(spec.template.spec.serviceAccountName)')

# Grant Cloud Run Invoker to services that need to call other services
# Web UI → Registry Service
gcloud run services add-iam-policy-binding registry-service \
  --region=us-central1 \
  --member="serviceAccount:${WEB_SA}" \
  --role="roles/run.invoker"

# All agents → Auth Service
for sa in $TICKETS_SA $FINOPS_SA $OXYGEN_SA; do
  gcloud run services add-iam-policy-binding auth-service \
    --region=us-central1 \
    --member="serviceAccount:${sa}" \
    --role="roles/run.invoker"
done

# Agents → Registry Service (for agent registration)
for sa in $TICKETS_SA $FINOPS_SA $OXYGEN_SA; do
  gcloud run services add-iam-policy-binding registry-service \
    --region=us-central1 \
    --member="serviceAccount:${sa}" \
    --role="roles/run.invoker"
done

# Agent-to-agent calls (A2A)
# FinOps → Tickets
gcloud run services add-iam-policy-binding tickets-agent \
  --region=us-central1 \
  --member="serviceAccount:${FINOPS_SA}" \
  --role="roles/run.invoker"

# Oxygen → Tickets, FinOps
for service in tickets-agent finops-agent; do
  gcloud run services add-iam-policy-binding $service \
    --region=us-central1 \
    --member="serviceAccount:${OXYGEN_SA}" \
    --role="roles/run.invoker"
done
```

### 7. Setup Load Balancer with Cloud Armor

```bash
# Reserve external IP
gcloud compute addresses create agentic-jarvis-ip \
  --global

# Create serverless NEGs for each public service
gcloud compute network-endpoint-groups create web-ui-neg \
  --region=us-central1 \
  --network-endpoint-type=serverless \
  --cloud-run-service=web-ui

# Create backend service
gcloud compute backend-services create agentic-jarvis-backend \
  --global \
  --load-balancing-scheme=EXTERNAL_MANAGED

# Add NEG to backend
gcloud compute backend-services add-backend agentic-jarvis-backend \
  --global \
  --network-endpoint-group=web-ui-neg \
  --network-endpoint-group-region=us-central1

# Create URL map
gcloud compute url-maps create agentic-jarvis-lb \
  --default-service=agentic-jarvis-backend

# Create SSL certificate (managed)
gcloud compute ssl-certificates create agentic-jarvis-cert \
  --domains=your-domain.com \
  --global

# Create HTTPS proxy
gcloud compute target-https-proxies create agentic-jarvis-https-proxy \
  --ssl-certificates=agentic-jarvis-cert \
  --url-map=agentic-jarvis-lb

# Create forwarding rule
gcloud compute forwarding-rules create agentic-jarvis-https-rule \
  --address=agentic-jarvis-ip \
  --global \
  --target-https-proxy=agentic-jarvis-https-proxy \
  --ports=443

# Create Cloud Armor security policy
gcloud compute security-policies create agentic-jarvis-armor \
  --description="DDoS and WAF protection for Agentic Jarvis"

# Add rate limiting rule
gcloud compute security-policies rules create 1000 \
  --security-policy=agentic-jarvis-armor \
  --expression="true" \
  --action=rate-based-ban \
  --rate-limit-threshold-count=1000 \
  --rate-limit-threshold-interval-sec=60 \
  --ban-duration-sec=600 \
  --conform-action=allow \
  --exceed-action=deny-429 \
  --enforce-on-key=IP

# Attach to backend service
gcloud compute backend-services update agentic-jarvis-backend \
  --global \
  --security-policy=agentic-jarvis-armor
```

---

## Vertex AI Agent Engine Deployment

### When to Use Agent Engine

- Single ADK agent deployment
- Need managed sessions + Memory Bank
- Prefer no-Docker approach
- Willing to trade flexibility for simplicity

### Deployment Steps

```bash
# 1. Create agent_engine.yaml configuration
cat > agent_engine.yaml <<EOF
agent:
  name: jarvis-orchestrator
  description: "Multi-agent orchestrator for IT operations"

runtime:
  memory: 2Gi
  cpu: 1
  max_instances: 10
  min_instances: 1

services:
  session_service_uri: "vertexai://session"
  memory_service_uri: "vertexai://memory"

environment:
  - name: GOOGLE_API_KEY
    secret: google-api-key
  - name: LOG_LEVEL
    value: INFO
EOF

# 2. Deploy using ADK CLI
adk deploy agent_engine \
  --project=$PROJECT_ID \
  --region=us-central1 \
  --agent_engine_config_file=agent_engine.yaml

# 3. Get deployment URL
gcloud ai endpoints list --region=us-central1
```

### Memory Bank Integration

```python
from google.adk.sessions import VertexAISessionService
from google.adk.memory import VertexAIMemoryBankService

# Configure memory services
session_service = VertexAISessionService(
    project_id="your-project-id",
    region="us-central1"
)

memory_service = VertexAIMemoryBankService(
    project_id="your-project-id",
    region="us-central1"
)

# Create agent with memory
agent = Agent(
    name="jarvis",
    model="gemini-2.5-flash",
    session_service=session_service,
    memory_service=memory_service
)
```

### Agent Engine Limitations for Agentic Jarvis

❌ **Not recommended because**:
1. Cannot deploy 6 independent services
2. Limited control over networking
3. No native support for separate Auth/Registry services
4. Requires restructuring existing architecture
5. Still maturing (as of August 2025)

---

## A2A Protocol Production Requirements

### 1. Agent Card Requirements

Every A2A agent **MUST** expose an agent card at:

```
https://your-agent-domain/.well-known/agent-card.json
```

**HTTPS Requirements** (Production):
- TLS 1.3+ with strong cipher suites
- Valid SSL certificate from trusted CA
- PQC cipher suites recommended (as available)

**Agent Card Schema**:

```json
{
  "name": "tickets-agent",
  "description": "IT ticket management agent",
  "version": "1.0.0",
  "capabilities": {
    "streaming": true,
    "forms": false,
    "audio": false
  },
  "skills": [
    {
      "name": "create_ticket",
      "description": "Create a new IT support ticket",
      "parameters": {
        "type": "object",
        "properties": {
          "operation": {"type": "string"},
          "user": {"type": "string"}
        }
      }
    }
  ],
  "securitySchemes": {
    "bearerAuth": {
      "type": "http",
      "scheme": "bearer",
      "bearerFormat": "JWT"
    }
  },
  "security": [
    {"bearerAuth": []}
  ],
  "endpoints": {
    "sendMessage": "https://tickets-agent-xxx.run.app/a2a/send_message"
  }
}
```

### 2. Agent Card Endpoint Implementation

**FastAPI Example**:

```python
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

@app.get("/.well-known/agent-card.json")
async def agent_card():
    return JSONResponse({
        "name": "tickets-agent",
        "description": "IT ticket management agent",
        "version": "1.0.0",
        "capabilities": {
            "streaming": True,
            "forms": False,
            "audio": False
        },
        "skills": [...],
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        },
        "security": [{"bearerAuth": []}],
        "endpoints": {
            "sendMessage": "https://tickets-agent-xxx.run.app/a2a/send_message"
        }
    })
```

### 3. RemoteA2aAgent Configuration

**Development (localhost)**:

```python
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

oxygen_agent = RemoteA2aAgent(
    name="oxygen_agent",
    description="Learning & development platform",
    agent_card="http://localhost:8082/.well-known/agent-card.json"
)
```

**Production (Cloud Run)**:

```python
oxygen_agent = RemoteA2aAgent(
    name="oxygen_agent",
    description="Learning & development platform",
    agent_card="https://oxygen-agent-xxx.run.app/.well-known/agent-card.json",
    auth_scheme="bearerAuth",
    auth_credential=lambda: get_service_account_token()
)
```

### 4. Service-to-Service Authentication

**IAM-Based (Recommended for GCP)**:

```python
import google.auth
from google.auth.transport.requests import Request

def get_service_account_token():
    """Generate JWT for calling Cloud Run service with IAM"""
    credentials, project = google.auth.default()

    # Get ID token for Cloud Run
    auth_req = Request()
    credentials.refresh(auth_req)

    return credentials.token
```

**JWT Bearer Token**:

```python
from fastapi import Header, HTTPException

async def verify_jwt(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing or invalid Authorization header")

    token = authorization.split(" ")[1]

    # Verify JWT
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Invalid token")

@app.post("/a2a/send_message", dependencies=[Depends(verify_jwt)])
async def send_message(request: A2ARequest):
    # Handle A2A request
    pass
```

### 5. A2A Protocol v0.3 Features (2025)

✨ **New in v0.3**:
- **gRPC Support**: Lower latency for agent-to-agent calls
- **Security Card Signing**: Verify agent card authenticity
- **Extended Client Support**: Python SDK enhancements

---

## Service-by-Service Deployment Guide

### 1. Auth Service

**Purpose**: JWT authentication and user management

**Dockerfile** (`auth/Dockerfile`):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY auth/ ./auth/
COPY main_auth.py .

# Expose port
EXPOSE 9998

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=9998

# Run server
CMD ["uvicorn", "main_auth:app", "--host", "0.0.0.0", "--port", "9998"]
```

**Environment Variables**:
- `JWT_SECRET_KEY`: From Secret Manager
- `JWT_ALGORITHM`: HS256
- `ACCESS_TOKEN_EXPIRE_MINUTES`: 1440
- `LOG_LEVEL`: INFO

**Cloud Run Configuration**:
- Memory: 512Mi
- CPU: 1
- Min instances: 1 (always warm)
- Max instances: 5
- Ingress: Internal only

---

### 2. Registry Service

**Purpose**: Agent registration and session management

**Dockerfile** (`agent_registry_service/Dockerfile`):

Already exists in your project - use the multi-stage build for optimal size.

**Environment Variables**:
- `DB_CONNECTION_STRING`: From Secret Manager
- `CORS_ORIGINS`: *
- `LOG_LEVEL`: INFO

**Cloud Run Configuration**:
- Memory: 512Mi
- CPU: 1
- Min instances: 1
- Max instances: 5
- Cloud SQL: Enabled
- Ingress: Internal only

**Database Schema**:

```sql
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    url VARCHAR(512) NOT NULL,
    capabilities JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    agent_name VARCHAR(255) NOT NULL,
    context JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (agent_name) REFERENCES agents(name)
);

CREATE INDEX idx_sessions_user ON sessions(user_id);
CREATE INDEX idx_sessions_agent ON sessions(agent_name);
```

---

### 3. Tickets Agent (A2A)

**Purpose**: IT ticket management with A2A protocol

**Dockerfile** (`tickets_agent_service/Dockerfile`):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY jarvis_agent/sub_agents/tickets/ ./tickets_agent/
COPY tickets_agent_service/main.py .

# Expose port
EXPOSE 8080

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Run A2A server
CMD ["python", "main.py"]
```

**main.py** (A2A conversion):

```python
from google.adk.a2a import to_a2a
from tickets_agent.agent import tickets_agent

if __name__ == "__main__":
    # CRITICAL: Always specify port parameter
    app = to_a2a(tickets_agent, port=8080)
    app.run()
```

**Environment Variables**:
- `GOOGLE_API_KEY`: From Secret Manager
- `DB_CONNECTION_STRING`: From Secret Manager
- `AUTH_SERVICE_URL`: https://auth-service-xxx.run.app
- `LOG_LEVEL`: INFO

**Cloud Run Configuration**:
- Memory: 1Gi
- CPU: 1
- Min instances: 0 (scale to zero)
- Max instances: 20
- CPU boost: Enabled (cold start optimization)
- Cloud SQL: Enabled
- Ingress: Internal only

**Agent Card** (`/.well-known/agent-card.json`):

Must be accessible for A2A discovery.

---

### 4. FinOps Agent (A2A)

**Purpose**: Cloud cost analytics with A2A protocol

**Configuration**: Similar to Tickets Agent

**Dockerfile**: Same pattern as Tickets Agent

**Port**: 8081

**Skills**:
- `get_cloud_costs`
- `analyze_spending`
- `forecast_costs`

---

### 5. Oxygen Agent (A2A)

**Purpose**: Learning & development platform with A2A protocol

**Configuration**: Similar to Tickets/FinOps Agents

**Dockerfile**: Same pattern

**Port**: 8082

**Skills**:
- `get_user_courses`
- `get_pending_exams`
- `enroll_course`
- `get_exam_deadlines`

---

### 6. Web UI

**Purpose**: Frontend for user interaction

**Dockerfile** (`web_ui/Dockerfile`):

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY web_ui/ ./web_ui/

# Expose port
EXPOSE 9999

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=9999

# Run server
CMD ["uvicorn", "web_ui.app:app", "--host", "0.0.0.0", "--port", "9999"]
```

**Environment Variables**:
- `REGISTRY_SERVICE_URL`: https://registry-service-xxx.run.app
- `AUTH_SERVICE_URL`: https://auth-service-xxx.run.app

**Cloud Run Configuration**:
- Memory: 512Mi
- CPU: 1
- Min instances: 1
- Max instances: 10
- Ingress: All (public)
- Allow unauthenticated: Yes

---

## Database Migration

### SQLite → Cloud SQL PostgreSQL

**Challenges**:
1. Different SQL dialects
2. Schema differences (TEXT → VARCHAR, INTEGER → BIGINT)
3. No native migration tool

**Recommended Approach**:

#### Step 1: Export SQLite Data

```bash
# Export to CSV
sqlite3 data/tickets.db <<EOF
.headers on
.mode csv
.output tickets_export.csv
SELECT * FROM tickets;
.quit
EOF

sqlite3 data/finops.db <<EOF
.headers on
.mode csv
.output finops_export.csv
SELECT * FROM cloud_costs;
.quit
EOF

sqlite3 data/oxygen.db <<EOF
.headers on
.mode csv
.output oxygen_users_export.csv
SELECT * FROM users;
.output oxygen_courses_export.csv
SELECT * FROM courses;
.quit
EOF
```

#### Step 2: Create Cloud SQL Schemas

```sql
-- Tickets schema
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    operation VARCHAR(100) NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FinOps schema
CREATE TABLE cloud_costs (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    service_name VARCHAR(255) NOT NULL,
    cost DECIMAL(10, 2) NOT NULL,
    period VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Oxygen schemas
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    preferences JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE courses (
    id SERIAL PRIMARY KEY,
    course_name VARCHAR(255) NOT NULL,
    description TEXT,
    duration_hours INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE enrollments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    course_id INTEGER REFERENCES courses(id),
    status VARCHAR(50),
    enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    UNIQUE(user_id, course_id)
);

CREATE TABLE exams (
    id SERIAL PRIMARY KEY,
    course_id INTEGER REFERENCES courses(id),
    exam_name VARCHAR(255) NOT NULL,
    deadline TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_user ON tickets(user_name);
CREATE INDEX idx_cloud_costs_provider ON cloud_costs(provider);
CREATE INDEX idx_enrollments_user ON enrollments(user_id);
CREATE INDEX idx_exams_deadline ON exams(deadline);
```

#### Step 3: Import Data

```bash
# Connect to Cloud SQL
gcloud sql connect agentic-jarvis-db --user=postgres --database=jarvis

# Import CSV data
\copy tickets(id, operation, user_name, status, created_at, updated_at) FROM '/path/to/tickets_export.csv' WITH (FORMAT CSV, HEADER true);
\copy cloud_costs(id, provider, service_name, cost, period, created_at) FROM '/path/to/finops_export.csv' WITH (FORMAT CSV, HEADER true);
\copy users(id, username, email, preferences, created_at) FROM '/path/to/oxygen_users_export.csv' WITH (FORMAT CSV, HEADER true);
\copy courses(id, course_name, description, duration_hours, created_at) FROM '/path/to/oxygen_courses_export.csv' WITH (FORMAT CSV, HEADER true);

# Reset sequences
SELECT setval('tickets_id_seq', (SELECT MAX(id) FROM tickets));
SELECT setval('cloud_costs_id_seq', (SELECT MAX(id) FROM cloud_costs));
SELECT setval('users_id_seq', (SELECT MAX(id) FROM users));
SELECT setval('courses_id_seq', (SELECT MAX(id) FROM courses));
```

#### Step 4: Update Application Code

**Before (SQLite)**:

```python
import sqlite3

conn = sqlite3.connect('data/tickets.db')
cursor = conn.cursor()
cursor.execute("SELECT * FROM tickets WHERE status = ?", ("pending",))
```

**After (PostgreSQL with psycopg2)**:

```python
import psycopg2
import os

# Cloud SQL connection via Unix socket
conn = psycopg2.connect(
    host="/cloudsql/project-id:region:instance-name",
    database="jarvis",
    user="jarvis_app",
    password=os.getenv("DB_PASSWORD")
)
cursor = conn.cursor()
cursor.execute("SELECT * FROM tickets WHERE status = %s", ("pending",))
```

**Or with SQLAlchemy (Recommended)**:

```python
from sqlalchemy import create_engine
import os

# Get connection string from environment (Secret Manager)
engine = create_engine(os.getenv("DB_CONNECTION_STRING"))

# Use with ORM
from sqlalchemy.orm import sessionmaker
Session = sessionmaker(bind=engine)
session = Session()

# Query
tickets = session.query(Ticket).filter_by(status="pending").all()
```

---

## Security & Authentication

### 1. Secret Manager Best Practices

✅ **DO**:
- Store API keys, JWT secrets, database passwords in Secret Manager
- Pin secrets to specific versions (not `latest`)
- Use secret-level IAM bindings
- Rotate secrets quarterly
- Use separate projects for staging/production

❌ **DON'T**:
- Store secrets in environment variables
- Use `latest` version in production
- Include credentials in Docker images
- Commit secrets to git

**Example**:

```bash
# Create secret with specific version
echo -n "my-secret-value" | gcloud secrets create my-secret --data-file=-

# Grant access to specific service account
gcloud secrets add-iam-policy-binding my-secret \
  --member="serviceAccount:tickets-agent@project.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Access in Cloud Run
gcloud run deploy tickets-agent \
  --set-secrets=GOOGLE_API_KEY=google-api-key:1  # Pin to version 1
```

### 2. Service-to-Service Authentication

**IAM-Based (Recommended)**:

```python
import google.auth
from google.auth.transport.requests import Request
import requests

def call_internal_service(url: str):
    """Call Cloud Run service with IAM authentication"""
    # Get default credentials
    credentials, project = google.auth.default()

    # Get ID token
    auth_req = Request()
    credentials.refresh(auth_req)

    # Make authenticated request
    headers = {
        "Authorization": f"Bearer {credentials.token}",
        "Content-Type": "application/json"
    }

    response = requests.post(url, headers=headers, json={...})
    return response.json()
```

**JWT Bearer Token**:

```python
from fastapi import FastAPI, Depends, HTTPException, Header
from jose import JWTError, jwt
import os

app = FastAPI()

JWT_SECRET = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = "HS256"

async def verify_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing Authorization header")

    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(401, "Invalid token")

@app.post("/a2a/send_message")
async def send_message(user=Depends(verify_token)):
    # user contains decoded JWT payload
    return {"status": "authenticated", "user": user}
```

### 3. Cloud Armor Configuration

**DDoS Protection**:

```bash
# Create security policy
gcloud compute security-policies create ddos-protection \
  --description="DDoS protection for Agentic Jarvis"

# Rate limiting (1000 requests/minute per IP)
gcloud compute security-policies rules create 1000 \
  --security-policy=ddos-protection \
  --expression="true" \
  --action=rate-based-ban \
  --rate-limit-threshold-count=1000 \
  --rate-limit-threshold-interval-sec=60 \
  --ban-duration-sec=600 \
  --conform-action=allow \
  --exceed-action=deny-429 \
  --enforce-on-key=IP
```

**WAF Rules**:

```bash
# Block SQL injection attempts
gcloud compute security-policies rules create 2000 \
  --security-policy=ddos-protection \
  --expression="evaluatePreconfiguredExpr('sqli-v33-stable')" \
  --action=deny-403

# Block XSS attempts
gcloud compute security-policies rules create 3000 \
  --security-policy=ddos-protection \
  --expression="evaluatePreconfiguredExpr('xss-v33-stable')" \
  --action=deny-403

# Geo-blocking (example: allow only US traffic)
gcloud compute security-policies rules create 4000 \
  --security-policy=ddos-protection \
  --expression="origin.region_code != 'US'" \
  --action=deny-403
```

### 4. Network Security

**VPC Configuration**:

```bash
# Create VPC network
gcloud compute networks create jarvis-vpc \
  --subnet-mode=custom

# Create subnet
gcloud compute networks subnets create jarvis-subnet \
  --network=jarvis-vpc \
  --region=us-central1 \
  --range=10.0.0.0/24

# Enable Private Google Access (for Cloud SQL)
gcloud compute networks subnets update jarvis-subnet \
  --region=us-central1 \
  --enable-private-ip-google-access

# Configure Cloud Run to use VPC (Direct VPC egress - 2025)
gcloud run services update tickets-agent \
  --region=us-central1 \
  --network=jarvis-vpc \
  --subnet=jarvis-subnet \
  --network-tags=cloud-run-agents
```

**Firewall Rules**:

```bash
# Allow Cloud Run egress to Cloud SQL
gcloud compute firewall-rules create allow-cloud-run-to-sql \
  --network=jarvis-vpc \
  --allow=tcp:5432 \
  --source-tags=cloud-run-agents \
  --target-tags=cloudsql-instance

# Deny all other egress (whitelist approach)
gcloud compute firewall-rules create deny-all-egress \
  --network=jarvis-vpc \
  --direction=EGRESS \
  --priority=65535 \
  --action=DENY \
  --rules=all
```

---

## Observability & Monitoring

### 1. Cloud Trace (Distributed Tracing)

**ADK Integration**:

```python
from google.cloud import trace_v1
from google.adk.tracing import enable_cloud_trace

# Enable Cloud Trace for ADK agents
enable_cloud_trace(project_id="your-project-id")

# Traces automatically created for:
# - Agent invocations
# - Tool executions
# - A2A calls
```

**Manual Instrumentation**:

```python
from google.cloud import trace_v2
from google.cloud.trace_v2 import TraceServiceClient

tracer_client = TraceServiceClient()

@app.post("/a2a/send_message")
async def send_message(request: A2ARequest):
    # Create span
    project_id = "your-project-id"
    trace_id = request.headers.get("X-Cloud-Trace-Context", "").split("/")[0]

    span = {
        "name": f"projects/{project_id}/traces/{trace_id}/spans/send_message",
        "span_id": "1",
        "display_name": {"value": "A2A Send Message"},
        "start_time": {"seconds": int(time.time())},
        "end_time": {"seconds": int(time.time()) + 1}
    }

    # Process request
    result = await process_a2a_request(request)

    return result
```

### 2. Structured Logging

```python
import logging
from google.cloud import logging as cloud_logging

# Setup Cloud Logging
client = cloud_logging.Client()
client.setup_logging()

logger = logging.getLogger(__name__)

# Structured logging with JSON
logger.info("A2A request received", extra={
    "agent_name": "tickets-agent",
    "user_id": "user123",
    "request_id": "req-456",
    "latency_ms": 45
})

# Correlate with traces
logger.info("Processing ticket", extra={
    "trace": f"projects/{project_id}/traces/{trace_id}",
    "span_id": span_id
})
```

### 3. Cloud Monitoring Dashboards

**Key Metrics**:

```bash
# CPU utilization
resource.type="cloud_run_revision"
metric.type="run.googleapis.com/container/cpu/utilizations"

# Memory usage
resource.type="cloud_run_revision"
metric.type="run.googleapis.com/container/memory/utilizations"

# Request count
resource.type="cloud_run_revision"
metric.type="run.googleapis.com/request_count"

# Request latency
resource.type="cloud_run_revision"
metric.type="run.googleapis.com/request_latencies"

# Instance count
resource.type="cloud_run_revision"
metric.type="run.googleapis.com/container/instance_count"

# Billable instance time
resource.type="cloud_run_revision"
metric.type="run.googleapis.com/container/billable_instance_time"
```

**Create Dashboard**:

```bash
gcloud monitoring dashboards create --config-from-file=dashboard.json
```

**dashboard.json**:

```json
{
  "displayName": "Agentic Jarvis - A2A Agents",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Request Count by Service",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_RATE"
                  }
                }
              }
            }]
          }
        }
      },
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Average Latency (P95)",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "metric.type=\"run.googleapis.com/request_latencies\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_PERCENTILE_95"
                  }
                }
              }
            }]
          }
        }
      }
    ]
  }
}
```

### 4. Alerting

```bash
# Create alert for high latency
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Latency Alert" \
  --condition-display-name="Latency > 1000ms" \
  --condition-threshold-value=1000 \
  --condition-threshold-duration=60s \
  --condition-filter='resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_latencies"'

# Create alert for error rate
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=0.05 \
  --condition-threshold-duration=60s \
  --condition-filter='resource.type="cloud_run_revision" AND metric.type="run.googleapis.com/request_count" AND metric.label.response_code_class="5xx"'
```

### 5. OpenTelemetry Integration (2025 Best Practice)

```python
from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Setup OpenTelemetry with Cloud Trace
trace.set_tracer_provider(TracerProvider())
cloud_trace_exporter = CloudTraceSpanExporter()
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(cloud_trace_exporter)
)

tracer = trace.get_tracer(__name__)

# Instrument FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor.instrument_app(app)

# Manual spans
@app.post("/a2a/send_message")
async def send_message(request: A2ARequest):
    with tracer.start_as_current_span("process_a2a") as span:
        span.set_attribute("agent.name", "tickets-agent")
        span.set_attribute("user.id", request.user_id)

        result = await process_request(request)

        span.set_attribute("result.status", result.status)
        return result
```

---

## Cost Analysis

### Cloud Run Pricing (2025)

**Pricing Model**: Pay-per-use (vCPU-seconds + GiB-seconds + requests)

**Free Tier (Monthly)**:
- 2 million requests
- 180,000 vCPU-seconds
- 360,000 GiB-seconds

**Tier 1 Pricing (US regions)**:
- CPU: $0.00002400 per vCPU-second
- Memory: $0.00000250 per GiB-second
- Requests: $0.40 per million requests

### Monthly Cost Estimation

**Assumptions**:
- 100,000 requests/month (moderate usage)
- Average latency: 300ms per request
- 6 services: Auth (512Mi/1vCPU), Registry (512Mi/1vCPU), 3 Agents (1Gi/1vCPU), Web UI (512Mi/1vCPU)

**Breakdown**:

| Service | Requests | Latency | Memory | CPU | Monthly Cost |
|---------|----------|---------|--------|-----|--------------|
| Auth | 50,000 | 100ms | 512Mi | 1 vCPU | $0.73 |
| Registry | 30,000 | 150ms | 512Mi | 1 vCPU | $0.66 |
| Tickets Agent | 10,000 | 400ms | 1Gi | 1 vCPU | $1.36 |
| FinOps Agent | 5,000 | 400ms | 1Gi | 1 vCPU | $0.68 |
| Oxygen Agent | 5,000 | 400ms | 1Gi | 1 vCPU | $0.68 |
| Web UI | 100,000 | 200ms | 512Mi | 1 vCPU | $2.92 |
| **Subtotal** | | | | | **$7.03** |

**Additional Costs**:

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| Cloud SQL (db-f1-micro) | 0.6 vCPU, 0.6GB RAM, 10GB SSD | $7.67 |
| Artifact Registry | 10GB storage | $1.00 |
| Load Balancer | 100K requests, minimal forwarding | $18.26 |
| Secret Manager | 6 secrets, 500K accesses | $0.36 |
| Cloud Armor | 2 security policies, 10 rules | $5.00 |
| Cloud Monitoring/Logging | 50GB logs, standard retention | $2.50 |
| Egress (Cloud Run → Internet) | 1GB/month | $0.12 |
| **Total Infrastructure** | | **$34.91** |

**Gemini API Costs** (Vertex AI):

| Model | Input Tokens | Output Tokens | Monthly Cost |
|-------|--------------|---------------|--------------|
| Gemini 2.5 Flash | 10M tokens (~$0.075/1M) | 2M tokens (~$0.30/1M) | $1.35 |

**Grand Total**: **$43.29/month** (100K requests/month)

### Scaling Scenarios

**Low Usage (10K requests/month)**:
- Cloud Run: ~$1.50
- Infrastructure: $34.91
- Gemini: $0.30
- **Total**: ~$36.71/month

**Medium Usage (100K requests/month)**:
- Cloud Run: ~$7.03
- Infrastructure: $34.91
- Gemini: $1.35
- **Total**: ~$43.29/month

**High Usage (1M requests/month)**:
- Cloud Run: ~$70.30
- Infrastructure: $54.91 (upgraded Cloud SQL: db-g1-small $25)
- Gemini: $13.50
- **Total**: ~$138.71/month

### Cost Comparison: Cloud Run vs VPS

**VPS (DigitalOcean Droplet)**:
- 2 vCPU, 4GB RAM: $24/month
- Managed PostgreSQL: $15/month
- Load Balancer: $12/month
- **Total**: $51/month (fixed cost)

**Analysis**:
- VPS is **50%+ cheaper** for sustained traffic
- Cloud Run is **cheaper** for variable/bursty traffic (<50K requests/month)
- Cloud Run provides **better scalability** (0-1000 instances)
- VPS requires **manual management** (no auto-scaling)

**Recommendation**:
- **Development/Staging**: Cloud Run (scale to zero, $0 when idle)
- **Production (low traffic)**: Cloud Run
- **Production (high sustained traffic)**: Consider VPS or GKE with committed use discounts

### Cost Optimization Strategies

1. **Use Committed Use Discounts**: 25% (1-year) to 52% (3-year) discount on Cloud SQL
2. **Scale to Zero**: Set `min-instances=0` for agents not frequently used
3. **Regional Pricing**: Use Tier 1 regions (us-central1, us-east1, us-west1)
4. **Right-Size Memory/CPU**: Start with 512Mi/1vCPU, monitor, and adjust
5. **Log Retention**: Reduce Cloud Logging retention to 30 days
6. **Artifact Registry Cleanup**: Delete old/unused images regularly
7. **Cloud SQL Auto-Increase**: Enable but set max storage to prevent runaway costs
8. **Vertex AI Free Tier**: First $300 in credits for new accounts

---

## Migration Checklist

### Pre-Deployment

- [ ] Google Cloud account created
- [ ] Billing enabled
- [ ] Project created (`gcloud projects create`)
- [ ] Required APIs enabled (Cloud Run, SQL, Secret Manager, etc.)
- [ ] gcloud CLI installed and authenticated
- [ ] Docker installed locally
- [ ] ADK CLI installed (`pip install google-adk[a2a]`)
- [ ] Domain name purchased (for SSL certificate)

### Infrastructure Setup

- [ ] Artifact Registry repository created
- [ ] Docker authentication configured (`gcloud auth configure-docker`)
- [ ] Cloud SQL instance created
- [ ] Cloud SQL databases created (jarvis)
- [ ] Cloud SQL users created
- [ ] Secret Manager secrets created:
  - [ ] `google-api-key`
  - [ ] `jwt-secret-key`
  - [ ] `db-connection-string`
- [ ] IAM permissions granted to Cloud Run service accounts
- [ ] VPC network created (if using VPC)
- [ ] Firewall rules configured (if using VPC)

### Database Migration

- [ ] Export data from SQLite (CSV format)
- [ ] Create Cloud SQL schemas
- [ ] Import data to Cloud SQL
- [ ] Verify data integrity
- [ ] Reset sequences
- [ ] Update application connection strings
- [ ] Test database connectivity from local machine
- [ ] Test database connectivity from Cloud Run (after deployment)

### Application Updates

- [ ] Update database drivers (sqlite3 → psycopg2)
- [ ] Update connection strings (environment variables)
- [ ] Update agent card URLs (localhost → Cloud Run URLs)
- [ ] Update RemoteA2aAgent configurations
- [ ] Add IAM authentication for service-to-service calls
- [ ] Implement health check endpoints
- [ ] Update CORS origins for production domains
- [ ] Configure structured logging (Cloud Logging)
- [ ] Add OpenTelemetry instrumentation (optional)

### Docker Configuration

- [ ] Create Dockerfile for Auth Service
- [ ] Create Dockerfile for Registry Service
- [ ] Create Dockerfile for Tickets Agent
- [ ] Create Dockerfile for FinOps Agent
- [ ] Create Dockerfile for Oxygen Agent
- [ ] Create Dockerfile for Web UI
- [ ] Test Docker builds locally
- [ ] Optimize images (multi-stage builds, slim base images)

### Cloud Run Deployment

- [ ] Deploy Auth Service
- [ ] Deploy Registry Service
- [ ] Deploy Tickets Agent
- [ ] Deploy FinOps Agent
- [ ] Deploy Oxygen Agent
- [ ] Deploy Web UI
- [ ] Verify all services are running (`gcloud run services list`)
- [ ] Test health check endpoints
- [ ] Configure IAM permissions (service-to-service)
- [ ] Configure autoscaling (min/max instances)
- [ ] Enable CPU boost for agents
- [ ] Configure Cloud SQL connections

### Networking & Security

- [ ] Reserve static IP for Load Balancer
- [ ] Create serverless NEGs for Web UI
- [ ] Create backend service
- [ ] Create URL map (routing rules)
- [ ] Create SSL certificate (managed or upload)
- [ ] Create HTTPS proxy
- [ ] Create forwarding rule
- [ ] Update DNS records (point domain to Load Balancer IP)
- [ ] Create Cloud Armor security policy
- [ ] Add rate limiting rules
- [ ] Add WAF rules (SQL injection, XSS)
- [ ] Attach Cloud Armor to backend service
- [ ] Test DDoS protection (optional)

### A2A Protocol Verification

- [ ] Verify agent cards accessible at `/.well-known/agent-card.json`
- [ ] Test HTTPS for agent cards (TLS 1.3+)
- [ ] Verify agent card schema correctness
- [ ] Test RemoteA2aAgent connections
- [ ] Test A2A authentication (IAM or JWT)
- [ ] Test cross-agent communication (Tickets → FinOps → Oxygen)
- [ ] Verify distributed tracing across A2A calls

### Observability

- [ ] Cloud Trace enabled
- [ ] Cloud Logging configured (structured logs)
- [ ] Cloud Monitoring dashboard created
- [ ] Alerts configured (latency, error rate, instance count)
- [ ] OpenTelemetry instrumentation (optional)
- [ ] Log-based metrics created (optional)
- [ ] Uptime checks configured (optional)

### Testing

- [ ] Test auth service (login, token generation)
- [ ] Test registry service (agent registration, session management)
- [ ] Test each agent individually (health checks, A2A endpoints)
- [ ] Test end-to-end user flows (Web UI → Agents)
- [ ] Test JWT authentication
- [ ] Test IAM authentication (service-to-service)
- [ ] Load testing (Apache Bench, Locust, or K6)
- [ ] Security testing (OWASP ZAP, Burp Suite)
- [ ] Test error handling (500 errors, timeouts)
- [ ] Test autoscaling (simulate traffic spike)

### Production Readiness

- [ ] Environment variables configured (production values)
- [ ] Secrets rotated (JWT secret, API keys)
- [ ] SSL certificate provisioned and active
- [ ] Domain DNS propagated (24-48 hours)
- [ ] Backup strategy for Cloud SQL (automated backups enabled)
- [ ] Disaster recovery plan documented
- [ ] Runbook created (deployment, rollback, troubleshooting)
- [ ] Monitoring alerts tested
- [ ] On-call rotation established (if applicable)
- [ ] Cost budget alerts configured

### CI/CD (Optional)

- [ ] Cloud Build configuration created (`cloudbuild.yaml`)
- [ ] GitHub/GitLab integration configured
- [ ] Automated testing in CI pipeline
- [ ] Automated Docker builds
- [ ] Automated Cloud Run deployments
- [ ] Blue/green or canary deployment strategy
- [ ] Rollback automation

### Documentation

- [ ] Update README with Cloud Run URLs
- [ ] Document deployment process
- [ ] Document troubleshooting steps
- [ ] Document cost monitoring
- [ ] Document scaling policies
- [ ] Document security policies

---

## CI/CD with Cloud Build

### cloudbuild.yaml (Multi-Service)

```yaml
steps:
  # Build Auth Service
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/auth-service:$SHORT_SHA'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/auth-service:latest'
      - '-f'
      - 'auth/Dockerfile'
      - '.'

  # Build Registry Service
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/registry-service:$SHORT_SHA'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/registry-service:latest'
      - '-f'
      - 'agent_registry_service/Dockerfile'
      - '.'

  # Build Tickets Agent
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/tickets-agent:$SHORT_SHA'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/tickets-agent:latest'
      - '-f'
      - 'tickets_agent_service/Dockerfile'
      - '.'

  # Build FinOps Agent
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/finops-agent:$SHORT_SHA'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/finops-agent:latest'
      - '-f'
      - 'finops_agent_service/Dockerfile'
      - '.'

  # Build Oxygen Agent
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/oxygen-agent:$SHORT_SHA'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/oxygen-agent:latest'
      - '-f'
      - 'oxygen_agent_service/Dockerfile'
      - '.'

  # Build Web UI
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/web-ui:$SHORT_SHA'
      - '-t'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/web-ui:latest'
      - '-f'
      - 'web_ui/Dockerfile'
      - '.'

  # Push all images
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - '--all-tags'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/auth-service'

  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - '--all-tags'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/registry-service'

  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - '--all-tags'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/tickets-agent'

  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - '--all-tags'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/finops-agent'

  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - '--all-tags'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/oxygen-agent'

  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - '--all-tags'
      - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/web-ui'

  # Deploy to Cloud Run (Auth Service)
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'auth-service'
      - '--image=us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/auth-service:$SHORT_SHA'
      - '--region=us-central1'
      - '--platform=managed'

  # Deploy other services (similar pattern)
  # ...

images:
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/auth-service:$SHORT_SHA'
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/registry-service:$SHORT_SHA'
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/tickets-agent:$SHORT_SHA'
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/finops-agent:$SHORT_SHA'
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/oxygen-agent:$SHORT_SHA'
  - 'us-central1-docker.pkg.dev/$PROJECT_ID/agentic-jarvis/web-ui:$SHORT_SHA'

options:
  machineType: 'N1_HIGHCPU_8'
  logging: CLOUD_LOGGING_ONLY
```

### Setup CI/CD Trigger

```bash
# Create build trigger
gcloud builds triggers create github \
  --repo-name=agentic-jarvis \
  --repo-owner=your-github-username \
  --branch-pattern=^main$ \
  --build-config=cloudbuild.yaml

# Grant Cloud Run permissions to Cloud Build service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud iam service-accounts add-iam-policy-binding \
  $PROJECT_NUMBER-compute@developer.gserviceaccount.com \
  --member="serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

---

## References

### Official Google Documentation

1. **ADK & A2A Protocol**
   - [What's new with Agents: ADK, Agent Engine, and A2A Enhancements - Google Developers Blog](https://developers.googleblog.com/en/agents-adk-agent-engine-a2a-enhancements-google-io/)
   - [ADK with Agent2Agent (A2A) Protocol - Agent Development Kit](https://google.github.io/adk-docs/a2a/)
   - [Agent2Agent protocol (A2A) is getting an upgrade | Google Cloud Blog](https://cloud.google.com/blog/products/ai-machine-learning/agent2agent-protocol-is-getting-an-upgrade)
   - [GitHub - google/adk-python: An open-source, code-first Python toolkit](https://github.com/google/adk-python)

2. **Cloud Run Deployment**
   - [Host A2A agents on Cloud Run overview | Google Cloud](https://cloud.google.com/run/docs/host-a2a-agents)
   - [Deploy A2A agents to Cloud Run | Google Cloud](https://cloud.google.com/run/docs/deploy-a2a-agents)
   - [Cloud Run - Agent Development Kit](https://google.github.io/adk-docs/deploy/cloud-run/)
   - [Building a Multi-Agent Deep Research Tool with Google ADK, A2A, & Cloud Run](https://dev.to/agenticamit/building-a-multi-agent-deep-research-tool-with-google-adk-a2a-cloud-run-2ldj)

3. **Vertex AI Agent Engine**
   - [Build and manage multi-system agents with Vertex AI | Google Cloud Blog](https://cloud.google.com/blog/products/ai-machine-learning/build-and-manage-multi-system-agents-with-vertex-ai)
   - [Vertex AI Agent Builder | Google Cloud](https://cloud.google.com/products/agent-builder)
   - [Vertex AI Agent Engine Memory Bank overview](https://cloud.google.com/agent-builder/agent-engine/memory-bank/overview)
   - [Deploy to Vertex AI Agent Engine - Agent Development Kit](https://google.github.io/adk-docs/deploy/agent-engine/)

4. **Cloud Run Optimization**
   - [Optimize Python applications for Cloud Run | Google Cloud](https://cloud.google.com/run/docs/tips/python)
   - [3 Ways to optimize Cloud Run response times | Google Cloud Blog](https://cloud.google.com/blog/topics/developers-practitioners/3-ways-optimize-cloud-run-response-times)
   - [Google Cloud Run 2025: Cold Start Optimization Techniques](https://markaicode.com/google-cloud-run-cold-start-optimization-2025/)

5. **Networking & Security**
   - [VPC with connectors | Cloud Run | Google Cloud](https://cloud.google.com/run/docs/configuring/vpc-connectors)
   - [Private networking and Cloud Run | Google Cloud Documentation](https://docs.cloud.google.com/run/docs/securing/private-networking)
   - [Configure secrets for services | Cloud Run](https://docs.cloud.google.com/run/docs/configuring/services/secrets)
   - [Secret Manager best practices | Google Cloud](https://cloud.google.com/secret-manager/docs/best-practices)
   - [Cloud Armor Network Security | Google Cloud](https://cloud.google.com/security/products/armor)

6. **Observability**
   - [Cloud Trace - Agent Development Kit](https://google.github.io/adk-docs/observability/cloud-trace/)
   - [Monitoring and logging overview | Cloud Run](https://docs.cloud.google.com/run/docs/monitoring-overview)
   - [Serverless observability: How to monitor Google Cloud Run with OpenTelemetry](https://grafana.com/blog/2024/05/23/serverless-observability-how-to-monitor-google-cloud-run-with-opentelemetry-and-grafana-cloud/)

7. **Pricing & Cost**
   - [Cloud Run pricing | Google Cloud](https://cloud.google.com/run/pricing)
   - [Google Cloud Run Pricing in 2025: A Comprehensive Guide](https://cloudchipr.com/blog/cloud-run-pricing)
   - [Vertex AI Pricing | Google Cloud](https://cloud.google.com/vertex-ai/generative-ai/pricing)
   - [Gemini AI Pricing: What You'll Really Pay In 2025](https://www.cloudzero.com/blog/gemini-pricing/)

8. **A2A Protocol Specification**
   - [Overview - A2A Protocol](https://a2a-protocol.org/latest/specification/)
   - [2025 Complete Guide: Agent2Agent (A2A) Protocol](https://a2aprotocol.ai/blog/2025-full-guide-a2a-protocol)
   - [How to enhance Agent2Agent (A2A) security | Red Hat Developer](https://developers.redhat.com/articles/2025/08/19/how-enhance-agent2agent-security)

### Community Resources

9. **Deployment Guides**
   - [A Step-by-Step Guide To Deploying ADK Agents on Cloud Run - The New Stack](https://thenewstack.io/a-step-by-step-guide-to-deploying-adk-agents-on-cloud-run/)
   - [Deploying AI Agents in the Enterprise using ADK and Google Cloud](https://fmind.medium.com/deploying-ai-agents-in-the-enterprise-using-adk-and-google-cloud-b49e7eda3b41)
   - [FastAPI Deployment: Scalable Production Guide for 2025](https://www.zestminds.com/blog/fastapi-deployment-guide/)

10. **Multi-Agent Patterns**
    - [A2A Agent Patterns with the Agent Development Kit (ADK)](https://medium.com/google-cloud/a2a-agent-patterns-with-the-agent-development-kit-adk-aee3d61c52cf)
    - [Create multi agent system with ADK, deploy in Agent Engine](https://codelabs.developers.google.com/codelabs/create-multi-agents-adk-a2a)
    - [Google's Agent Stack in Action: ADK, A2A, MCP on Google Cloud](https://codelabs.developers.google.com/instavibe-adk-multi-agents/instructions)

---

## Appendix A: FastAPI Production Optimization

### Cold Start Optimization

```python
import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Preload models/resources at startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global db_pool, model_client

    # Initialize database pool
    db_pool = await create_pool(...)

    # Initialize Gemini client
    model_client = genai.GenerativeModel("gemini-2.5-flash")

    # Warm up model (optional)
    await model_client.generate_content_async("warm up")

    yield

    # Shutdown
    await db_pool.close()

app = FastAPI(lifespan=lifespan)

# Use Uvicorn with Gunicorn for production
# CMD ["gunicorn", "main:app", "--workers", "2", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8080"]
```

### Dockerfile Optimization

```dockerfile
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Pre-compile Python files
RUN python -m compileall .

# Non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

# Use exec form for proper signal handling
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]
```

---

## Appendix B: Troubleshooting

### Common Issues

**1. Cold Start Latency > 10 seconds**

❌ Problem: High import overhead (ADK, TensorFlow, etc.)

✅ Solution:
- Enable CPU boost: `gcloud run services update --cpu-boost`
- Lazy import heavy dependencies
- Use `min-instances=1` for critical services
- Precompile Python bytecode in Dockerfile

**2. "503 Service Unavailable" errors**

❌ Problem: Service scaled to zero, cold start timeout

✅ Solution:
- Increase Cloud Run timeout: `--timeout=300`
- Set `min-instances=1` for frequently accessed services
- Implement retry logic in clients

**3. A2A agent card not accessible**

❌ Problem: HTTPS required, agent card endpoint not public

✅ Solution:
- Ensure `/.well-known/agent-card.json` endpoint exists
- Verify SSL certificate is valid (TLS 1.3+)
- Check Cloud Run ingress settings (`--ingress=all` for public agents)

**4. "Permission denied" when calling internal service**

❌ Problem: Missing IAM permissions

✅ Solution:
```bash
gcloud run services add-iam-policy-binding TARGET_SERVICE \
  --region=us-central1 \
  --member="serviceAccount:CALLER_SA@project.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

**5. High Cloud SQL latency**

❌ Problem: Public IP connection, no VPC

✅ Solution:
- Use Cloud SQL Proxy or Private IP
- Add Cloud SQL instance to Cloud Run service:
  `--add-cloudsql-instances=PROJECT:REGION:INSTANCE`

**6. Secrets not accessible in Cloud Run**

❌ Problem: IAM permissions missing

✅ Solution:
```bash
gcloud secrets add-iam-policy-binding SECRET_NAME \
  --member="serviceAccount:SERVICE_ACCOUNT" \
  --role="roles/secretmanager.secretAccessor"
```

**7. Build fails: "Address already in use"**

❌ Problem: Docker daemon conflict

✅ Solution:
```bash
# Stop all containers
docker stop $(docker ps -aq)
docker system prune -a
```

---

## Appendix C: Health Check Endpoints

```python
from fastapi import FastAPI, Response
from datetime import datetime
import psycopg2
import os

app = FastAPI()

@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/readiness")
async def readiness_check():
    """Check if service is ready to accept traffic"""
    checks = {
        "status": "ready",
        "database": False,
        "api_key": False
    }

    # Check database connection
    try:
        conn = psycopg2.connect(os.getenv("DB_CONNECTION_STRING"))
        conn.close()
        checks["database"] = True
    except Exception as e:
        return Response(status_code=503, content=f"Database unavailable: {e}")

    # Check API key exists
    if os.getenv("GOOGLE_API_KEY"):
        checks["api_key"] = True
    else:
        return Response(status_code=503, content="API key not configured")

    return checks

@app.get("/liveness")
async def liveness_check():
    """Check if service is alive (simple)"""
    return {"status": "alive"}
```

---

**End of Document**

For questions or issues, consult the [official Google ADK documentation](https://google.github.io/adk-docs/) or the [A2A Protocol specification](https://a2a-protocol.org/).
