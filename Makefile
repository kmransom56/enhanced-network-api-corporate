# Enhanced Network API Makefile
# Provides convenient commands for development, testing, and deployment

.PHONY: help install install-dev test test-unit test-integration test-self-healing test-smoke test-all lint format security coverage clean build docker-build docker-run health-check monitor

# Default target
help: ## Show this help message
	@echo "Enhanced Network API - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Installation
install: ## Install production dependencies
	uv pip install -r requirements.txt

install-dev: ## Install development dependencies
	uv pip install -r requirements-test.txt
	uv pip install -e .
	pre-commit install

install-test: ## Install test dependencies only
	uv pip install pytest pytest-asyncio pytest-cov pytest-html pytest-xdist pytest-retry pytest-timeout

# Testing
test: ## Run all tests
	pytest tests/ -v --cov=src/enhanced_network_api --cov-report=html --cov-report=term-missing

test-unit: ## Run unit tests only
	pytest tests/ -m "unit" -v --cov=src/enhanced_network_api --cov-report=term-missing

test-integration: ## Run integration tests
	pytest tests/ -m "integration" -v --timeout=600

test-self-healing: ## Run self-healing tests
	pytest tests/ -m "self_healing" -v --timeout=600

test-smoke: ## Run smoke tests (fast)
	pytest tests/ -m "smoke" -v --timeout=180

test-api: ## Run API tests
	pytest tests/ -m "api" -v --timeout=300

test-mcp: ## Run MCP tests
	pytest tests/ -m "mcp" -v --timeout=300

test-topology: ## Run topology tests
	pytest tests/ -m "topology" -v --timeout=300

test-performance: ## Run performance tests
	pytest tests/ -m "performance" -v --timeout=600

test-fast: ## Run fast tests only (exclude slow and performance)
	pytest tests/ -m "not slow and not performance" -v --maxfail=3

test-ci: ## Run tests for CI (parallel execution)
	pytest tests/ -v --cov=src/enhanced_network_api --cov-report=xml --cov-report=html --dist=loadscope -n auto

test-watch: ## Run tests in watch mode
	pytest-watch tests/ -v --cov=src/enhanced_network_api --cov-report=term-missing

# Code Quality
lint: ## Run linting (ruff)
	ruff check src/ tests/
	ruff format --check src/ tests/

format: ## Format code (ruff)
	ruff format src/ tests/

lint-fix: ## Fix linting issues automatically
	ruff check --fix src/ tests/
	ruff format src/ tests/

type-check: ## Run type checking (mypy)
	mypy src/enhanced_network_api/

security: ## Run security checks
	bandit -r src/enhanced_network_api/ -f json -o security-report.json
	bandit -r src/enhanced_network_api/
	safety check

# Coverage
coverage: ## Generate coverage report
	pytest tests/ --cov=src/enhanced_network_api --cov-report=html --cov-report=term-missing --cov-report=xml
	@echo "Coverage report generated in htmlcov/"

coverage-html: ## Open coverage report in browser
	pytest tests/ --cov=src/enhanced_network_api --cov-report=html
	@echo "Opening coverage report..."
	@if command -v xdg-open > /dev/null; then xdg-open htmlcov/index.html; \
	elif command -v open > /dev/null; then open htmlcov/index.html; \
	else echo "Open htmlcov/index.html in your browser"; fi

# Development
dev: ## Start development server
	python -m src.enhanced_network_api.platform_web_api_fastapi

dev-watch: ## Start development server with auto-reload
	watchmedo shell-command --patterns="*.py" --recursive --command='make dev' .

dev-mcp: ## Start MCP bridge for development
	cd /home/keith/chat-copilot/fortinet-meraki-llm/mcp-integration/fortinet-enhanced && python server_enhanced.py

dev-full: ## Start full development stack (API + MCP)
	make dev-mcp &
	sleep 2
	make dev

# Docker
docker-build: ## Build Docker image
	docker build -t enhanced-network-api .

docker-build-dev: ## Build development Docker image
	docker build -f Dockerfile.dev -t enhanced-network-api:dev .

docker-run: ## Run Docker container
	docker run -p 11111:11111 enhanced-network-api

docker-run-dev: ## Run development Docker container
	docker run -p 11111:11111 -v $(PWD):/app enhanced-network-api:dev

docker-compose-up: ## Start services with docker-compose
	docker-compose -f docker-compose.main.yml up --build

docker-compose-down: ## Stop services
	docker-compose -f docker-compose.main.yml down

docker-compose-logs: ## Show service logs
	docker-compose -f docker-compose.main.yml logs -f

# Health and Monitoring
health-check: ## Run comprehensive health check
	@echo "🔍 Running Enhanced Network API Health Check..."
	@echo ""
	@echo "📊 API Health:"
	@curl -f http://127.0.0.1:11111/health 2>/dev/null && echo "✅ API Healthy" || echo "❌ API Unhealthy"
	@echo ""
	@echo "🌐 Main Page:"
	@curl -f http://127.0.0.1:11111/ 2>/dev/null && echo "✅ Main Page Healthy" || echo "❌ Main Page Unhealthy"
	@echo ""
	@echo "🔗 Topology Endpoints:"
	@curl -f http://127.0.0.1:11111/api/topology/raw 2>/dev/null && echo "✅ Raw Topology Healthy" || echo "⚠️ Raw Topology Issues"
	@curl -f http://127.0.0.1:11111/api/topology/scene 2>/dev/null && echo "✅ 3D Scene Healthy" || echo "⚠️ 3D Scene Issues"
	@echo ""
	@echo "🔌 MCP Bridge:"
	@curl -f http://127.0.0.1:9001/mcp/call-tool -X POST -H "Content-Type: application/json" -d '{"name":"test","arguments":{}}' 2>/dev/null && echo "✅ MCP Bridge Healthy" || echo "⚠️ MCP Bridge Issues"

monitor: ## Start monitoring dashboard
	@echo "📊 Starting monitoring dashboard..."
	@echo "Open http://127.0.0.1:11111/ in your browser"
	@echo "API Docs: http://127.0.0.1:11111/docs"
	@echo ""
	@echo "Press Ctrl+C to stop monitoring"
	@while true; do make health-check; echo "---"; sleep 30; done

# Docker and Cache
clean: ## Clean up temporary files
	@echo "🧹 Cleaning up..."
	@rm -rf .pytest_cache/
	@rm -rf htmlcov/
	@rm -rf reports/
	@rm -rf dist/
	@rm -rf build/
	@rm -rf *.egg-info/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo "✅ Clean up complete"

db-reset: ## Reset database (if applicable)
	@echo "🔄 Resetting database..."
	@echo "Database reset not implemented for this application"

# Deployment
deploy-staging: ## Deploy to staging
	@echo "🚀 Deploying to staging..."
	@echo "Staging deployment not yet implemented"

deploy-production: ## Deploy to production
	@echo "🚀 Deploying to production..."
	@echo "Production deployment not yet implemented"

# Utilities
clean-docker: ## Clean up Docker resources
	@echo "🧹 Cleaning Docker resources..."
	@docker system prune -f
	@docker volume prune -f
	@echo "✅ Docker cleanup complete"

backup: ## Create backup of configuration and data
	@echo "💾 Creating backup..."
	@mkdir -p backups
	@tar -czf backups/backup-$(shell date +%Y%m%d-%H%M%S).tar.gz \
		src/ tests/ requirements*.txt pyproject.toml pytest.ini Makefile .github/ \
		--exclude-vcs --exclude='*.pyc' --exclude='__pycache__' --exclude='.pytest_cache'
	@echo "✅ Backup created in backups/"

restore: ## Restore from backup (usage: make restore BACKUP=backup-file.tar.gz)
	@if [ -z "$(BACKUP)" ]; then echo "Usage: make restore BACKUP=backup-file.tar.gz"; exit 1; fi
	@echo "🔄 Restoring from $(BACKUP)..."
	@tar -xzf backups/$(BACKUP)
	@echo "✅ Restore complete"

# Documentation
docs: ## Generate documentation
	@echo "📚 Generating documentation..."
	@mkdir -p docs
	@echo "# Enhanced Network API Documentation" > docs/README.md
	@echo "" >> docs/README.md
	@echo "## API Documentation" >> docs/README.md
	@echo "API docs available at: http://127.0.0.1:11111/docs" >> docs/README.md
	@echo "" >> docs/README.md
	@echo "## Test Coverage" >> docs/README.md
	@echo "Test coverage report available at: htmlcov/index.html" >> docs/README.md
	@echo "✅ Documentation generated"

# Performance and Load Testing
load-test: ## Run load tests
	@echo "⚡ Running load tests..."
	@if command -v locust > /dev/null; then \
		locust -f tests/performance/locustfile.py --headless --users 10 --spawn-rate 2 --run-time 30s --host http://127.0.0.1:11111; \
	else \
		echo "Locust not installed. Install with: uv pip install locust"; \
	fi

benchmark: ## Run performance benchmarks
	@echo "📈 Running benchmarks..."
	@python -c "
import time
import requests
import statistics

def benchmark_endpoint(endpoint, iterations=10):
    times = []
    for _ in range(iterations):
        start = time.time()
        try:
            response = requests.get(f'http://127.0.0.1:11111{endpoint}', timeout=10)
            if response.status_code == 200:
                times.append((time.time() - start) * 1000)
        except:
            pass
    
    if times:
        print(f'{endpoint}: {statistics.mean(times):.1f}ms avg (min: {min(times):.1f}, max: {max(times):.1f})')
    else:
        print(f'{endpoint}: Failed')

benchmark_endpoint('/')
benchmark_endpoint('/api/topology/raw')
benchmark_endpoint('/api/topology/scene')
"

# Self-Healing Tests
self-healing-test: ## Run comprehensive self-healing tests
	@echo "🚑 Running self-healing tests..."
	@make test-self-healing
	@echo ""
	@echo "🔍 Running manual healing simulation..."
	@python -c "
import time
import requests

print('Simulating service failure and recovery...')

# Test error recovery
try:
    response = requests.get('http://127.0.0.1:11111/api/invalid', timeout=5)
except:
    pass

# Test service recovery
time.sleep(2)
response = requests.get('http://127.0.0.1:11111/', timeout=5)
if response.status_code == 200:
    print('✅ Service recovered successfully')
else:
    print('❌ Service recovery failed')
"

# Quick Development Commands
quick-test: ## Run quick tests for development
	@echo "⚡ Running quick development tests..."
	@make test-smoke
	@make lint

quick-deploy: ## Quick deployment for development
	@echo "🚀 Quick development deployment..."
	@make clean
	@make install-dev
	@make test-smoke
	@make dev

# CI/CD Simulation
ci-local: ## Simulate CI/CD pipeline locally
	@echo "🔄 Simulating CI/CD pipeline..."
	@echo ""
	@echo "Step 1: Code Quality"
	@make lint || (echo "❌ Linting failed" && exit 1)
	@echo ""
	@echo "Step 2: Type Checking"
	@make type-check || (echo "❌ Type checking failed" && exit 1)
	@echo ""
	@echo "Step 3: Security Scan"
	@make security || (echo "❌ Security scan failed" && exit 1)
	@echo ""
	@echo "Step 4: Unit Tests"
	@make test-unit || (echo "❌ Unit tests failed" && exit 1)
	@echo ""
	@echo "Step 5: Integration Tests"
	@make test-integration || (echo "❌ Integration tests failed" && exit 1)
	@echo ""
	@echo "Step 6: Self-Healing Tests"
	@make test-self-healing || (echo "❌ Self-healing tests failed" && exit 1)
	@echo ""
	@echo "Step 7: Smoke Tests"
	@make test-smoke || (echo "❌ Smoke tests failed" && exit 1)
	@echo ""
	@echo "✅ CI/CD pipeline simulation completed successfully!"

# Environment Setup
setup-dev: ## Set up complete development environment
	@echo "🔧 Setting up development environment..."
	@make install-dev
	@pre-commit install
	@echo ""
	@echo "✅ Development environment ready!"
	@echo ""
	@echo "Next steps:"
	@echo "1. Run 'make dev' to start the development server"
	@echo "2. Run 'make test' to run all tests"
	@echo "3. Run 'make health-check' to verify system health"

setup-ci: ## Set up CI/CD environment
	@echo "🔧 Setting up CI/CD environment..."
	@make install-test
	@echo "✅ CI/CD environment ready!"
