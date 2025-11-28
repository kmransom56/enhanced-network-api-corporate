"""
Configuration Management for Enhanced Network Platform
Handles environment variables, secrets, and platform configurations
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class FortinetConfig:
    """Fortinet device configuration"""
    host: str
    token: str
    name: Optional[str] = None
    port: int = 10443
    timeout: int = 30

@dataclass
class MerakiConfig:
    """Meraki API configuration"""
    api_key: str
    organization_id: Optional[str] = None
    base_url: str = "https://api.meraki.com/api/v1"
    timeout: int = 30

@dataclass
class LLMConfig:
    """LLM configuration"""
    base_url: str
    model: str
    timeout: int = 30
    max_tokens: int = 2048
    temperature: float = 0.7

class ConfigManager:
    """
    Centralized configuration manager
    Loads from environment variables and .env files
    """
    
    def __init__(self, env_file: Optional[str] = None):
        self.env_file = env_file or ".env"
        self._load_environment()
        self._validate_config()
    
    def _load_environment(self):
        """Load environment variables from .env file"""
        # Look for .env in multiple locations
        possible_paths = [
            Path(self.env_file),  # Current directory
            Path(__file__).parent.parent.parent / self.env_file,  # Project root
            Path.cwd() / self.env_file,  # Working directory
        ]
        
        env_path = None
        for path in possible_paths:
            if path.exists():
                env_path = path
                break
        
        # Configure logging here to make sure we see the logs
        logging.basicConfig(level=logging.INFO)

        if env_path:
            try:
                from dotenv import load_dotenv
                load_dotenv(env_path)
                logger.info(f"Loaded environment from {env_path}")
            except ImportError:
                logger.warning("python-dotenv not installed, using system environment only")
            except Exception as e:
                logger.error(f"Failed to load .env file: {e}")
        else:
            logger.warning(f".env file not found in any of: {possible_paths}")
    
    def _validate_config(self):
        """Validate required configuration"""
        required_vars = []
        missing_vars = []
        
        # Check Fortinet configurations
        fortigate_hosts = self.get_fortigate_hosts()
        for host in fortigate_hosts:
            host_slug = host.replace(".", "_").replace("-", "_").replace(":", "_")
            token_var = f"FORTIGATE_{host_slug}_TOKEN"
            if not os.getenv(token_var):
                missing_vars.append(token_var)
        
        # Check Meraki configuration
        if self.has_meraki_config():
            if not os.getenv("MERAKI_API_KEY"):
                missing_vars.append("MERAKI_API_KEY")
        
        # Check LLM configuration
        if not os.getenv("LLM_BASE_URL"):
            missing_vars.append("LLM_BASE_URL")
        
        if missing_vars:
            logger.warning(f"Missing environment variables: {missing_vars}")
    
    def get_fortigate_hosts(self) -> list:
        """Get list of configured FortiGate hosts"""
        hosts = []
        
        # Look for FORTIGATE_HOSTS environment variable
        hosts_str = os.getenv("FORTIGATE_HOSTS", "")
        logger.info(f"FORTIGATE_HOSTS env var: {hosts_str}")
        if hosts_str:
            hosts.extend([host.strip() for host in hosts_str.split(",") if host.strip()])
        
        # Look for individual FORTIGATE_x_HOST variables
        for key in os.environ.keys():
            if key.startswith("FORTIGATE_") and key.endswith("_HOST") and key != "FORTIGATE_HOST":
                host = os.getenv(key)
                if host and host not in hosts:
                    hosts.append(host)
        
        # Default to the known lab device
        if not hosts:
            hosts.append("192.168.0.254")
        
        logger.info(f"Returning hosts: {hosts}")
        return hosts
    
    def get_fortigate_config(self, host: str) -> Optional[FortinetConfig]:
        """Get FortiGate configuration for a specific host"""
        # Generate variable names
        host_clean = host.replace(".", "_").replace("-", "_").replace(":", "_")
        token_var = f"FORTIGATE_{host_clean}_TOKEN"
        name_var = f"FORTIGATE_{host_clean}_NAME"
        port_var = f"FORTIGATE_{host_clean}_PORT"
        
        token = os.getenv(token_var)
        if not token:
            # Try default token
            token = os.getenv("FORTIGATE_DEFAULT_TOKEN")
        
        if not token:
            logger.error(f"No token found for FortiGate {host}")
            return None
        
        name = os.getenv(name_var) or f"FortiGate-{host}"
        port = int(os.getenv(port_var, "10443"))
        
        return FortinetConfig(
            host=host,
            token=token,
            name=name,
            port=port
        )
    
    def get_all_fortigate_configs(self) -> Dict[str, FortinetConfig]:
        """Get all configured FortiGate configurations"""
        configs = {}
        
        for host in self.get_fortigate_hosts():
            config = self.get_fortigate_config(host)
            if config:
                configs[host] = config
        
        return configs
    
    def has_meraki_config(self) -> bool:
        """Check if Meraki configuration is available"""
        return bool(os.getenv("MERAKI_API_KEY"))
    
    def get_meraki_config(self) -> Optional[MerakiConfig]:
        """Get Meraki configuration"""
        api_key = os.getenv("MERAKI_API_KEY")
        if not api_key:
            return None
        
        return MerakiConfig(
            api_key=api_key,
            organization_id=os.getenv("MERAKI_ORG_ID"),
            base_url=os.getenv("MERAKI_BASE_URL", "https://api.meraki.com/api/v1"),
            timeout=int(os.getenv("MERAKI_TIMEOUT", "30"))
        )
    
    def get_llm_config(self) -> Optional[LLMConfig]:
        """Get LLM configuration"""
        base_url = os.getenv("LLM_BASE_URL")
        if not base_url:
            return None
        
        return LLMConfig(
            base_url=base_url,
            model=os.getenv("LLM_MODEL", "fortinet-custom"),
            timeout=int(os.getenv("LLM_TIMEOUT", "30")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2048")),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7"))
        )
    
    def get_mcp_server_config(self, server_name: str) -> Dict[str, Any]:
        """Get MCP server configuration"""
        prefix = f"MCP_{server_name.upper()}_"
        
        config = {}
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                config[config_key] = value
        
        return config
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            "url": os.getenv("DATABASE_URL", "sqlite:///./enhanced_network.db"),
            "echo": os.getenv("DATABASE_ECHO", "false").lower() == "true",
            "pool_size": int(os.getenv("DATABASE_POOL_SIZE", "5")),
            "max_overflow": int(os.getenv("DATABASE_MAX_OVERFLOW", "10"))
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "format": os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            "file": os.getenv("LOG_FILE", None),
            "max_size": int(os.getenv("LOG_MAX_SIZE", "10485760")),  # 10MB
            "backup_count": int(os.getenv("LOG_BACKUP_COUNT", "5"))
        }
    
    def get_topology_config(self) -> Dict[str, Any]:
        """Get topology visualization configuration"""
        return {
            "auto_refresh": os.getenv("TOPOLOGY_AUTO_REFRESH", "false").lower() == "true",
            "refresh_interval": int(os.getenv("TOPOLOGY_REFRESH_INTERVAL", "30")),  # seconds
            "max_devices": int(os.getenv("TOPOLOGY_MAX_DEVICES", "100")),
            "icon_path": os.getenv("TOPOLOGY_ICON_PATH", "/static/fortinet-icons"),
            "default_view": os.getenv("TOPOLOGY_DEFAULT_VIEW", "3d")
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """Get API server configuration"""
        return {
            "host": os.getenv("API_HOST", "0.0.0.0"),
            "port": int(os.getenv("API_PORT", "11111")),
            "debug": os.getenv("API_DEBUG", "false").lower() == "true",
            "cors_origins": os.getenv("API_CORS_ORIGINS", "*").split(","),
            "rate_limit": int(os.getenv("API_RATE_LIMIT", "100")),  # requests per minute
            "timeout": int(os.getenv("API_TIMEOUT", "30"))
        }
    
    def get_troubleshooting_config(self) -> Dict[str, Any]:
        """Get troubleshooting configuration"""
        return {
            "max_sessions": int(os.getenv("TROUBLESHOOTING_MAX_SESSIONS", "10")),
            "session_timeout": int(os.getenv("TROUBLESHOOTING_SESSION_TIMEOUT", "3600")),  # seconds
            "auto_save": os.getenv("TROUBLESHOOTING_AUTO_SAVE", "true").lower() == "true",
            "save_path": os.getenv("TROUBLESHOOTING_SAVE_PATH", "./troubleshooting_sessions")
        }
    
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration as a dictionary"""
        return {
            "fortigate": {host: config.__dict__ for host, config in self.get_all_fortigate_configs().items()},
            "meraki": self.get_meraki_config().__dict__ if self.has_meraki_config() else None,
            "llm": self.get_llm_config().__dict__ if self.get_llm_config() else None,
            "database": self.get_database_config(),
            "logging": self.get_logging_config(),
            "topology": self.get_topology_config(),
            "api": self.get_api_config(),
            "troubleshooting": self.get_troubleshooting_config()
        }
    
    def create_env_template(self, output_path: str = ".env.template"):
        """Create a template .env file with all required variables"""
        template = """# Enhanced Network Platform Configuration

# FortiGate Devices
FORTIGATE_HOSTS=192.168.0.254
FORTIGATE_192_168_0_254_TOKEN=your_fortigate_token_here
FORTIGATE_192_168_0_254_NAME=Lab_FortiGate
FORTIGATE_192_168_0_254_PORT=10443

# Optional: Default FortiGate token (used if no specific token)
# FORTIGATE_DEFAULT_TOKEN=your_default_token

# Meraki Configuration (optional)
MERAKI_API_KEY=your_meraki_api_key
MERAKI_ORG_ID=your_organization_id
MERAKI_BASE_URL=https://api.meraki.com/api/v1
MERAKI_TIMEOUT=30

# LLM Configuration
LLM_BASE_URL=http://localhost:11434
LLM_MODEL=fortinet-custom
LLM_TIMEOUT=30
LLM_MAX_TOKENS=2048
LLM_TEMPERATURE=0.7

# Database Configuration
DATABASE_URL=sqlite:///./enhanced_network.db
DATABASE_ECHO=false
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10

# Logging Configuration
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
# LOG_FILE=/var/log/enhanced-network.log
LOG_MAX_SIZE=10485760
LOG_BACKUP_COUNT=5

# Topology Configuration
TOPOLOGY_AUTO_REFRESH=false
TOPOLOGY_REFRESH_INTERVAL=30
TOPOLOGY_MAX_DEVICES=100
TOPOLOGY_ICON_PATH=/static/fortinet-icons
TOPOLOGY_DEFAULT_VIEW=3d

# API Configuration
API_HOST=0.0.0.0
API_PORT=11111
API_DEBUG=false
API_CORS_ORIGINS=*
API_RATE_LIMIT=100
API_TIMEOUT=30

# Troubleshooting Configuration
TROUBLESHOOTING_MAX_SESSIONS=10
TROUBLESHOOTING_SESSION_TIMEOUT=3600
TROUBLESHOOTING_AUTO_SAVE=true
TROUBLESHOOTING_SAVE_PATH=./troubleshooting_sessions

# MCP Server Configuration
MCP_FORTINET_HOST=127.0.0.1
MCP_FORTINET_PORT=11110
MCP_MERAKI_HOST=127.0.0.1
MCP_MERAKI_PORT=11112
"""
        
        try:
            with open(output_path, 'w') as f:
                f.write(template)
            logger.info(f"Created .env template at {output_path}")
        except Exception as e:
            logger.error(f"Failed to create .env template: {e}")

# Global configuration instance
config_manager = ConfigManager()
