FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    API_HOST=0.0.0.0 \
    API_PORT=11111

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY mcp_servers/ ./mcp_servers/
COPY .env.template .env.template

# Copy static assets (SVG icons, 3D models, etc.)
COPY extracted_icons/ ./extracted_icons/
COPY lab_3d_models/ ./lab_3d_models/
COPY realistic_device_svgs/ ./realistic_device_svgs/
COPY realistic_3d_models/ ./realistic_3d_models/
COPY vss_extraction/ ./vss_extraction/

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/troubleshooting_sessions

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:11111/health || exit 1

# Expose port
EXPOSE 11111

# Start the application
CMD ["python", "src/enhanced_network_api/platform_web_api_fastapi.py"]
