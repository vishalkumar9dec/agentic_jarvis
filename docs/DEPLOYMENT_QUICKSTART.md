# Jarvis Deployment Quick Start Guide

This is a condensed version of the full deployment strategy. For complete details, see [DEPLOYMENT_STRATEGY.md](./DEPLOYMENT_STRATEGY.md).

---

## TL;DR - Deploy in 30 Minutes

**Recommended**: Docker Compose on DigitalOcean + Railway PostgreSQL

**Total Cost**: ~$35/month
**Time**: 30-60 minutes
**Supports**: 1,000-10,000 users

---

## Prerequisites

- DigitalOcean account (or any VPS provider)
- Railway account (for managed PostgreSQL)
- Domain name (optional but recommended)
- GitHub account (for CI/CD)
- Google API key

---

## Step 1: Set Up Database (5 minutes)

### Option A: Railway PostgreSQL (Recommended)

1. Go to [Railway](https://railway.app)
2. Create new project → Add PostgreSQL
3. Copy connection string: `postgresql://user:pass@host:port/db`
4. Cost: $5/month for 1GB

### Option B: Neon (Free Tier)

1. Go to [Neon](https://neon.tech)
2. Create free database (512MB)
3. Copy connection string
4. Cost: Free up to 512MB

---

## Step 2: Create Server (5 minutes)

### DigitalOcean Droplet

```bash
# Using doctl CLI
doctl compute droplet create jarvis-prod \
  --region nyc3 \
  --size s-2vcpu-4gb \
  --image ubuntu-22-04-x64 \
  --ssh-keys YOUR_SSH_KEY_ID

# Or use web UI:
# - 2 vCPU, 4GB RAM ($24/month)
# - Ubuntu 22.04 LTS
# - NYC3 datacenter
```

**Alternative Providers:**
- **Linode**: 4GB Shared CPU - $24/month
- **Vultr**: 2 vCPU, 4GB - $24/month
- **Hetzner**: CX21 (2 vCPU, 4GB) - €5.83/month (~$6)

---

## Step 3: Server Setup (10 minutes)

```bash
# SSH into server
ssh root@YOUR_SERVER_IP

# Run automated setup script
curl -fsSL https://raw.githubusercontent.com/yourusername/agentic_jarvis/main/scripts/setup_server.sh | bash

# Or manual setup:
apt update && apt upgrade -y
curl -fsSL https://get.docker.com | sh
apt install docker-compose-plugin -y

# Firewall
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable

# Create app directory
mkdir -p /opt/jarvis
cd /opt/jarvis
```

---

## Step 4: Deploy Application (10 minutes)

```bash
# Clone repository
cd /opt/jarvis
git clone https://github.com/yourusername/agentic_jarvis.git .

# Create production .env
cat > .env << EOF
GOOGLE_API_KEY=your_google_api_key_here
JWT_SECRET_KEY=$(openssl rand -base64 32)
JWT_ALGORITHM=HS256
DATABASE_URL=postgresql://user:pass@host:port/jarvis
AUTH_SERVICE_URL=http://auth-service:9998
REGISTRY_SERVICE_URL=http://registry-service:8003
EOF

# Create minimal docker-compose.yml (use production one from repo)
# Build and start
docker compose build
docker compose up -d

# Check status
docker compose ps
docker compose logs -f
```

---

## Step 5: Configure Nginx + SSL (5 minutes)

```bash
# Install certbot
apt install certbot python3-certbot-nginx -y

# Get SSL certificate (interactive)
certbot --nginx -d your-domain.com

# Or use the nginx.conf from the repository
cp nginx.conf /etc/nginx/sites-available/jarvis
ln -s /etc/nginx/sites-available/jarvis /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

---

## Step 6: Verify Deployment (5 minutes)

```bash
# Health checks
curl http://localhost/health
curl http://localhost/auth/health
curl http://localhost/api/health

# Test authentication
curl -X POST http://localhost/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"username":"vishal","password":"password123"}'

# Check all services
docker compose ps

# Expected output:
# All services should show "healthy" status
```

---

## Minimal docker-compose.yml

Create `/opt/jarvis/docker-compose.yml`:

```yaml
version: '3.8'

services:
  auth-service:
    build: ./auth
    container_name: jarvis-auth
    env_file: .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9998/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    networks:
      - jarvis-network

  registry-service:
    build: ./agent_registry_service
    container_name: jarvis-registry
    env_file: .env
    volumes:
      - registry-data:/app/data
    depends_on:
      - auth-service
    restart: unless-stopped
    networks:
      - jarvis-network

  tickets-agent:
    build:
      context: .
      dockerfile: tickets_agent_service/Dockerfile
    container_name: jarvis-tickets
    env_file: .env
    depends_on:
      - registry-service
    restart: unless-stopped
    networks:
      - jarvis-network

  finops-agent:
    build:
      context: .
      dockerfile: finops_agent_service/Dockerfile
    container_name: jarvis-finops
    env_file: .env
    depends_on:
      - registry-service
    restart: unless-stopped
    networks:
      - jarvis-network

  oxygen-agent:
    build:
      context: .
      dockerfile: oxygen_agent_service/Dockerfile
    container_name: jarvis-oxygen
    env_file: .env
    depends_on:
      - registry-service
    restart: unless-stopped
    networks:
      - jarvis-network

  web-ui:
    build: ./web_ui
    container_name: jarvis-web
    env_file: .env
    ports:
      - "80:9999"
    depends_on:
      - auth-service
      - tickets-agent
      - finops-agent
      - oxygen-agent
    restart: unless-stopped
    networks:
      - jarvis-network

networks:
  jarvis-network:
    driver: bridge

volumes:
  registry-data:
```

---

## Minimal Dockerfile Templates

### Auth Service Dockerfile

Create `auth/Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 9998
CMD ["uvicorn", "auth_server:app", "--host", "0.0.0.0", "--port", "9998"]
```

### Agent Service Dockerfile Template

Create `tickets_agent_service/Dockerfile`:

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["uvicorn", "tickets_agent_service.agent:a2a_app", "--host", "0.0.0.0", "--port", "8080"]
```

Repeat for `finops_agent_service` (port 8081) and `oxygen_agent_service` (port 8082).

---

## Database Migration (SQLite → PostgreSQL)

```python
# migration_script.py
import sqlite3
import psycopg2
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Connect to databases
sqlite_conn = sqlite3.connect('data/sessions.db')
pg_conn = psycopg2.connect(os.getenv('DATABASE_URL'))

# Migrate sessions
sqlite_cursor = sqlite_conn.cursor()
pg_cursor = pg_conn.cursor()

# Create table
pg_cursor.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        session_id VARCHAR(255) PRIMARY KEY,
        user_id VARCHAR(255),
        data JSONB,
        created_at TIMESTAMP,
        updated_at TIMESTAMP
    )
""")

# Copy data
sqlite_cursor.execute("SELECT * FROM sessions")
for row in sqlite_cursor.fetchall():
    pg_cursor.execute(
        "INSERT INTO sessions VALUES (%s, %s, %s, %s, %s)",
        row
    )

pg_conn.commit()
print("Migration complete!")
```

Run:
```bash
python migration_script.py
```

---

## Monitoring Setup

### Quick Monitoring Stack

```bash
# cAdvisor (container metrics)
docker run -d \
  --name=cadvisor \
  --volume=/:/rootfs:ro \
  --volume=/var/run:/var/run:ro \
  --volume=/sys:/sys:ro \
  --volume=/var/lib/docker/:/var/lib/docker:ro \
  --publish=8080:8080 \
  google/cadvisor:latest

# Dozzle (log viewer)
docker run -d \
  --name=dozzle \
  --volume=/var/run/docker.sock:/var/run/docker.sock:ro \
  --publish=8081:8080 \
  amir20/dozzle:latest

# Access:
# - cAdvisor: http://your-server-ip:8080
# - Dozzle: http://your-server-ip:8081
```

### UptimeRobot (Free External Monitoring)

1. Go to [UptimeRobot](https://uptimerobot.com)
2. Add monitors:
   - HTTP(s): https://your-domain.com/health
   - HTTP(s): https://your-domain.com/auth/health
3. Set up email/Slack alerts

---

## Backup Setup

```bash
# Create backup script
cat > /opt/jarvis/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/jarvis/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
pg_dump $DATABASE_URL | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Backup volumes
docker run --rm \
  --volumes-from jarvis-registry \
  -v $BACKUP_DIR:/backup \
  alpine tar czf /backup/registry_$DATE.tar.gz /app/data

# Keep last 7 days
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /opt/jarvis/backup.sh

# Schedule daily at 2 AM
echo "0 2 * * * /opt/jarvis/backup.sh >> /var/log/jarvis-backup.log 2>&1" | crontab -
```

---

## CI/CD Setup (GitHub Actions)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to server
        uses: appleboy/ssh-action@v1.0.0
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_PRIVATE_KEY }}
          script: |
            cd /opt/jarvis
            git pull origin main
            docker compose build
            docker compose up -d
            docker system prune -f
```

Add secrets in GitHub:
- `SERVER_HOST`: Your server IP
- `SERVER_USER`: `root`
- `SSH_PRIVATE_KEY`: Your SSH private key

---

## Troubleshooting

### Services won't start

```bash
# Check logs
docker compose logs auth-service
docker compose logs registry-service

# Check environment variables
docker compose exec auth-service env | grep GOOGLE_API_KEY

# Restart specific service
docker compose restart auth-service
```

### Database connection issues

```bash
# Test PostgreSQL connection
docker compose exec auth-service bash
pip install psycopg2-binary
python -c "import psycopg2; psycopg2.connect('$DATABASE_URL')"

# Check DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql://user:pass@host:port/dbname
```

### Port conflicts

```bash
# Check what's using ports
lsof -i :80
lsof -i :9998

# Kill processes
lsof -ti:80 | xargs kill -9
```

### High memory usage

```bash
# Check container stats
docker stats

# Set memory limits in docker-compose.yml
services:
  auth-service:
    mem_limit: 512m
    mem_reservation: 256m
```

---

## Common Operations

### View Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f auth-service

# Last 100 lines
docker compose logs --tail=100 auth-service
```

### Restart Services

```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart auth-service

# Rebuild and restart
docker compose up -d --build auth-service
```

### Update Code

```bash
cd /opt/jarvis
git pull origin main
docker compose build
docker compose up -d
```

### Scale Services

```bash
# Scale horizontally (multiple instances)
docker compose up -d --scale tickets-agent=3

# Scale vertically (upgrade server)
# Resize droplet in DigitalOcean dashboard
# Services automatically get more resources
```

---

## Cost Optimization Tips

1. **Use Hetzner instead of DigitalOcean**: Save ~70% ($6/month vs $24/month)
2. **Use Neon free tier**: Save $5-15/month on database
3. **Reserve instances**: Save 30-40% with 1-year commitment
4. **Use spot instances** (AWS): Save up to 90% (for non-critical services)
5. **Optimize Docker images**: Use multi-stage builds, Alpine Linux
6. **Enable caching**: Reduce Gemini API calls (biggest variable cost)

---

## When to Upgrade

### Upgrade to bigger server when:
- CPU usage consistently > 70%
- Memory usage > 80%
- Response times > 500ms
- Users > 5,000

### Migrate to Kubernetes when:
- Users > 50,000
- Need multi-region deployment
- Team size > 5 developers
- Require 99.99% uptime
- Need complex deployment strategies (canary, blue-green)

---

## Next Steps

1. Set up monitoring and alerts
2. Configure automated backups
3. Add custom domain with SSL
4. Implement rate limiting
5. Set up log aggregation
6. Plan capacity for growth

For detailed information, see [DEPLOYMENT_STRATEGY.md](./DEPLOYMENT_STRATEGY.md).

---

## Support Resources

- **Documentation**: [docs/](.)
- **Issues**: GitHub Issues
- **Community**: [Your community channel]
- **Deployment Guide**: [DEPLOYMENT_STRATEGY.md](./DEPLOYMENT_STRATEGY.md)

---

**Last Updated**: 2025-12-31
