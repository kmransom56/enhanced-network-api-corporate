#!/bin/bash
# Helper script to start Enhanced Network API Docker Compose services
# Sets required environment variables and starts all services

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.corporate.yml"
ENV_FILE=".env"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Enhanced Network API - Docker Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if docker-compose file exists
if [ ! -f "$COMPOSE_FILE" ]; then
    echo -e "${RED}❌ Error: $COMPOSE_FILE not found!${NC}"
    exit 1
fi

# Function to check if variable is set
check_var() {
    local var_name=$1
    local var_value=${!var_name}
    if [ -z "$var_value" ]; then
        return 1  # Not set
    else
        return 0  # Set
    fi
}

# Function to prompt for password
prompt_password() {
    local var_name=$1
    local prompt_text=$2
    local password
    
    read -sp "$prompt_text: " password
    echo ""
    export "$var_name=$password"
}

# Check for .env file
if [ -f "$ENV_FILE" ]; then
    echo -e "${GREEN}✓ Found $ENV_FILE file${NC}"
    # Parse .env file safely - only extract simple KEY=VALUE pairs
    # This avoids shell syntax errors from special characters
    while IFS= read -r line || [ -n "$line" ]; do
        # Skip empty lines and comments
        line_trimmed=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        [[ -z "$line_trimmed" || "$line_trimmed" =~ ^# ]] && continue
        
        # Only process lines that match simple KEY=VALUE pattern (no special chars in key)
        # This regex matches: KEY=VALUE where KEY is alphanumeric/underscore only
        if [[ "$line_trimmed" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
            key="${BASH_REMATCH[1]}"
            value="${BASH_REMATCH[2]}"
            # Remove leading/trailing whitespace from value
            value=$(echo "$value" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            # Remove surrounding quotes if present
            if [[ "$value" =~ ^\".*\"$ ]] || [[ "$value" =~ ^\'.*\'$ ]]; then
                value="${value:1:-1}"
            fi
            # Export the variable (only if key is valid)
            if [ -n "$key" ]; then
                export "$key=$value"
            fi
        fi
    done < "$ENV_FILE"
else
    echo -e "${YELLOW}⚠️  $ENV_FILE file not found${NC}"
    echo -e "${YELLOW}   Creating one from template...${NC}"
    
    # Check if template exists
    if [ -f "corporate.env.template" ]; then
        cp corporate.env.template "$ENV_FILE"
        echo -e "${GREEN}✓ Created $ENV_FILE from template${NC}"
        echo -e "${YELLOW}   Please edit $ENV_FILE and set your passwords, then run this script again${NC}"
        exit 0
    fi
fi

# Check and set DB_PASSWORD
if ! check_var "DB_PASSWORD"; then
    echo -e "${YELLOW}⚠️  DB_PASSWORD not set${NC}"
    if [ -t 0 ]; then  # Check if running interactively
        prompt_password "DB_PASSWORD" "Enter PostgreSQL password (or press Enter for default: 'changeme')"
        if [ -z "$DB_PASSWORD" ]; then
            export DB_PASSWORD="changeme"
            echo -e "${YELLOW}   Using default password: changeme${NC}"
            echo -e "${YELLOW}   ⚠️  WARNING: Change this in production!${NC}"
        fi
    else
        # Non-interactive mode - use default
        export DB_PASSWORD="changeme"
        echo -e "${YELLOW}   Using default password: changeme (non-interactive mode)${NC}"
    fi
else
    echo -e "${GREEN}✓ DB_PASSWORD is set${NC}"
fi

# Check and set GRAFANA_PASSWORD
if ! check_var "GRAFANA_PASSWORD"; then
    echo -e "${YELLOW}⚠️  GRAFANA_PASSWORD not set${NC}"
    if [ -t 0 ]; then  # Check if running interactively
        prompt_password "GRAFANA_PASSWORD" "Enter Grafana admin password (or press Enter for default: 'admin')"
        if [ -z "$GRAFANA_PASSWORD" ]; then
            export GRAFANA_PASSWORD="admin"
            echo -e "${YELLOW}   Using default password: admin${NC}"
            echo -e "${YELLOW}   ⚠️  WARNING: Change this in production!${NC}"
        fi
    else
        # Non-interactive mode - use default
        export GRAFANA_PASSWORD="admin"
        echo -e "${YELLOW}   Using default password: admin (non-interactive mode)${NC}"
    fi
else
    echo -e "${GREEN}✓ GRAFANA_PASSWORD is set${NC}"
fi

# Save passwords to .env file if they were just set
if [ -f "$ENV_FILE" ]; then
    # Update .env file with passwords if not already there
    if ! grep -q "^DB_PASSWORD=" "$ENV_FILE" 2>/dev/null; then
        echo "DB_PASSWORD=$DB_PASSWORD" >> "$ENV_FILE"
    fi
    if ! grep -q "^GRAFANA_PASSWORD=" "$ENV_FILE" 2>/dev/null; then
        echo "GRAFANA_PASSWORD=$GRAFANA_PASSWORD" >> "$ENV_FILE"
    fi
fi

echo ""
echo -e "${BLUE}Starting Docker Compose services...${NC}"
echo ""

# Parse command line arguments
BUILD=false
DETACHED=false
SERVICES=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --build|-b)
            BUILD=true
            shift
            ;;
        --detached|-d)
            DETACHED=true
            shift
            ;;
        --services|-s)
            SERVICES="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -b, --build       Build images before starting"
            echo "  -d, --detached    Run in detached mode (background)"
            echo "  -s, --services    Start only specific services (comma-separated)"
            echo "  -h, --help        Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                    # Start all services"
            echo "  $0 --build           # Build and start all services"
            echo "  $0 -d                 # Start in background"
            echo "  $0 -s postgres,redis  # Start only postgres and redis"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build docker compose command
COMPOSE_CMD="docker compose -f $COMPOSE_FILE"

if [ "$BUILD" = true ]; then
    COMPOSE_CMD="$COMPOSE_CMD up --build"
else
    COMPOSE_CMD="$COMPOSE_CMD up"
fi

if [ "$DETACHED" = true ]; then
    COMPOSE_CMD="$COMPOSE_CMD -d"
fi

if [ -n "$SERVICES" ]; then
    # Convert comma-separated to space-separated
    SERVICES=$(echo "$SERVICES" | tr ',' ' ')
    COMPOSE_CMD="$COMPOSE_CMD $SERVICES"
fi

# Display what will be started
echo -e "${BLUE}Command:${NC} $COMPOSE_CMD"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Error: Docker is not running!${NC}"
    echo "   Please start Docker and try again."
    exit 1
fi

# Check if docker compose is available
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not installed!${NC}"
    exit 1
fi

# Execute docker compose command
echo -e "${GREEN}Starting services...${NC}"
echo ""

eval $COMPOSE_CMD

# Show status if running in detached mode
if [ "$DETACHED" = true ]; then
    echo ""
    echo -e "${GREEN}✓ Services started in background${NC}"
    echo ""
    echo -e "${BLUE}Service URLs:${NC}"
    echo -e "  API:        ${GREEN}http://localhost:8443${NC}"
    echo -e "  Grafana:    ${GREEN}http://localhost:3000${NC}"
    echo -e "  Nginx:      ${GREEN}http://localhost:80${NC} (if configured)"
    echo ""
    echo "To view logs:"
    echo "  docker compose -f $COMPOSE_FILE logs -f"
    echo ""
    echo "To stop services:"
    echo "  docker compose -f $COMPOSE_FILE down"
else
    echo ""
    echo -e "${GREEN}✓ Services are running${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
fi

