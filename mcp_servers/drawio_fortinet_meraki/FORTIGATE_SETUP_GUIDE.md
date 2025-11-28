# FortiGate + CodeLlama MCP Setup Guide

## 🎯 Your Current Setup

✅ **FortiGate**: 192.168.0.254 (configured)  
✅ **CodeLlama Model**: `/home/keith/chat-copilot/fortinet-meraki-llm/models/codellama-7b_fortinet_meraki_cpu_20251106_062854`  
✅ **MCP Server**: Built and tested  
✅ **DrawIO Integration**: Working with demo data  

## 🚀 Quick Start - Get Real FortiGate Data

### 1. Configure FortiGate Password

Edit your `.env` file:

```bash
# Set your actual FortiGate password
FORTIMANAGER_PASSWORD=your_actual_fortigate_password
```

### 2. Test Real Connection

```bash
cd /home/keith/enhanced-network-api-corporate/mcp_servers/drawio_fortinet_meraki
python test_fortigate_mcp.py
```

### 3. Generate Real Diagrams

```bash
python -c "
import asyncio
from mcp_server import DrawIOMCPServer

async def main():
    server = DrawIOMCPServer()
    await server.initialize_topology_collector()
    
    # Collect real topology
    result = await server.collect_topology({'refresh': True})
    print('Topology collected!')
    
    # Generate diagram
    diagram = await server.generate_drawio_diagram({
        'layout': 'hierarchical',
        'group_by': 'type'
    })
    
    # Save diagram
    with open('my_fortigate_topology.drawio', 'w') as f:
        f.write(diagram.content[2].text)
    print('Diagram saved: my_fortigate_topology.drawio')

asyncio.run(main())
"
```

## 🎨 Natural Language Commands

Once configured, you can use natural language:

```
User: "Show my FortiGate with all interfaces and VIPs"
AI: [Executes collect_topology → generate_drawio_diagram]

User: "Create a circular layout of my network"
AI: [Generates circular diagram]

User: "Export configuration as JSON"
AI: [Exports topology data]
```

## 🔗 Integration Options

### Option 1: Claude Desktop (Recommended)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "fortigate-drawio": {
      "command": "python",
      "args": ["/home/keith/enhanced-network-api-corporate/mcp_servers/drawio_fortinet_meraki/mcp_server.py"],
      "cwd": "/home/keith/enhanced-network-api-corporate/mcp_servers/drawio_fortinet_meraki",
      "env": {
        "PYTHONPATH": "."
      }
    }
  }
}
```

### Option 2: Windsurf Integration

Add to your Windsurf MCP configuration:

```json
{
  "mcpServers": {
    "fortigate-drawio": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/home/keith/enhanced-network-api-corporate/mcp_servers/drawio_fortinet_meraki"
    }
  }
}
```

### Option 3: Direct Python Integration

```python
from fortigate_collector import FortiGateTopologyCollector

# Use in your scripts
collector = FortiGateTopologyCollector(
    host="192.168.0.254",
    username="admin", 
    password="your_password"
)

topology = await collector.collect_topology()
```

## 🔧 FortiGate API Requirements

Your FortiGate needs:

1. **API Access Enabled**:
   ```bash
   config system global
       set rest-api-request-timeout 60
       set restapi-oauth2-enable enable
   end
   ```

2. **Admin User with API Permissions**:
   ```bash
   config system admin
       edit admin
           set remote-auth enable
           set accprofile "super_admin"
           set password your_password
       next
   end
   ```

3. **HTTPS Access** (port 443)

## 🤖 CodeLlama Integration (Future)

Your CodeLlama model is detected and ready for future enhancement:

```python
# Future: CodeLlama integration
from transformers import AutoTokenizer, AutoModelForCausalLM

model_path = "/home/keith/chat-copilot/fortinet-meraki-llm/models/codellama-7b_fortinet_meraki_cpu_20251106_062854"

# Load model for FortiGate configuration generation
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)
```

## 📊 Generated Files

Your test generated:

- ✅ `fortigate_topology_test.drawio` - Visual diagram
- ✅ `fortigate_topology_export.json` - Machine-readable data  
- ✅ Full topology with interfaces, VIPs, and metrics

## 🎯 Next Steps

1. **Configure Password**: Set your FortiGate password in `.env`
2. **Test Real API**: Verify connection to your FortiGate
3. **Open Diagram**: Load `.drawio` files in [DrawIO](https://app.diagrams.net/)
4. **MCP Client**: Connect to Claude Desktop or Windsurf
5. **3D Integration**: Use data with your Babylon.js viewer

## 🔍 Troubleshooting

### API Connection Issues

```bash
# Test direct connection
curl -k -u admin:password \
  "https://192.168.0.254/api/v2/cmdb/system/status"

# Check FortiGate API status
config system global
    show | grep rest-api
end
```

### Demo Mode Working

If you see "Source: fortigate_demo", it's working but using demo data.
Configure your password to get real data.

### DrawIO Extension

Install the DrawIO MCP extension for browser integration:
- Chrome: [DrawIO MCP Extension](https://chromewebstore.google.com/detail/drawio-mcp-extension)

## 🎉 Success Metrics

- ⚡ **Real-time Data**: Live FortiGate topology
- 🎨 **Visual Diagrams**: Professional network documentation  
- 🗣️ **Natural Language**: Describe intent, AI creates diagrams
- 🔗 **3D Ready**: Data compatible with Babylon.js viewer
- 🤖 **AI Integration**: Ready for CodeLlama enhancement

---

**Your FortiGate MCP server is ready!** Just configure the password and you'll have AI-assisted network diagram generation for your FortiGate! 🚀
