# Divv API - Quick Start Guide

Get your entire stack running locally or deployed to Railway in minutes.

## 🎯 What's Included

- **FastAPI Backend** - Python API with dividend data
- **Next.js Frontend** - Documentation and API key management
- **Redis** - Caching and rate limiting
- **Nginx** - Unified routing (production)
- **Supabase** - PostgreSQL database (remote)

---

## 🚀 Quick Deploy to Railway (5 minutes)

### 1. Fork & Push to GitHub

```bash
git clone https://github.com/yourusername/high-yield-dividend-analysis.git
cd high-yield-dividend-analysis
git push origin main
```

### 2. Deploy to Railway

1. Go to [railway.app/new](https://railway.app/new)
2. Click **Deploy from GitHub**
3. Select your repository
4. Add environment variables from `.env.railway.example`
5. Click **Deploy**

**Done!** Your API is live at `https://your-app.railway.app`

📖 **Full guide:** See [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)

---

## 💻 Local Development

### Prerequisites

- Docker Desktop installed
- Git
- Node.js 20+ (optional, for local frontend dev)
- Python 3.11+ (optional, for local backend dev)

### Option 1: Docker Compose (Recommended)

**Start everything:**
```bash
docker-compose up -d
```

**Access:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Redis: localhost:6379

**Stop:**
```bash
docker-compose down
```

### Option 2: Local Development (Hot Reload)

**Backend:**
```bash
# Install dependencies
cd api
pip install -r requirements.txt

# Run dev server
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
# Install dependencies
cd docs-site
npm install

# Run dev server
npm run dev
```

---

## 🔧 Environment Setup

### 1. Copy Environment Template

```bash
cp .env.example .env
```

### 2. Required Variables

Edit `.env` and set:

```env
# Supabase (from your dashboard)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# API Keys
FMP_API_KEY=your-fmp-key
ALPHA_VANTAGE_API_KEY=your-alpha-vantage-key

# Security (generate with: openssl rand -hex 32)
SECRET_KEY=your-random-secret
```

---

## 📊 Verify Installation

### Health Check

```bash
curl http://localhost:8000/health
# {"status": "healthy"}
```

### Test API Endpoint

```bash
curl http://localhost:8000/v1/stocks/AAPL/quote
```

### Access Frontend

Open browser: http://localhost:3000

---

## 🎨 Architecture

### Development (Local)

```
┌─────────────┐     ┌─────────────┐
│   Next.js   │────▶│   FastAPI   │
│   :3000     │     │   :8000     │
└─────────────┘     └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │    Redis    │
                    │    :6379    │
                    └─────────────┘
```

### Production (Railway)

```
                ┌─────────────┐
                │   Railway   │
                │   (Domain)  │
                └──────┬──────┘
                       │
                ┌──────▼──────┐
                │    Nginx    │
                │    :80      │
                └──────┬──────┘
         ┌─────────────┴─────────────┐
         │                           │
  ┌──────▼──────┐            ┌──────▼──────┐
  │   Next.js   │            │   FastAPI   │
  │   :3000     │            │   :8000     │
  └─────────────┘            └──────┬──────┘
                                    │
                             ┌──────▼──────┐
                             │    Redis    │
                             │    :6379    │
                             └─────────────┘
```

---

## 📁 Project Structure

```
high-yield-dividend-analysis/
├── api/                      # FastAPI backend
│   ├── main.py              # API entry point
│   ├── routers/             # API endpoints
│   └── requirements.txt     # Python deps
├── docs-site/               # Next.js frontend
│   ├── app/                 # Next.js pages
│   ├── components/          # React components
│   └── package.json         # Node deps
├── lib/                     # Shared Python libraries
├── scripts/                 # Data scrapers & utilities
├── supabase/               # Database migrations
│   └── migrations/         # SQL migration files
├── nginx/                  # Nginx configs
│   ├── nginx.conf          # Production config
│   └── nginx.railway.conf  # Railway config
├── docker-compose.yml           # Development
├── docker-compose.railway.yml   # Railway production
├── Dockerfile.backend           # Backend container
├── Dockerfile.frontend          # Frontend container
├── railway.toml                 # Railway config
└── RAILWAY_DEPLOYMENT.md        # Deployment guide
```

---

## 🔑 Common Commands

### Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild containers
docker-compose up --build

# Remove everything (including volumes)
docker-compose down -v
```

### Railway CLI

```bash
# Install
npm i -g @railway/cli

# Login
railway login

# Link project
railway link

# View logs
railway logs

# Deploy
railway up

# Add variables
railway variables set KEY=value
```

### Database Migrations

```bash
# Run migration
PGPASSWORD="$SUPABASE_DB_PASSWORD" psql \
  -h db.your-project.supabase.co \
  -p 5432 \
  -U postgres \
  -d postgres \
  -f supabase/migrations/your-migration.sql
```

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find process
lsof -ti:3000 | xargs kill
lsof -ti:8000 | xargs kill
```

### Docker Issues

```bash
# Reset Docker
docker-compose down -v
docker system prune -a

# Rebuild from scratch
docker-compose up --build
```

### Environment Variables Not Loading

```bash
# Verify .env exists
cat .env

# Docker: recreate containers
docker-compose up --force-recreate
```

### API Not Connecting to Database

```bash
# Test Supabase connection
curl https://your-project.supabase.co/rest/v1/

# Check API logs
docker-compose logs backend
```

---

## 📚 Next Steps

### Development
1. Read [API Documentation](http://localhost:8000/docs)
2. Explore [Frontend Code](./docs-site/README.md)
3. Check [Database Schema](./supabase/migrations/)

### Deployment
1. Deploy to Railway: [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)
2. Add Cloudflare CDN: [CLOUDFLARE_SETUP.md](./CLOUDFLARE_SETUP.md)
3. Monitor performance in Railway dashboard

### Scaling
1. Monitor metrics in Railway
2. Increase resources as needed
3. Add horizontal scaling (multiple replicas)
4. Consider Redis Cloud for distributed caching

---

## 🆘 Getting Help

- **API Issues**: Check logs with `docker-compose logs backend`
- **Frontend Issues**: Check logs with `docker-compose logs frontend`
- **Railway Issues**: Check [Railway docs](https://docs.railway.app)
- **Supabase Issues**: Check [Supabase docs](https://supabase.com/docs)

---

## 💰 Cost Summary

### Development (Local)
- **Cost**: $0/month
- Just your electricity!

### Production (Railway + Cloudflare)
- **Railway**: $10-15/month (1-2GB RAM)
- **Cloudflare**: $0/month (free tier)
- **Supabase**: $0-25/month (free tier or Pro)
- **Total**: $10-40/month

---

**Built with ❤️ using FastAPI, Next.js, and Railway**

Happy coding! 🚀
