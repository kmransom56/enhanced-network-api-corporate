# Docker Compose Quick Start

This guide helps you quickly start the Enhanced Network API using Docker Compose.

## Quick Start

### 1. Start All Services

```bash
./start-docker.sh
```

This script will:
- ✅ Check for required environment variables
- ✅ Prompt for passwords if not set (or use defaults)
- ✅ Start all Docker Compose services
- ✅ Display service URLs

### 2. Start with Options

```bash
# Build images before starting
./start-docker.sh --build

# Start in background (detached mode)
./start-docker.sh -d

# Build and start in background
./start-docker.sh --build -d

# Start only specific services
./start-docker.sh -s postgres,redis
```

### 3. Stop Services

```bash
# Stop services (keeps data)
./stop-docker.sh

# Stop and remove volumes (WARNING: deletes data!)
./stop-docker.sh --volumes
```

## Manual Commands

If you prefer to run Docker Compose directly:

```bash
# Set environment variables
export DB_PASSWORD=your_password
export GRAFANA_PASSWORD=your_grafana_password

# Start services
docker compose -f docker-compose.corporate.yml up --build

# Start in background
docker compose -f docker-compose.corporate.yml up -d

# Stop services
docker compose -f docker-compose.corporate.yml down
```

## Environment Variables

The script will automatically:
1. Check for `.env` file
2. Load variables from `.env` if it exists
3. Prompt for missing passwords (or use defaults)

### Required Variables

- `DB_PASSWORD` - PostgreSQL database password
- `GRAFANA_PASSWORD` - Grafana admin password

### Setting Variables

**Option 1: Create `.env` file**
```bash
echo "DB_PASSWORD=your_secure_password" >> .env
echo "GRAFANA_PASSWORD=your_grafana_password" >> .env
```

**Option 2: Export in shell**
```bash
export DB_PASSWORD=your_secure_password
export GRAFANA_PASSWORD=your_grafana_password
```

**Option 3: Use template**
```bash
cp corporate.env.template .env
# Edit .env and set your passwords
```

## Service URLs

Once started, services are available at:

- **API**: http://localhost:11111
- **Grafana**: http://localhost:11112
- **Nginx HTTP** (if configured): http://localhost:11114
- **Nginx HTTPS** (if configured): https://localhost:11113

## Viewing Logs

```bash
# All services
docker compose -f docker-compose.corporate.yml logs -f

# Specific service
docker compose -f docker-compose.corporate.yml logs -f enhanced-network-api
```

## Troubleshooting

### Port Already in Use

If you get port conflicts:
```bash
# Check what's using the port
sudo lsof -i :8443

# Or modify docker-compose.corporate.yml to use different ports
```

### Permission Denied

```bash
# Make scripts executable
chmod +x start-docker.sh stop-docker.sh
```

### Docker Not Running

```bash
# Check Docker status
docker info

# Start Docker (varies by system)
sudo systemctl start docker  # Linux
# or start Docker Desktop (Mac/Windows)
```

## Services Included

- **enhanced-network-api**: Main FastAPI application
- **postgres**: PostgreSQL database
- **redis**: Redis cache and session storage
- **nginx**: Reverse proxy (optional)
- **grafana**: Monitoring dashboards (optional)

## Production Considerations

⚠️ **Security Warnings:**

1. **Change Default Passwords**: The script uses default passwords (`changeme`, `admin`) if not set. **Always change these in production!**

2. **Use Strong Passwords**: Generate secure passwords:
   ```bash
   openssl rand -base64 32  # For DB_PASSWORD
   openssl rand -base64 32  # For GRAFANA_PASSWORD
   ```

3. **Secure .env File**: Never commit `.env` to version control:
   ```bash
   echo ".env" >> .gitignore
   ```

4. **SSL/TLS**: Configure SSL certificates for production use (see `corporate.env.template`)

## Additional Commands

```bash
# View running containers
docker compose -f docker-compose.corporate.yml ps

# Restart a specific service
docker compose -f docker-compose.corporate.yml restart enhanced-network-api

# View service status
docker compose -f docker-compose.corporate.yml ps

# Execute command in container
docker compose -f docker-compose.corporate.yml exec enhanced-network-api bash
```

