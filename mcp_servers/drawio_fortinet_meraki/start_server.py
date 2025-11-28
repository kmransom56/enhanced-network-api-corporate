#!/usr/bin/env python3
"""
Startup script for DrawIO Fortinet/Meraki MCP Server
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
log_level = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=getattr(logging, log_level),
    format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)

logger = logging.getLogger(__name__)

async def main():
    """Main entry point"""
    logger.info("🚀 Starting DrawIO Fortinet/Meraki MCP Server...")
    
    try:
        # Import and run the MCP server
        from mcp_server import main as mcp_main
        
        logger.info("✅ MCP Server loaded successfully")
        
        # Check configuration
        fortimanager_host = os.getenv("FORTIMANAGER_HOST")
        meraki_api_key = os.getenv("MERAKI_API_KEY")
        
        if fortimanager_host:
            logger.info(f"🔗 FortiManager configured: {fortimanager_host}")
        else:
            logger.info("⚠️  FortiManager not configured - will use demo data")
            
        if meraki_api_key:
            logger.info("🔗 Meraki API key configured")
        else:
            logger.info("⚠️  Meraki not configured - will use demo data")
        
        # Start the MCP server
        await mcp_main()
        
    except KeyboardInterrupt:
        logger.info("👋 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
