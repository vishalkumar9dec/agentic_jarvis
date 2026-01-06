# GCP Deployment Research Summary - Quick Reference

**Research Date:** December 31, 2025
**Target System:** Agentic Jarvis (6-service A2A multi-agent architecture)

---

## Executive Summary

### Key Findings

✅ **A2A Protocol is Production-Ready (2025)**
- Google ADK v1.0.0+ released May 2025
- A2A Protocol v0.3 with gRPC support
- 150+ organizations supporting the standard
- Official Cloud Run deployment guide available

✅ **Two Primary Deployment Options**

| Option | Best For | Cost | Complexity |
|--------|----------|------|------------|
| **Cloud Run** | Multi-service A2A, variable traffic | $45/mo (100K req) | Medium |
| **Vertex AI Agent Engine** | Single-agent, managed memory | Similar | Low |

✅ **Recommended: Cloud Run**
- Full control over 6 independent services
- Official A2A support with agent cards
- Auto-scaling (0-1000 instances)
- Scale-to-zero for dev/staging
- Better fit for existing FastAPI architecture

---

## Architecture Overview

### Current (Localhost)

```
Auth (9998) + Registry (8003) + Tickets (8080) + FinOps (8081) + Oxygen (8082) + Web UI (9999)
         ↓                ↓                 ↓                ↓              ↓
      SQLite         SQLite            SQLite           SQLite        SQLite
```

### Target (Cloud Run)

```
                     Google Cloud Load Balancer (HTTPS)
                               ↓
                     Cloud Armor (DDoS/WAF)
                               ↓
       ┌──────────────────────┴──────────────────────┐
       │                                              │
   Cloud Run Services (Internal + IAM Auth)      Web UI (Public)
       │                                              │
   Auth, Registry, Tickets, FinOps, Oxygen           │
       │                                              │
       └────────────┬─────────────────────────────────┘
                    ↓
         Cloud SQL PostgreSQL (Private)
                    ↓
         Vertex AI (Gemini 2.5 Flash)
```

---

## Cost Analysis

### Monthly Cost by Usage Level

| Traffic | Cloud Run | Infrastructure | Gemini API | Total |
|---------|-----------|----------------|------------|-------|
| **10K req/mo** (Dev) | $0.15 | $34.70 | $0.14 | **$35/mo** |
| **100K req/mo** (Prod) | $7.03 | $36.37 | $1.35 | **$45/mo** |
| **1M req/mo** (High) | $72.50 | $68.71 | $13.50 | **$155/mo** |

### Comparison: Cloud Run vs VPS

| Metric | Cloud Run | VPS (DigitalOcean) |
|--------|-----------|---------------------|
| **Low traffic (<100K req/mo)** | $35-$45 ✅ | $56 |
| **High traffic (>500K req/mo)** | $95+ | $56 ✅ |
| **Scale-to-zero** | Yes ✅ | No |
| **Auto-scaling** | Yes ✅ | Manual |
| **Observability** | Built-in ✅ | DIY |
| **Maintenance** | Zero ✅ | Manual |

**Verdict**: Cloud Run wins for <400K req/mo, VPS wins for sustained high traffic

---

## A2A Protocol Requirements (Production)

### 1. Agent Card Endpoint (MANDATORY)

Every A2A agent MUST serve an agent card at:

```
https://your-agent-domain/.well-known/agent-card.json
```

**HTTPS Requirements**:
- TLS 1.3+ with strong ciphers
- Valid SSL certificate from trusted CA
- Cloud Run provides this automatically

**Agent Card Schema**:
```json
{
  "name": "tickets-agent",
  "description": "IT ticket management",
  "version": "1.0.0",
  "capabilities": {"streaming": true},
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
}
```

### 2. RemoteA2aAgent Configuration

**Development**:
```python
oxygen_agent = RemoteA2aAgent(
    name="oxygen_agent",
    agent_card="http://localhost:8082/.well-known/agent-card.json"
)
```

**Production**:
```python
oxygen_agent = RemoteA2aAgent(
    name="oxygen_agent",
    agent_card="https://oxygen-agent-xxx.run.app/.well-known/agent-card.json",
    auth_scheme="bearerAuth",
    auth_credential=lambda: get_iam_token()  # IAM or JWT
)
```

### 3. Service-to-Service Authentication

**IAM-Based (Recommended for GCP)**:
```python
import google.auth
from google.auth.transport.requests import Request

def get_iam_token():
    credentials, _ = google.auth.default()
    auth_req = Request()
    credentials.refresh(auth_req)
    return credentials.token
```

**Configure IAM**:
```bash
gcloud run services add-iam-policy-binding TARGET_SERVICE \
  --member="serviceAccount:CALLER_SA@project.iam.gserviceaccount.com" \
  --role="roles/run.invoker"
```

---

## Deployment Steps (Simplified)

### Phase 1: Setup GCP Infrastructure

```bash
# 1. Enable APIs
gcloud services enable run.googleapis.com sql-component.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com

# 2. Create Artifact Registry
gcloud artifacts repositories create agentic-jarvis \
  --repository-format=docker --location=us-central1

# 3. Create Cloud SQL
gcloud sql instances create agentic-jarvis-db \
  --database-version=POSTGRES_15 --tier=db-f1-micro \
  --region=us-central1

# 4. Store secrets
echo -n "YOUR_API_KEY" | gcloud secrets create google-api-key --data-file=-
echo -n "YOUR_JWT_SECRET" | gcloud secrets create jwt-secret-key --data-file=-
```

### Phase 2: Migrate Database

```bash
# 1. Export SQLite to CSV
sqlite3 data/tickets.db ".mode csv" ".output tickets.csv" "SELECT * FROM tickets;"

# 2. Create PostgreSQL schemas (see full guide)

# 3. Import to Cloud SQL
gcloud sql connect agentic-jarvis-db --user=postgres
\copy tickets FROM 'tickets.csv' WITH (FORMAT CSV, HEADER true);
```

### Phase 3: Deploy Services

**Option A: Manual Docker Build**
```bash
PROJECT_ID="your-project"
REGISTRY="us-central1-docker.pkg.dev/${PROJECT_ID}/agentic-jarvis"

docker build -t ${REGISTRY}/tickets-agent:latest -f tickets_agent_service/Dockerfile .
docker push ${REGISTRY}/tickets-agent:latest

gcloud run deploy tickets-agent \
  --image=${REGISTRY}/tickets-agent:latest \
  --region=us-central1 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=20 \
  --cpu-boost \
  --no-allow-unauthenticated
```

**Option B: ADK CLI (Simplified)**
```bash
cd tickets_agent_service
adk deploy cloud_run \
  --project=$PROJECT_ID \
  --region=us-central1 \
  --service-name=tickets-agent
```

**Note**: ADK CLI automatically builds, pushes, and deploys!

### Phase 4: Configure Load Balancer + Cloud Armor

```bash
# 1. Create serverless NEG
gcloud compute network-endpoint-groups create web-ui-neg \
  --region=us-central1 \
  --network-endpoint-type=serverless \
  --cloud-run-service=web-ui

# 2. Create backend service
gcloud compute backend-services create agentic-jarvis-backend \
  --global --load-balancing-scheme=EXTERNAL_MANAGED

gcloud compute backend-services add-backend agentic-jarvis-backend \
  --global --network-endpoint-group=web-ui-neg \
  --network-endpoint-group-region=us-central1

# 3. Setup SSL + forwarding rule (see full guide)

# 4. Enable Cloud Armor
gcloud compute security-policies create agentic-jarvis-armor
gcloud compute backend-services update agentic-jarvis-backend \
  --global --security-policy=agentic-jarvis-armor
```

---

## Key Configuration Changes (Localhost → Cloud Run)

### 1. Database Connection

**Before (SQLite)**:
```python
import sqlite3
conn = sqlite3.connect('data/tickets.db')
```

**After (Cloud SQL)**:
```python
import psycopg2
import os

conn = psycopg2.connect(os.getenv("DB_CONNECTION_STRING"))
# DB_CONNECTION_STRING from Secret Manager:
# postgresql://user:pass@/dbname?host=/cloudsql/project:region:instance
```

### 2. Agent Card URLs

**Before**:
```python
oxygen_agent = RemoteA2aAgent(
    agent_card="http://localhost:8082/.well-known/agent-card.json"
)
```

**After**:
```python
oxygen_agent = RemoteA2aAgent(
    agent_card="https://oxygen-agent-xxx.run.app/.well-known/agent-card.json",
    auth_scheme="bearerAuth",
    auth_credential=get_iam_token
)
```

### 3. Environment Variables

**Before (.env)**:
```bash
GOOGLE_API_KEY=sk-...
JWT_SECRET_KEY=secret123
```

**After (Secret Manager)**:
```bash
gcloud run deploy SERVICE \
  --set-secrets=GOOGLE_API_KEY=google-api-key:latest,JWT_SECRET_KEY=jwt-secret-key:latest
```

### 4. Port Binding

**Before**:
```python
# Hardcoded ports
app = to_a2a(tickets_agent, port=8080)
```

**After**:
```python
# Use PORT environment variable (Cloud Run requirement)
import os
port = int(os.getenv("PORT", 8080))
app = to_a2a(tickets_agent, port=port)
```

---

## Best Practices (2025 Official Recommendations)

### 1. Secrets Management

✅ **DO**:
- Store API keys, JWT secrets in Secret Manager
- Pin to specific secret versions (not `latest`)
- Cache secrets in memory (10-minute TTL)

❌ **DON'T**:
- Use environment variables for secrets
- Commit secrets to git
- Include secrets in Docker images

### 2. Cold Start Optimization

✅ **DO**:
- Use `python:3.11-slim` base image
- Enable CPU boost (`--cpu-boost`)
- Lazy import heavy libraries
- Precompile Python bytecode (`python -m compileall`)
- Set `min-instances=1` for critical services

❌ **DON'T**:
- Use full `python:3.11` image (too large)
- Import TensorFlow/PyTorch at module level (if not always needed)
- Set `min-instances` too high (cost increases)

### 3. Observability

✅ **DO**:
- Use Cloud Trace for distributed tracing (automatic with ADK)
- Implement structured logging (JSON format)
- Use OpenTelemetry for vendor-neutral instrumentation
- Exclude health check logs

❌ **DON'T**:
- Log sensitive data (tokens, passwords)
- Use DEBUG level in production
- Log every single request (use sampling for high-frequency events)

### 4. Networking

✅ **DO**:
- Use Direct VPC egress (no connector required in 2025)
- Deploy all services in same region (us-central1)
- Use Private Google Access for Cloud SQL
- Implement IAM-based service-to-service auth

❌ **DON'T**:
- Use public IPs for internal services
- Allow unauthenticated access to agent endpoints
- Expose Cloud SQL to public internet

---

## Migration Checklist (Quick)

### Pre-Deployment
- [ ] GCP project created
- [ ] Billing enabled
- [ ] APIs enabled
- [ ] gcloud CLI installed

### Infrastructure
- [ ] Artifact Registry created
- [ ] Cloud SQL instance + database created
- [ ] Secrets created (google-api-key, jwt-secret-key, db-connection-string)
- [ ] IAM permissions configured

### Application Changes
- [ ] Database: SQLite → PostgreSQL (psycopg2)
- [ ] Agent cards: localhost → Cloud Run URLs
- [ ] Port: hardcoded → os.getenv("PORT")
- [ ] Secrets: .env → Secret Manager
- [ ] Health check endpoints added

### Deployment
- [ ] Build Docker images (or use `adk deploy`)
- [ ] Deploy 6 services to Cloud Run
- [ ] Configure service-to-service IAM
- [ ] Setup Load Balancer + SSL
- [ ] Enable Cloud Armor

### Testing
- [ ] Health checks pass
- [ ] Agent cards accessible (/.well-known/agent-card.json)
- [ ] A2A communication works (RemoteA2aAgent)
- [ ] End-to-end user flows (Web UI → Agents)
- [ ] JWT authentication works
- [ ] Distributed tracing visible in Cloud Trace

### Production Readiness
- [ ] SSL certificate active
- [ ] DNS configured
- [ ] Budget alerts configured
- [ ] Monitoring dashboard created
- [ ] Runbook documented

---

## Common Issues & Solutions

### Issue: "503 Service Unavailable"
**Cause**: Cold start timeout
**Solution**:
```bash
gcloud run services update SERVICE --timeout=300 --cpu-boost
```

### Issue: "Permission denied" calling internal service
**Cause**: Missing IAM permissions
**Solution**:
```bash
gcloud run services add-iam-policy-binding TARGET \
  --member="serviceAccount:CALLER_SA" --role="roles/run.invoker"
```

### Issue: Agent card not accessible
**Cause**: HTTPS required, endpoint not public
**Solution**:
```python
@app.get("/.well-known/agent-card.json")
async def agent_card():
    return {...}
```

### Issue: High latency
**Cause**: Cold starts, no min-instances
**Solution**:
```bash
gcloud run services update SERVICE --min-instances=1
```

### Issue: High costs
**Cause**: Over-provisioned resources
**Solution**: Right-size memory/CPU, enable scale-to-zero

---

## Next Steps

### 1. Start with Dev/Staging

```bash
# Deploy to staging with scale-to-zero
gcloud run deploy SERVICE \
  --region=us-central1 \
  --min-instances=0 \
  --max-instances=5 \
  --memory=512Mi
```

**Cost**: $0 when idle, ~$10/month with light usage

### 2. Monitor for 30 Days

- Track request patterns
- Identify resource usage
- Measure Gemini API costs
- Validate cost projections

### 3. Optimize Based on Data

- Right-size memory/CPU
- Adjust min/max instances
- Implement caching for Gemini prompts
- Enable committed use discounts (Cloud SQL)

### 4. Evaluate Production Strategy

- **If traffic <400K req/mo**: Stay on Cloud Run
- **If traffic >500K req/mo**: Evaluate VPS or GKE with committed use
- **If budget-constrained**: Consider VPS ($56/month fixed)

---

## Resources

### Official Documentation
- [Cloud Run A2A Deployment Guide](https://cloud.google.com/run/docs/host-a2a-agents)
- [ADK Documentation](https://google.github.io/adk-docs/)
- [A2A Protocol Specification](https://a2a-protocol.org/latest/specification/)
- [Cloud Run Best Practices](https://cloud.google.com/run/docs/tips/general)

### Project Documentation
- **Full Deployment Guide**: [docs/GCP_DEPLOYMENT_GUIDE.md](./GCP_DEPLOYMENT_GUIDE.md)
- **Detailed Cost Analysis**: [docs/GCP_COST_ANALYSIS.md](./GCP_COST_ANALYSIS.md)
- **Architecture Guide**: [CLAUDE.md](../CLAUDE.md)

### Community Resources
- [ADK GitHub](https://github.com/google/adk-python)
- [A2A Protocol Community](https://a2aprotocol.ai/)
- [Google Cloud Community](https://www.googlecloudcommunity.com/)

---

## Quick Commands Reference

### Deploy Service (ADK CLI)
```bash
adk deploy cloud_run --project=$PROJECT_ID --region=us-central1
```

### Check Service Status
```bash
gcloud run services list --region=us-central1
```

### View Logs
```bash
gcloud run services logs read SERVICE_NAME --region=us-central1 --limit=50
```

### Test Agent Card
```bash
curl https://SERVICE-xxx.run.app/.well-known/agent-card.json
```

### Monitor Costs
```bash
gcloud billing budgets list --billing-account=ACCOUNT_ID
```

### Update Service
```bash
gcloud run services update SERVICE --memory=1Gi --cpu=2
```

---

**For detailed information, see:**
- [GCP_DEPLOYMENT_GUIDE.md](./GCP_DEPLOYMENT_GUIDE.md) - Complete deployment instructions
- [GCP_COST_ANALYSIS.md](./GCP_COST_ANALYSIS.md) - Detailed cost breakdown and optimization
