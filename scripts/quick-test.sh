#!/bin/bash

# Quick Test Script - Fast validation for development iterations
# Runs essential checks without full deployment testing

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
ERRORS=0

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[PASS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[FAIL]${NC} $1"; ((ERRORS++)); }

echo "Quick Development Test"
echo "===================="
echo

# 1. Fast syntax check
check_syntax() {
    log_info "Checking syntax..."
    
    cd "$PROJECT_ROOT"
    
    # Check main application
    if python3 -m py_compile src/enhanced_network_api/platform_web_api_fastapi.py 2>/dev/null; then
        log_success "Main application syntax OK"
    else
        log_error "Main application syntax error"
    fi
    
    # Quick check of key modules
    local modules=(
        "src/enhanced_network_api/shared/config_manager.py"
        "src/enhanced_network_api/api/endpoints/smart_analysis.py"
    )
    
    for module in "${modules[@]}"; do
        if [ -f "$module" ]; then
            if python3 -m py_compile "$module" 2>/dev/null; then
                log_success "$(basename $module) syntax OK"
            else
                log_error "$(basename $module) syntax error"
            fi
        fi
    done
    
    echo
}

# 2. Configuration quick check
check_config_quick() {
    log_info "Quick configuration check..."
    
    if [ -f "$PROJECT_ROOT/.env" ]; then
        log_success ".env file exists"
        
        # Check critical variables
        if grep -q "API_PORT=" "$PROJECT_ROOT/.env"; then
            log_success "API_PORT configured"
        else
            log_error "API_PORT not configured"
        fi
        
        if grep -q "LLM_BASE_URL=" "$PROJECT_ROOT/.env"; then
            log_success "LLM_BASE_URL configured"
        else
            log_warning "LLM_BASE_URL not configured"
        fi
    else
        log_error ".env file missing"
    fi
    
    echo
}

# 3. Import test
check_imports() {
    log_info "Testing imports..."
    
    cd "$PROJECT_ROOT"
    
    # Test critical imports
    python3 -c "
import sys
sys.path.append('src')

try:
    from enhanced_network_api.shared.config_manager import config_manager
    print('✅ Config manager imports')
except Exception as e:
    print(f'❌ Config manager import failed: {e}')

try:
    import fastapi
    print('✅ FastAPI available')
except ImportError:
    print('❌ FastAPI not available')

try:
    import httpx
    print('✅ httpx available')
except ImportError:
    print('❌ httpx not available')

try:
    import pydantic
    print('✅ Pydantic available')
except ImportError:
    print('❌ Pydantic not available')
" 2>/dev/null || log_error "Import test failed"
    
    echo
}

# 4. Port availability
check_port() {
    log_info "Checking port availability..."
    
    local api_port=11111
    if [ -f "$PROJECT_ROOT/.env" ]; then
        api_port=$(grep "API_PORT=" "$PROJECT_ROOT/.env" | cut -d'=' -f2 | tr -d ' ')
        api_port=${api_port:-11111}
    fi
    
    if netstat -tuln 2>/dev/null | grep -q ":$api_port "; then
        log_warning "Port $api_port already in use"
    else
        log_success "Port $api_port available"
    fi
    
    echo
}

# 5. Fast startup test
test_startup_fast() {
    log_info "Fast startup test..."
    
    cd "$PROJECT_ROOT"
    
    # Start application in background
    timeout 30 python3 src/enhanced_network_api/platform_web_api_fastapi.py &
    local app_pid=$!
    
    # Quick health check
    sleep 5
    
    if kill -0 $app_pid 2>/dev/null; then
        log_success "Application starts without crashing"
        
        # Test health endpoint
        if curl -f -s "http://127.0.0.1:11111/health" > /dev/null 2>&1; then
            log_success "Health endpoint responds"
        else
            log_warning "Health endpoint not responding (may need more time)"
        fi
        
        # Cleanup
        kill $app_pid 2>/dev/null || true
        wait $app_pid 2>/dev/null || true
    else
        log_error "Application failed to start"
    fi
    
    echo
}

# 6. Static files check
check_static_files() {
    log_info "Checking static files..."
    
    local static_dir="$PROJECT_ROOT/src/enhanced_network_api/static"
    
    if [ -d "$static_dir" ]; then
        log_success "Static directory exists"
        
        # Check key files
        local key_files=("visualization.html" "smart-tools.html" "app.js")
        for file in "${key_files[@]}"; do
            if [ -f "$static_dir/$file" ]; then
                log_success "$file exists"
            else
                log_warning "$file missing"
            fi
        done
        
        # Check icons
        if [ -d "$static_dir/fortinet-icons" ]; then
            local icon_count=$(find "$static_dir/fortinet-icons" -name "*.svg" 2>/dev/null | wc -l)
            if [ "$icon_count" -gt "0" ]; then
                log_success "$icon_count SVG icons found"
            else
                log_warning "No SVG icons found"
            fi
        else
            log_warning "Fortinet icons directory missing"
        fi
    else
        log_error "Static directory missing"
    fi
    
    echo
}

# 7. Generate quick summary
generate_summary() {
    echo "Quick Test Summary"
    echo "=================="
    
    if [ $ERRORS -eq 0 ]; then
        echo -e "${GREEN}✅ All critical checks passed${NC}"
        echo -e "${GREEN}🚀 Ready for development testing${NC}"
        echo
        echo "Next steps:"
        echo "1. Run full validation: ./scripts/pre-deploy-check.sh"
        echo "2. Start development: python src/enhanced_network_api/platform_web_api_fastapi.py"
        echo "3. Access: http://127.0.0.1:11111"
    else
        echo -e "${RED}❌ $ERRORS critical issues found${NC}"
        echo
        echo "Fix these issues before proceeding:"
        echo "1. Check syntax errors in code"
        echo "2. Configure .env file properly"
        echo "3. Install missing dependencies"
    fi
    
    echo
    return $ERRORS
}

# Main execution
main() {
    local original_dir=$(pwd)
    
    check_syntax
    check_config_quick
    check_imports
    check_port
    test_startup_fast
    check_static_files
    
    generate_summary
    local exit_code=$?
    
    cd "$original_dir"
    exit $exit_code
}

# Run main function
main "$@"
