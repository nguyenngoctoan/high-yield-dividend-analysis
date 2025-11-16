#!/bin/bash
# ============================================================================
# Production Deployment Script for Dividend API
# ============================================================================
# This script automates the production deployment process with safety checks
# and rollback capabilities.
#
# Usage:
#   ./deploy-production.sh [options]
#
# Options:
#   --build-only     Build images without deploying
#   --no-backup      Skip backup before deployment
#   --skip-checks    Skip pre-deployment checks
#   --rollback       Rollback to previous deployment
# ============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"
BACKUP_DIR="./backups/deployments"
VERSION=$(date +%Y%m%d_%H%M%S)

# Parse arguments
BUILD_ONLY=false
NO_BACKUP=false
SKIP_CHECKS=false
ROLLBACK=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --build-only)
            BUILD_ONLY=true
            shift
            ;;
        --no-backup)
            NO_BACKUP=true
            shift
            ;;
        --skip-checks)
            SKIP_CHECKS=true
            shift
            ;;
        --rollback)
            ROLLBACK=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# ============================================================================
# Helper functions
# ============================================================================

log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

check_requirements() {
    log_info "Checking requirements..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    # Check .env file
    if [ ! -f "$ENV_FILE" ]; then
        log_error ".env file not found"
        exit 1
    fi

    # Check production compose file
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "$COMPOSE_FILE not found"
        exit 1
    fi

    log_success "All requirements met"
}

pre_deployment_checks() {
    if [ "$SKIP_CHECKS" = true ]; then
        log_warning "Skipping pre-deployment checks"
        return
    fi

    log_info "Running pre-deployment checks..."

    # Check environment variables
    log_info "Validating environment variables..."
    required_vars=(
        "SUPABASE_URL"
        "SUPABASE_KEY"
        "SUPABASE_SERVICE_ROLE_KEY"
        "FMP_API_KEY"
        "SECRET_KEY"
        "SESSION_SECRET"
    )

    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$ENV_FILE"; then
            log_error "Missing required environment variable: $var"
            exit 1
        fi
    done

    # Check SECRET_KEY length
    SECRET_KEY=$(grep "^SECRET_KEY=" "$ENV_FILE" | cut -d'=' -f2)
    if [ ${#SECRET_KEY} -lt 32 ]; then
        log_error "SECRET_KEY must be at least 32 characters long"
        exit 1
    fi

    # Warn about default passwords
    if grep -q "change-this" "$ENV_FILE"; then
        log_warning "Default passwords detected in .env file"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    log_success "Pre-deployment checks passed"
}

backup_current_deployment() {
    if [ "$NO_BACKUP" = true ]; then
        log_warning "Skipping backup"
        return
    fi

    log_info "Creating backup of current deployment..."

    mkdir -p "$BACKUP_DIR"

    # Backup environment file
    cp "$ENV_FILE" "$BACKUP_DIR/.env.$VERSION"

    # Backup docker-compose state
    docker-compose -f "$COMPOSE_FILE" ps > "$BACKUP_DIR/services.$VERSION.txt" 2>&1 || true

    # Export current images
    log_info "Backing up current Docker images..."
    docker save dividend-api:latest -o "$BACKUP_DIR/backend.$VERSION.tar" 2>/dev/null || true
    docker save dividend-docs:latest -o "$BACKUP_DIR/frontend.$VERSION.tar" 2>/dev/null || true

    log_success "Backup created at $BACKUP_DIR"
}

build_images() {
    log_info "Building Docker images..."

    export BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
    export VERSION="$VERSION"

    docker-compose -f "$COMPOSE_FILE" build --no-cache

    log_success "Images built successfully"
}

deploy() {
    log_info "Deploying to production..."

    # Pull any updated base images
    log_info "Pulling latest base images..."
    docker-compose -f "$COMPOSE_FILE" pull || true

    # Start services
    log_info "Starting services..."
    docker-compose -f "$COMPOSE_FILE" up -d

    # Wait for services to be healthy
    log_info "Waiting for services to become healthy..."
    sleep 10

    # Check health
    max_attempts=30
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up (healthy)"; then
            log_success "Services are healthy"
            break
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    echo

    if [ $attempt -eq $max_attempts ]; then
        log_error "Services did not become healthy in time"
        log_info "Check logs with: docker-compose -f $COMPOSE_FILE logs"
        exit 1
    fi

    log_success "Deployment completed successfully"
}

post_deployment_checks() {
    log_info "Running post-deployment checks..."

    # Check if services are running
    if ! docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        log_error "Services are not running"
        return 1
    fi

    # Test backend health endpoint
    log_info "Testing backend health endpoint..."
    if curl -f -s http://localhost:8000/health > /dev/null 2>&1; then
        log_success "Backend is responding"
    else
        log_warning "Backend health check failed"
    fi

    # Test frontend
    log_info "Testing frontend..."
    if curl -f -s http://localhost:3000 > /dev/null 2>&1; then
        log_success "Frontend is responding"
    else
        log_warning "Frontend is not responding"
    fi

    log_success "Post-deployment checks completed"
}

rollback_deployment() {
    log_warning "Rolling back to previous deployment..."

    # Find latest backup
    latest_backup=$(ls -t "$BACKUP_DIR"/.env.* 2>/dev/null | head -1)

    if [ -z "$latest_backup" ]; then
        log_error "No backup found to rollback to"
        exit 1
    fi

    backup_version=$(basename "$latest_backup" | sed 's/.env.//')
    log_info "Rolling back to version: $backup_version"

    # Stop current services
    docker-compose -f "$COMPOSE_FILE" down

    # Restore environment
    cp "$latest_backup" "$ENV_FILE"

    # Load backup images
    if [ -f "$BACKUP_DIR/backend.$backup_version.tar" ]; then
        docker load -i "$BACKUP_DIR/backend.$backup_version.tar"
    fi

    if [ -f "$BACKUP_DIR/frontend.$backup_version.tar" ]; then
        docker load -i "$BACKUP_DIR/frontend.$backup_version.tar"
    fi

    # Restart services
    docker-compose -f "$COMPOSE_FILE" up -d

    log_success "Rollback completed"
}

show_status() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}           Deployment Status${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo ""

    docker-compose -f "$COMPOSE_FILE" ps

    echo ""
    echo -e "${GREEN}Services accessible at:${NC}"
    echo "  • Frontend: https://your-domain.com"
    echo "  • Backend API: https://your-domain.com/api"
    echo "  • Health Check: https://your-domain.com/health"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  • Monitor logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "  • Check metrics: http://localhost:9090 (Prometheus)"
    echo "  • View dashboards: http://localhost:3001 (Grafana)"
    echo ""
}

# ============================================================================
# Main execution
# ============================================================================

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}     Dividend API - Production Deployment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# Handle rollback
if [ "$ROLLBACK" = true ]; then
    rollback_deployment
    exit 0
fi

# Run deployment steps
check_requirements
pre_deployment_checks
backup_current_deployment
build_images

if [ "$BUILD_ONLY" = true ]; then
    log_success "Build completed (deployment skipped)"
    exit 0
fi

deploy
post_deployment_checks
show_status

log_success "Production deployment completed successfully!"
echo ""
