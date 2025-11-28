#!/bin/bash

# Pre-Deployment Validation Script
# Ensures everything works before attempting deployment

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$PROJECT_ROOT/.env"
ERRORS=0
WARNINGS=0

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; ((WARNINGS++)); }
log_error() { echo -e "${RED}[FAIL]${NC} $1"; ((ERRORS++)); }

# Header
echo "Enhanced Network Platform - Pre-Deployment Validation"
echo "======================================================"
echo

# 1. Environment Validation
check_environment() {
    log_info "Checking environment configuration..."
    
    # Check .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error ".env file not found. Copy .env.template and configure it."
        return 1
    fi
    
    # Load environment variables
    set -a
    source "$ENV_FILE"
    set +a
    
    # Check required variables
    local required_vars=("API_HOST" "API_PORT" "LLM_BASE_URL")
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "Required environment variable $var is not set"
        else
            log_success "$var is configured"
        fi
    done
    
    # Check optional but recommended variables
    local optional_vars=("FORTIGATE_HOSTS" "MERAKI_API_KEY")
    for var in "${optional_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_warning "Optional variable $var is not set (may limit functionality)"
        else
            log_success "$var is configured"
        fi
    done
    
    echo
}

# 2. Python Environment Check
check_python_env() {
    log_info "Checking Python environment..."
    
    # Check if we're in a virtual environment
    if [[ "$VIRTUAL_ENV" == "" ]]; then
        log_warning "Not in a virtual environment. Consider using venv."
    else
        log_success "Virtual environment active: $VIRTUAL_ENV"
    fi
    
    # Check Python version
    local python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    local python_major=$(echo $python_version | cut -d'.' -f1)
    local python_minor=$(echo $python_version | cut -d'.' -f2)
    
    if [ "$python_major" -eq "3" ] && [ "$python_minor" -ge "8" ]; then
        log_success "Python version: $python_version"
    else
        log_error "Python 3.8+ required, found: $python_version"
    fi
    
    # Check critical dependencies
    local critical_deps=("fastapi" "httpx" "pydantic")
    for dep in "${critical_deps[@]}"; do
        if python3 -c "import $dep" 2>/dev/null; then
            log_success "$dep is installed"
        else
            log_error "$dep is not installed"
        fi
    done
    
    # Check optional dependencies
    local optional_deps=("python-dotenv" "mcp" "three")
    for dep in "${optional_deps[@]}"; do
        if python3 -c "import $dep" 2>/dev/null; then
            log_success "$dep is installed"
        else
            log_warning "$dep is not installed (optional features may be limited)"
        fi
    done
    
    echo
}

# 3. Code Quality Checks
check_code_quality() {
    log_info "Checking code quality..."
    
    cd "$PROJECT_ROOT"
    
    # Check for syntax errors
    if python3 -m py_compile src/enhanced_network_api/platform_web_api_fastapi.py; then
        log_success "Main application compiles"
    else
        log_error "Main application has syntax errors"
    fi
    
    # Check API endpoints
    local api_files=(
        "src/enhanced_network_api/api/endpoints/fortinet_llm.py"
        "src/enhanced_network_api/api/endpoints/meraki_mcp.py"
        "src/enhanced_network_api/api/endpoints/smart_analysis.py"
    )
    
    for file in "${api_files[@]}"; do
        if [ -f "$file" ]; then
            if python3 -m py_compile "$file"; then
                log_success "$(basename $file) compiles"
            else
                log_error "$(basename $file) has syntax errors"
            fi
        fi
    done
    
    # Check shared modules
    local shared_files=(
        "src/enhanced_network_api/shared/config_manager.py"
        "src/enhanced_network_api/shared/mcp_base.py"
    )
    
    for file in "${shared_files[@]}"; do
        if [ -f "$file" ]; then
            if python3 -m py_compile "$file"; then
                log_success "$(basename $file) compiles"
            else
                log_error "$(basename $file) has syntax errors"
            fi
        fi
    done
    
    echo
}

# 4. Configuration Validation
check_configuration() {
    log_info "Checking configuration consistency..."
    
    cd "$PROJECT_ROOT"
    
    # Test configuration loading
    if python3 -c "
import sys
sys.path.append('src')
try:
    from enhanced_network_api.shared.config_manager import config_manager
    configs = config_manager.get_all_config()
    print('Configuration loaded successfully')
except Exception as e:
    print(f'Configuration error: {e}')
    sys.exit(1)
" 2>/dev/null; then
        log_success "Configuration manager loads correctly"
    else
        log_error "Configuration manager failed to load"
    fi
    
    # Check API configuration
    if [ -n "$API_PORT" ]; then
        if netstat -tuln 2>/dev/null | grep -q ":$API_PORT "; then
            log_warning "Port $API_PORT is already in use"
        else
            log_success "Port $API_PORT is available"
        fi
    fi
    
    echo
}

# 5. External Connectivity Tests
check_external_connectivity() {
    log_info "Checking external connectivity..."
    
    cd "$PROJECT_ROOT"
    
    # Test LLM connectivity
    if [ -n "$LLM_BASE_URL" ]; then
        if curl -s --connect-timeout 5 "$LLM_BASE_URL" > /dev/null 2>&1; then
            log_success "LLM server is reachable at $LLM_BASE_URL"
        else
            log_warning "LLM server at $LLM_BASE_URL is not reachable"
        fi
    fi
    
    # Test FortiGate connectivity (if tokens configured)
    if [ -n "$FORTIGATE_HOSTS" ]; then
        IFS=',' read -ra HOSTS <<< "$FORTIGATE_HOSTS"
        for host in "${HOSTS[@]}"; do
            host=$(echo $host | xargs)  # trim whitespace
            if timeout 5 bash -c "</dev/tcp/$host/10443" 2>/dev/null; then
                log_success "FortiGate $host:10443 is reachable"
            else
                log_warning "FortiGate $host:10443 is not reachable"
            fi
        done
    fi
    
    # Test Meraki connectivity (if API key configured)
    if [ -n "$MERAKI_API_KEY" ]; then
        if curl -s --connect-timeout 5 "https://api.meraki.com" > /dev/null 2>&1; then
            log_success "Meraki API is reachable"
        else
            log_warning "Meraki API is not reachable"
        fi
    fi
    
    echo
}

# 6. Application Startup Test
check_application_startup() {
    log_info "Testing application startup..."
    
    cd "$PROJECT_ROOT"
    
    # Create a temporary test instance
    local test_port=54321  # Use a different port for testing
    local temp_env_file=$(mktemp)
    
    # Create test environment
    cat > "$temp_env_file" << EOF
API_HOST=127.0.0.1
API_PORT=$test_port
API_DEBUG=false
LLM_BASE_URL=$LLM_BASE_URL
EOF
    
    # Start application in background
    python3 src/enhanced_network_api/platform_web_api_fastapi.py &
    local app_pid=$!
    
    # Wait for startup
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "http://127.0.0.1:$test_port/health" > /dev/null 2>&1; then
            log_success "Application starts successfully"
            kill $app_pid 2>/dev/null || true
            wait $app_pid 2>/dev/null || true
            rm -f "$temp_env_file"
            return 0
        fi
        
        if [ $attempt -eq $max_attempts ]; then
            log_error "Application failed to start within expected time"
            kill $app_pid 2>/dev/null || true
            wait $app_pid 2>/dev/null || true
            rm -f "$temp_env_file"
            return 1
        fi
        
        sleep 1
        ((attempt++))
    done
    
    rm -f "$temp_env_file"
    echo
}

# 7. API Endpoint Tests
check_api_endpoints() {
    log_info "Testing critical API endpoints..."
    
    cd "$PROJECT_ROOT"
    
    # Start application for testing
    python3 src/enhanced_network_api/platform_web_api_fastapi.py &
    local app_pid=$!
    
    # Wait for startup
    sleep 10
    
    # Test health endpoint
    if curl -f -s "http://127.0.0.1:11111/health" > /dev/null; then
        log_success "Health endpoint responds"
    else
        log_error "Health endpoint failed"
    fi
    
    # Test topology endpoint
    if curl -f -s "http://127.0.0.1:11111/api/topology/scene" > /dev/null; then
        log_success "Topology endpoint responds"
    else
        log_warning "Topology endpoint failed (may be configuration issue)"
    fi
    
    # Test static files
    if curl -f -s "http://127.0.0.1:11111/" > /dev/null; then
        log_success "Static files serve correctly"
    else
        log_warning "Static files failed to serve"
    fi
    
    # Cleanup
    kill $app_pid 2>/dev/null || true
    wait $app_pid 2>/dev/null || true
    echo
}

# 8. File System Checks
check_file_system() {
    log_info "Checking file system..."
    
    cd "$PROJECT_ROOT"
    
    # Check required directories
    local required_dirs=("src/enhanced_network_api" "src/enhanced_network_api/static" "src/enhanced_network_api/api")
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            log_success "Directory exists: $dir"
        else
            log_error "Missing directory: $dir"
        fi
    done
    
    # Check required files
    local required_files=(
        "src/enhanced_network_api/platform_web_api_fastapi.py"
        "src/enhanced_network_api/shared/config_manager.py"
        "src/enhanced_network_api/shared/mcp_base.py"
        "src/enhanced_network_api/static/visualization.html"
        "src/enhanced_network_api/static/smart-tools.html"
    )
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            log_success "File exists: $(basename $file)"
        else
            log_error "Missing file: $file"
        fi
    done
    
    # Check static assets
    if [ -d "src/enhanced_network_api/static/fortinet-icons" ]; then
        local icon_count=$(find src/enhanced_network_api/static/fortinet-icons -name "*.svg" | wc -l)
        if [ "$icon_count" -gt "0" ]; then
            log_success "Found $icon_count SVG icons"
        else
            log_warning "No SVG icons found in fortinet-icons directory"
        fi
    else
        log_warning "Fortinet icons directory not found"
    fi
    
    echo
}

# 9. Configuration Drift Detection
check_configuration_drift() {
    log_info "Checking for configuration drift..."
    
    cd "$PROJECT_ROOT"
    
    # Check if .env differs from template
    if [ -f ".env.template" ]; then
        local template_vars=$(grep -v '^#' .env.template | grep '=' | cut -d'=' -f1 | sort)
        local env_vars=$(grep -v '^#' .env | grep '=' | cut -d'=' -f1 | sort)
        
        # Check for missing variables
        for var in $template_vars; do
            if ! grep -q "^$var=" .env; then
                log_warning "Template variable $var not set in .env"
            fi
        done
        
        # Check for extra variables
        for var in $env_vars; do
            if ! grep -q "^$var=" .env.template; then
                log_info "Custom variable $var in .env"
            fi
        done
        
        log_success "Configuration drift check completed"
    else
        log_warning ".env.template not found for drift comparison"
    fi
    
    echo
}

# 10. Generate Validation Report
generate_report() {
    echo "Validation Summary"
    echo "=================="
    
    if [ $ERRORS -eq 0 ]; then
        echo -e "${GREEN}✅ All critical checks passed${NC}"
        if [ $WARNINGS -eq 0 ]; then
            echo -e "${GREEN}✅ No warnings detected${NC}"
            echo -e "${GREEN}🚀 Ready for deployment!${NC}"
        else
            echo -e "${YELLOW}⚠️  $WARNINGS warnings detected (review recommended)${NC}"
            echo -e "${YELLOW}🚀 Ready for deployment with warnings${NC}"
        fi
    else
        echo -e "${RED}❌ $ERRORS errors detected${NC}"
        if [ $WARNINGS -gt 0 ]; then
            echo -e "${YELLOW}⚠️  $WARNINGS warnings also detected${NC}"
        fi
        echo -e "${RED}🛑 Fix errors before deployment${NC}"
    fi
    
    echo
    echo "Recommendations:"
    if [ $ERRORS -gt 0 ]; then
        echo "1. Fix all critical errors before proceeding"
        echo "2. Run this script again after fixes"
    fi
    if [ $WARNINGS -gt 0 ]; then
        echo "3. Review warnings and address if needed"
        echo "4. Consider setting up missing optional components"
    fi
    if [ $ERRORS -eq 0 ]; then
        echo "5. Run: ./scripts/deploy.sh deploy"
        echo "6. Monitor deployment logs for any issues"
    fi
    
    echo
    return $ERRORS
}

# Main execution
main() {
    # Save current directory
    local original_dir=$(pwd)
    
    # Run all checks
    check_environment
    check_python_env
    check_code_quality
    check_configuration
    check_external_connectivity
    check_application_startup
    check_api_endpoints
    check_file_system
    check_configuration_drift
    
    # Generate report
    generate_report
    local exit_code=$?
    
    # Restore directory
    cd "$original_dir"
    
    exit $exit_code
}

# Run main function
main "$@"
