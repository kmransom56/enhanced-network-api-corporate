#!/bin/bash

# Enhanced Network Observability Platform - Corporate Deployment Script
# This script handles deployment from development to corporate environment

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.corporate.yml"
ENV_FILE="$PROJECT_ROOT/corporate.env"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if we're in the right directory
    if [ ! -f "$COMPOSE_FILE" ]; then
        log_error "docker-compose.corporate.yml not found in project root."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

setup_environment() {
    log_info "Setting up environment..."
    
    # Check if corporate.env exists
    if [ ! -f "$ENV_FILE" ]; then
        log_warning "corporate.env not found. Creating from template..."
        if [ -f "$PROJECT_ROOT/corporate.env.template" ]; then
            cp "$PROJECT_ROOT/corporate.env.template" "$ENV_FILE"
            log_warning "Please edit $ENV_FILE with your corporate credentials before continuing."
            log_warning "Press Enter to continue or Ctrl+C to exit..."
            read -r
        else
            log_error "corporate.env.template not found. Cannot create environment file."
            exit 1
        fi
    fi
    
    # Create necessary directories
    mkdir -p "$PROJECT_ROOT/data"
    mkdir -p "$PROJECT_ROOT/logs"
    mkdir -p "$PROJECT_ROOT/troubleshooting_sessions"
    mkdir -p "$PROJECT_ROOT/backups"
    mkdir -p "$PROJECT_ROOT/nginx/ssl"
    
    log_success "Environment setup completed"
}

build_images() {
    log_info "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    # Build the main application image
    if docker build -t enhanced-network-api:latest .; then
        log_success "Docker image built successfully"
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

deploy_services() {
    log_info "Deploying services..."
    
    cd "$PROJECT_ROOT"
    
    # Use docker-compose or docker compose based on what's available
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi
    
    # Deploy services
    if $COMPOSE_CMD -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d; then
        log_success "Services deployed successfully"
    else
        log_error "Failed to deploy services"
        exit 1
    fi
}

wait_for_services() {
    log_info "Waiting for services to start..."
    
    # Wait for main API to be ready
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s http://localhost:8443/health > /dev/null 2>&1; then
            log_success "Main API is ready"
            break
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "Main API failed to start within expected time"
            exit 1
        fi
        
        log_info "Waiting for API to start... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done
    
    # Wait for database (if using PostgreSQL)
    if $COMPOSE_CMD -f "$COMPOSE_FILE" ps postgres | grep -q "Up"; then
        log_info "Waiting for database to be ready..."
        sleep 10
    fi
}

run_health_checks() {
    log_info "Running health checks..."
    
    # Check main API
    if curl -f -s http://localhost:8443/health > /dev/null; then
        log_success "Main API health check passed"
    else
        log_error "Main API health check failed"
    fi
    
    # Check database connection (if using PostgreSQL)
    if $COMPOSE_CMD -f "$COMPOSE_FILE" ps postgres | grep -q "Up"; then
        if docker exec enhanced-network-db pg_isready -U appuser > /dev/null 2>&1; then
            log_success "Database health check passed"
        else
            log_warning "Database health check failed"
        fi
    fi
    
    # Check Redis (if enabled)
    if $COMPOSE_CMD -f "$COMPOSE_FILE" ps redis | grep -q "Up"; then
        if docker exec enhanced-network-redis redis-cli ping > /dev/null 2>&1; then
            log_success "Redis health check passed"
        else
            log_warning "Redis health check failed"
        fi
    fi
}

show_access_info() {
    log_info "Deployment completed successfully!"
    echo
    echo "Access Information:"
    echo "=================="
    echo "Main Application: http://localhost:8443"
    echo "Smart Tools:      http://localhost:8443/smart-tools"
    echo "API Docs:         http://localhost:8443/docs"
    echo
    if $COMPOSE_CMD -f "$COMPOSE_FILE" ps grafana | grep -q "Up"; then
        echo "Grafana:          http://localhost:3000"
        echo "  Username: admin"
        echo "  Password: (check corporate.env)"
        echo
    fi
    echo "Service Status:"
    $COMPOSE_CMD -f "$COMPOSE_FILE" ps
    echo
    log_info "To view logs: $COMPOSE_CMD -f $COMPOSE_FILE logs -f"
    log_info "To stop services: $COMPOSE_CMD -f $COMPOSE_FILE down"
    log_info "To restart services: $COMPOSE_CMD -f $COMPOSE_FILE restart"
}

cleanup() {
    log_info "Performing cleanup..."
    
    # Remove unused Docker images
    docker image prune -f > /dev/null 2>&1
    
    log_success "Cleanup completed"
}

# Main execution
main() {
    echo "Enhanced Network Observability Platform - Corporate Deployment"
    echo "============================================================"
    echo
    
    check_prerequisites
    setup_environment
    build_images
    deploy_services
    wait_for_services
    run_health_checks
    show_access_info
    cleanup
    
    log_success "Deployment completed successfully!"
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        log_info "Stopping services..."
        cd "$PROJECT_ROOT"
        if command -v docker-compose &> /dev/null; then
            docker-compose -f "$COMPOSE_FILE" down
        else
            docker compose -f "$COMPOSE_FILE" down
        fi
        log_success "Services stopped"
        ;;
    "restart")
        log_info "Restarting services..."
        cd "$PROJECT_ROOT"
        if command -v docker-compose &> /dev/null; then
            docker-compose -f "$COMPOSE_FILE" restart
        else
            docker compose -f "$COMPOSE_FILE" restart
        fi
        log_success "Services restarted"
        ;;
    "logs")
        cd "$PROJECT_ROOT"
        if command -v docker-compose &> /dev/null; then
            docker-compose -f "$COMPOSE_FILE" logs -f "${2:-}"
        else
            docker compose -f "$COMPOSE_FILE" logs -f "${2:-}"
        fi
        ;;
    "status")
        cd "$PROJECT_ROOT"
        if command -v docker-compose &> /dev/null; then
            docker-compose -f "$COMPOSE_FILE" ps
        else
            docker compose -f "$COMPOSE_FILE" ps
        fi
        ;;
    "health")
        run_health_checks
        ;;
    "help")
        echo "Usage: $0 [COMMAND]"
        echo
        echo "Commands:"
        echo "  deploy   - Deploy the platform (default)"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  logs     - Show logs (optional service name)"
        echo "  status   - Show service status"
        echo "  health   - Run health checks"
        echo "  help     - Show this help"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for available commands"
        exit 1
        ;;
esac
