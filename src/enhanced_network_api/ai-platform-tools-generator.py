#!/usr/bin/env python3
"""
AI Research Platform Tools Generator for cagent
Dynamically generates tool configurations from discovered services
"""

import json
import yaml
import subprocess
from typing import Dict, List, Any
from pathlib import Path


class ServiceToolGenerator:
    """Converts discovered services into cagent tool definitions"""
    
    def __init__(self, service_registry_path: str = "platform_discovery/platform_map.json"):
        self.registry_path = Path(service_registry_path)
        self.services = {}
        self.load_services()
    
    def load_services(self):
        """Load discovered services from registry"""
        if not self.registry_path.exists():
            print(f"❌ Service registry not found: {self.registry_path}")
            print("   Run service discovery first!")
            return
        
        with open(self.registry_path) as f:
            platform_map = json.load(f)
            
        self.services = platform_map.get('service_mapping', {})
        print(f"✅ Loaded {len(self.services)} services from registry")
    
    def generate_api_tools(self) -> List[Dict[str, Any]]:
        """Generate API tool configurations for each service"""
        tools = []
        
        for port, service_info in self.services.items():
            container = service_info.get('container', f'service-{port}')
            
            # Determine service type and create appropriate tool
            tool_config = self._create_api_tool_config(port, service_info)
            if tool_config:
                tools.append(tool_config)
        
        return tools
    
    def _create_api_tool_config(self, port: str, service_info: Dict) -> Dict[str, Any]:
        """Create API tool configuration for a specific service"""
        container = service_info.get('container', f'service-{port}')
        base_url = f"http://localhost:{port}"
        
        # Map known services to tool configurations
        tool_name = self._generate_tool_name(container)
        
        return {
            'type': 'api',
            'api_config': {
                'name': tool_name,
                'instruction': f"Interact with {container} service",
                'endpoint': base_url,
                'method': 'POST',
                'headers': {
                    'Content-Type': 'application/json'
                }
            }
        }
    
    def _generate_tool_name(self, container_name: str) -> str:
        """Generate clean tool name from container name"""
        # Remove common prefixes/suffixes
        name = container_name.lower()
        name = name.replace('_container', '').replace('-container', '')
        name = name.replace('_service', '').replace('-service', '')
        name = name.replace('_', '-')
        return name
    
    def generate_mcp_server_config(self) -> Dict[str, Any]:
        """Generate MCP server configuration wrapping all services"""
        mcp_config = {
            'servers': {}
        }
        
        for port, service_info in self.services.items():
            container = service_info.get('container')
            tool_name = self._generate_tool_name(container)
            
            # Only create MCP configs for services that support it
            if self._is_mcp_compatible(service_info):
                mcp_config['servers'][tool_name] = {
                    'type': 'http',
                    'url': f"http://localhost:{port}/mcp"
                }
        
        return mcp_config
    
    def _is_mcp_compatible(self, service_info: Dict) -> bool:
        """Check if service appears to be MCP-compatible"""
        container = service_info.get('container', '').lower()
        return 'mcp' in container or 'gateway' in container
    
    def generate_cagent_yaml(self, output_path: str = "ai-platform-integrated.yaml"):
        """Generate complete cagent YAML with discovered services as tools"""
        
        # Generate tool configurations
        api_tools = self.generate_api_tools()
        mcp_config = self.generate_mcp_server_config()
        
        config = {
            '#!/usr/bin/env cagent run': None,
            'models': {
                'local_primary': {
                    'provider': 'dmr',
                    'model': 'ai/qwen3:4B',
                    'max_tokens': 8192,
                    'temperature': 0.7,
                    'base_url': 'http://127.0.0.1:12434/engines/llama.cpp/v1',
                    'provider_opts': {
                        'runtime_flags': ['--ngl=33', '--ctx-size=8192']
                    }
                },
                'cloud_fallback': {
                    'provider': 'anthropic',
                    'model': 'claude-sonnet-4-0',
                    'max_tokens': 4096,
                    'temperature': 0.5
                }
            },
            'agents': {
                'platform_orchestrator': {
                    'model': 'local_primary',
                    'description': 'AI Research Platform orchestrator with access to all discovered services',
                    'instruction': self._generate_orchestrator_instruction(),
                    'toolsets': self._generate_toolsets(),
                    'add_date': True,
                    'add_environment_info': True,
                    'max_iterations': 20
                }
            }
        }
        
        # Add MCP servers if any
        if mcp_config['servers']:
            config['mcp_servers'] = mcp_config['servers']
        
        # Write YAML
        output_file = Path(output_path)
        with open(output_file, 'w') as f:
            # Write shebang comment
            f.write('#!/usr/bin/env cagent run\n')
            f.write('# AI Research Platform - Integrated Agent Configuration\n')
            f.write(f'# Auto-generated from discovered services\n')
            f.write(f'# Generated: {self._get_timestamp()}\n\n')
            
            # Write rest of config (skip shebang key)
            config_data = {k: v for k, v in config.items() if k != '#!/usr/bin/env cagent run'}
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Generated cagent configuration: {output_file}")
        print(f"   - {len(api_tools)} API tools configured")
        print(f"   - {len(mcp_config['servers'])} MCP servers configured")
        
        return output_file
    
    def _generate_orchestrator_instruction(self) -> str:
        """Generate instruction text with discovered services"""
        services_list = []
        for port, info in self.services.items():
            container = info.get('container')
            services_list.append(f"      - {container} (port {port})")
        
        services_text = '\n'.join(services_list)
        
        return f"""You are the AI Research Platform orchestrator with direct access to all platform services.

**Available Services:**
{services_text}

**Your Capabilities:**
- Query and interact with any platform service
- Coordinate multi-service workflows
- Monitor platform health and status
- Execute complex tasks across services
- Provide unified platform access

**Working Principles:**
- Use appropriate tools for each service
- Handle errors gracefully with fallbacks
- Optimize for local AI usage (cost savings)
- Maintain service health awareness
- Document significant interactions

**Common Workflows:**
1. Health checks across all services
2. Multi-service data queries
3. Workflow automation across platforms
4. Service coordination and orchestration
5. Platform monitoring and reporting
"""
    
    def _generate_toolsets(self) -> List[Dict[str, Any]]:
        """Generate toolset configuration with service tools"""
        toolsets = [
            {'type': 'filesystem'},
            {'type': 'shell'},
            {'type': 'think'},
            {'type': 'todo'},
            {'type': 'memory', 'path': './platform_orchestrator_memory.db'}
        ]
        
        # Add API tools for each service
        for port, service_info in self.services.items():
            tool_config = self._create_api_tool_config(port, service_info)
            if tool_config:
                toolsets.append(tool_config)
        
        return toolsets
    
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def generate_service_wrapper(self, output_dir: str = "service_wrappers"):
        """Generate Python wrapper classes for each service"""
        wrapper_dir = Path(output_dir)
        wrapper_dir.mkdir(exist_ok=True)
        
        for port, service_info in self.services.items():
            container = service_info.get('container')
            wrapper_path = wrapper_dir / f"{self._generate_tool_name(container)}_wrapper.py"
            
            wrapper_code = self._generate_wrapper_code(port, service_info)
            
            with open(wrapper_path, 'w') as f:
                f.write(wrapper_code)
            
            print(f"  ✅ Generated wrapper: {wrapper_path}")
    
    def _generate_wrapper_code(self, port: str, service_info: Dict) -> str:
        """Generate Python wrapper code for a service"""
        container = service_info.get('container', f'service-{port}')
        class_name = ''.join(word.capitalize() for word in container.replace('-', '_').split('_'))
        
        return f'''#!/usr/bin/env python3
"""
Auto-generated wrapper for {container}
Base URL: http://localhost:{port}
"""

import requests
from typing import Dict, Any, Optional
import json


class {class_name}Client:
    """Client for {container} service"""
    
    def __init__(self, base_url: str = "http://localhost:{port}"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Check service health"""
        try:
            response = self.session.get(f"{{self.base_url}}/health", timeout=5)
            return response.json() if response.ok else {{"error": "Service unavailable"}}
        except Exception as e:
            return {{"error": str(e)}}
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Generic GET request"""
        try:
            url = f"{{self.base_url}}{{endpoint}}"
            response = self.session.get(url, params=params, timeout=30)
            return response.json() if response.ok else {{"error": response.text}}
        except Exception as e:
            return {{"error": str(e)}}
    
    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generic POST request"""
        try:
            url = f"{{self.base_url}}{{endpoint}}"
            response = self.session.post(url, json=data, timeout=30)
            return response.json() if response.ok else {{"error": response.text}}
        except Exception as e:
            return {{"error": str(e)}}


# Example usage
if __name__ == "__main__":
    client = {class_name}Client()
    health = client.health_check()
    print(f"{container} health: {{health}}")
'''


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate cagent tools from discovered AI platform services"
    )
    parser.add_argument(
        '--registry',
        default='platform_discovery/platform_map.json',
        help='Path to service registry JSON'
    )
    parser.add_argument(
        '--output',
        default='ai-platform-integrated.yaml',
        help='Output cagent YAML configuration'
    )
    parser.add_argument(
        '--wrappers',
        action='store_true',
        help='Also generate Python service wrappers'
    )
    
    args = parser.parse_args()
    
    print("🔧 AI Research Platform Tools Generator")
    print("=" * 50)
    
    # Generate tools
    generator = ServiceToolGenerator(args.registry)
    
    if not generator.services:
        print("\n❌ No services found. Please run service discovery first:")
        print("   cagent exec ai-platform-discovery.yaml 'discover'")
        return 1
    
    # Generate cagent configuration
    output_file = generator.generate_cagent_yaml(args.output)
    
    # Generate wrappers if requested
    if args.wrappers:
        print("\n📦 Generating service wrappers...")
        generator.generate_service_wrapper()
    
    print("\n🎉 Tool generation complete!")
    print(f"\n📋 Next steps:")
    print(f"   1. Review: {output_file}")
    print(f"   2. Test: cagent run {output_file}")
    print(f"   3. Use: Your agents now have access to all platform services!")
    
    return 0


if __name__ == '__main__':
    exit(main())