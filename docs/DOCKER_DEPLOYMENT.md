# Docker Deployment Guide

**Date**: November 15, 2025
**Status**: ✅ **Production Ready**

This guide covers deploying the Dividend API and Documentation Site using Docker containers.

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Configuration](#configuration)
5. [Building Images](#building-images)
6. [Running Containers](#running-containers)
7. [Production Deployment](#production-deployment)
8. [Monitoring & Logs](#monitoring--logs)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Topics](#advanced-topics)

---

## Overview

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     Docker Network                       │
│                    (dividend-network)                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐      ┌──────────────┐                │
│  │   Frontend   │      │   Backend    │                │
│  │  (Next.js)   │◄────►│  (FastAPI)   │                │
│  │  Port: 3000  │      │  Port: 8000  │                │
│  └──────────────┘      └──────────────┘                │
│         │                      │                         │
│         │                      │                         │
│         ▼                      ▼                         │
│  ┌────────────────────────────────────────┐             │
│  │      Supabase Remote Database          │             │
│  │  (db.uykxgbrzpfswbdxtyzlv.supabase.co) │             │
│  └────────────────────────────────────────┘             │
│                                                          │
│  Optional:                                               │
│  ┌──────────────┐                                       │
│  │    Redis     │ (Cache - start with --profile cache)  │
│  │  Port: 6379  │                                       │
│  └──────────────┘                                       │
└─────────────────────────────────────────────────────────┘
```

### Container Details

| Container | Base Image | Size (approx) | Purpose |
|-----------|------------|---------------|---------|
| **backend** | python:3.11-slim | ~200MB | FastAPI REST API |
| **frontend** | node:20-alpine | ~150MB | Next.js documentation site |
| **redis** (optional) | redis:7-alpine | ~40MB | Response caching |

---

## Prerequisites

### Required Software

```bash
# Docker Engine
docker --version  # Should be >= 20.10

# Docker Compose
docker-compose --version  # Should be >= 2.0

# Git
git --version
```

### Install Docker

**macOS**:
```bash
brew install --cask docker
```

**Linux**:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**Windows**:
Download Docker Desktop from https://www.docker.com/products/docker-desktop

---

## Quick Start

### 1. Clone Repository

```bash
cd /path/to/your/projects
git clone <repository-url>
cd high-yield-dividend-analysis
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your credentials
nano .env
```

**Required variables**:
```bash
# Supabase (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# API Keys (REQUIRED for data fetching)
FMP_API_KEY=your-fmp-api-key
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key

# Security (REQUIRED - change these!)
SECRET_KEY=your-secret-key-minimum-32-characters-long
SESSION_SECRET=your-session-secret-minimum-32-characters

# Google OAuth (OPTIONAL - for authentication)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

### 3. Build and Run

```bash
# Build images and start containers
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 4. Access Services

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (if enabled)
- **Health Check**: http://localhost:8000/health

### 5. Stop Services

```bash
# Stop containers
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

---

## Configuration

### Environment Variables

#### Backend (FastAPI)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUPABASE_URL` | ✅ Yes | - | Supabase project URL |
| `SUPABASE_KEY` | ✅ Yes | - | Anonymous/public key |
| `SUPABASE_SERVICE_ROLE_KEY` | ✅ Yes | - | Service role key (admin) |
| `FMP_API_KEY` | ✅ Yes | - | Financial Modeling Prep API key |
| `ALPHA_VANTAGE_API_KEY` | ✅ Yes | - | Alpha Vantage API key |
| `SECRET_KEY` | ✅ Yes | - | JWT signing key (32+ chars) |
| `SESSION_SECRET` | ✅ Yes | - | Session encryption key |
| `GOOGLE_CLIENT_ID` | ❌ No | - | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | ❌ No | - | Google OAuth secret |
| `ENVIRONMENT` | ❌ No | `production` | Environment (development/production) |
| `ALLOWED_ORIGINS` | ❌ No | `http://localhost:3000` | CORS allowed origins |

#### Frontend (Next.js)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | ❌ No | `http://localhost:8000` | Backend API URL |
| `NEXT_PUBLIC_SUPABASE_URL` | ✅ Yes | - | Supabase URL (client-side) |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | ✅ Yes | - | Supabase anon key (client-side) |

---

## Building Images

### Build Individual Images

```bash
# Backend only
docker build -f Dockerfile.backend -t dividend-api:latest .

# Frontend only
docker build -f Dockerfile.frontend -t dividend-docs:latest .
```

### Build with Docker Compose

```bash
# Build all services
docker-compose build

# Build with no cache (clean build)
docker-compose build --no-cache

# Build specific service
docker-compose build backend
```

### Multi-Platform Builds

For deploying to different architectures (e.g., ARM):

```bash
# Enable buildx
docker buildx create --use

# Build for multiple platforms
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  -f Dockerfile.backend \
  -t dividend-api:latest \
  --push \
  .
```

---

## Running Containers

### Start All Services

```bash
# Start in detached mode
docker-compose up -d

# Start with logs
docker-compose up

# Start specific service
docker-compose up -d backend
```

### Start with Redis Cache

```bash
# Start with optional Redis cache
docker-compose --profile with-cache up -d
```

### Scale Services

```bash
# Run multiple backend instances (load balancing)
docker-compose up -d --scale backend=3
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart specific service
docker-compose restart backend
```

---

## Production Deployment

### Production docker-compose.yml

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile.backend
      args:
        - BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
        - VERSION=1.0.0
    restart: always
    environment:
      - ENVIRONMENT=production
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G
      replicas: 2

  frontend:
    build:
      context: .
      dockerfile: Dockerfile.frontend
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend
    restart: always
```

### Deploy to Production

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Update running containers
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### Nginx Reverse Proxy (Production)

Create `nginx.conf`:

```nginx
upstream backend {
    least_conn;
    server backend:8000;
}

upstream frontend {
    least_conn;
    server frontend:3000;
}

server {
    listen 80;
    server_name yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;

    # API
    location /api/ {
        proxy_pass http://backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_cache_bypass $http_upgrade;
    }
}
```

---

## Monitoring & Logs

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# Since specific time
docker-compose logs --since 2025-11-15T10:00:00 backend
```

### Container Stats

```bash
# Real-time stats
docker stats

# Specific container
docker stats dividend-api
```

### Health Checks

```bash
# Check container health
docker ps --format "table {{.Names}}\t{{.Status}}"

# Inspect health check
docker inspect --format='{{.State.Health.Status}}' dividend-api

# Manual health check
curl http://localhost:8000/health
curl http://localhost:3000/
```

### Monitoring Stack (Optional)

Add to `docker-compose.yml`:

```yaml
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    depends_on:
      - prometheus
```

---

## Troubleshooting

### Common Issues

#### 1. Backend Won't Start

**Symptom**: Backend container exits immediately

**Check logs**:
```bash
docker-compose logs backend
```

**Common causes**:
- Missing environment variables
- Database connection failed
- Port 8000 already in use

**Solutions**:
```bash
# Check environment
docker-compose exec backend env | grep SUPABASE

# Test database connection
docker-compose exec backend python -c "from supabase_helpers import get_supabase_client; print(get_supabase_client())"

# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use port 8001 instead
```

#### 2. Frontend Build Fails

**Symptom**: Frontend container fails during build

**Check build logs**:
```bash
docker-compose build frontend 2>&1 | tee build.log
```

**Common causes**:
- Out of memory during build
- Missing dependencies
- TypeScript errors

**Solutions**:
```bash
# Increase Docker memory
# Docker Desktop > Settings > Resources > Memory: 4GB+

# Build with more memory
docker build \
  --build-arg NODE_OPTIONS="--max-old-space-size=4096" \
  -f Dockerfile.frontend \
  -t dividend-docs:latest \
  .

# Skip TypeScript checks (not recommended for production)
# Add to next.config.js:
# typescript: { ignoreBuildErrors: true }
```

#### 3. Cannot Connect to Database

**Symptom**: Backend logs show database connection errors

**Check**:
```bash
# Test from container
docker-compose exec backend ping db.uykxgbrzpfswbdxtyzlv.supabase.co

# Check environment
docker-compose exec backend printenv | grep SUPABASE_URL
```

**Solutions**:
```bash
# Verify credentials in .env
cat .env | grep SUPABASE

# Test connection manually
docker-compose exec backend python -c "
import os
from supabase import create_client
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')
client = create_client(url, key)
print(client.table('raw_stocks').select('symbol').limit(1).execute())
"
```

#### 4. Permission Denied Errors

**Symptom**: Container can't write to volumes

**Solutions**:
```bash
# Fix log directory permissions
chmod -R 777 logs/

# Or run container as root (not recommended)
# Add to docker-compose.yml:
user: "0:0"
```

#### 5. Out of Disk Space

**Check disk usage**:
```bash
docker system df
```

**Clean up**:
```bash
# Remove unused images
docker image prune -a

# Remove stopped containers
docker container prune

# Remove all unused data
docker system prune -a --volumes
```

### Debug Container

```bash
# Get shell in running container
docker-compose exec backend /bin/bash

# Run command in container
docker-compose exec backend python -c "import sys; print(sys.version)"

# Check container filesystem
docker-compose exec backend ls -la /app

# View environment
docker-compose exec backend env
```

---

## Advanced Topics

### Custom Networks

```yaml
networks:
  frontend-network:
    driver: bridge
  backend-network:
    driver: bridge
    internal: true  # No external access

services:
  backend:
    networks:
      - backend-network
      - frontend-network
```

### Secrets Management

Use Docker secrets instead of environment variables:

```yaml
services:
  backend:
    secrets:
      - supabase_key
      - secret_key

secrets:
  supabase_key:
    file: ./secrets/supabase_key.txt
  secret_key:
    file: ./secrets/secret_key.txt
```

### Auto-Updates with Watchtower

```yaml
services:
  watchtower:
    image: containrrr/watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    command: --interval 3600  # Check every hour
```

### Backup Strategy

```bash
# Backup volumes
docker run --rm \
  -v dividend-redis-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/redis-backup-$(date +%Y%m%d).tar.gz /data

# Restore volumes
docker run --rm \
  -v dividend-redis-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/redis-backup-20251115.tar.gz -C /
```

### CI/CD Integration

**GitHub Actions** (`.github/workflows/docker.yml`):

```yaml
name: Docker Build and Push

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build backend
        run: docker build -f Dockerfile.backend -t dividend-api:latest .

      - name: Build frontend
        run: docker build -f Dockerfile.frontend -t dividend-docs:latest .

      - name: Push to registry
        run: |
          echo "${{ secrets.DOCKER_PASSWORD }}" | docker login -u "${{ secrets.DOCKER_USERNAME }}" --password-stdin
          docker push dividend-api:latest
          docker push dividend-docs:latest
```

---

## Performance Optimization

### Image Size Optimization

Current sizes:
- Backend: ~200MB (multi-stage build)
- Frontend: ~150MB (Next.js standalone)

**Already optimized**:
- ✅ Multi-stage builds
- ✅ Alpine base images (where possible)
- ✅ .dockerignore files
- ✅ Only production dependencies

### Runtime Optimization

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
      replicas: 3
    environment:
      - WORKERS=4  # Uvicorn workers
```

### Caching Strategy

```yaml
services:
  redis:
    command: >
      redis-server
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --save 60 1000
      --appendonly yes
```

---

## Quick Reference

### Common Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# View logs
docker-compose logs -f backend

# Shell into container
docker-compose exec backend /bin/bash

# Check status
docker-compose ps

# Update containers
docker-compose pull && docker-compose up -d

# Clean everything
docker-compose down -v && docker system prune -a
```

### Ports

| Service | Internal Port | External Port | Access |
|---------|---------------|---------------|--------|
| Backend | 8000 | 8000 | http://localhost:8000 |
| Frontend | 3000 | 3000 | http://localhost:3000 |
| Redis | 6379 | 6379 | redis://localhost:6379 |

### File Structure

```
high-yield-dividend-analysis/
├── Dockerfile.backend           # Backend container definition
├── Dockerfile.frontend          # Frontend container definition
├── docker-compose.yml           # Development setup
├── docker-compose.prod.yml      # Production setup
├── .dockerignore               # Backend build exclusions
├── docs-site/
│   └── .dockerignore           # Frontend build exclusions
├── .env                        # Environment variables (gitignored)
└── .env.example                # Template for .env
```

---

## Security Checklist

- [ ] Change default `SECRET_KEY` and `SESSION_SECRET`
- [ ] Use strong passwords for all services
- [ ] Enable HTTPS in production (use nginx + Let's Encrypt)
- [ ] Run containers as non-root user (already configured)
- [ ] Keep `.env` out of git (already in .gitignore)
- [ ] Regularly update base images (`docker-compose pull`)
- [ ] Use Docker secrets for sensitive data in production
- [ ] Enable firewall rules to restrict access
- [ ] Set up automated backups
- [ ] Monitor container logs for suspicious activity

---

## Support

**Documentation**: `docs/DOCKER_DEPLOYMENT.md` (this file)
**Issues**: Create issue in GitHub repository
**Docker Docs**: https://docs.docker.com

---

**Last Updated**: November 15, 2025
**Version**: 1.0.0
**Tested On**: Docker 24.0.7, Docker Compose 2.23.0
