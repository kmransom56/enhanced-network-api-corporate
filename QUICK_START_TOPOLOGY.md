# Quick Start: Network Topology Workflow

## 🚀 Fastest Way to Get Started

### 1. Set Environment Variables

```bash
export FORTIGATE_HOST=192.168.1.99
export FORTIGATE_TOKEN=your-api-token-here
```

### 2. Run the Workflow

```bash
# Option A: Python CLI
python -m src.enhanced_network_api.network_topology_workflow

# Option B: Start API and use web interface
uvicorn src.enhanced_network_api.api.main:app --reload --port 8000
# Then open: http://localhost:8000/static/babylon_lab_view.html
```

## 📊 What You Get

✅ **Automatic Discovery**: FortiGate, FortiSwitch, FortiAP, and all connected clients  
✅ **MAC Identification**: Vendor lookup and device type classification  
✅ **SVG Icons**: Color-coded icons for each device type  
✅ **3D Visualization**: Interactive Babylon.js 3D network map  
✅ **Multiple Exports**: JSON, DrawIO, Babylon.js formats  

## 🎯 Key Files

| File | Purpose |
|------|---------|
| `src/enhanced_network_api/network_topology_workflow.py` | Main workflow orchestrator |
| `src/enhanced_network_api/api/topology_workflow_api.py` | FastAPI REST endpoints |
| `src/enhanced_network_api/device_mac_matcher.py` | MAC-based device identification |
| `src/enhanced_network_api/static/babylon_lab_view.html` | 3D visualization viewer |
| `docs/NETWORK_TOPOLOGY_WORKFLOW_GUIDE.md` | Complete documentation |

## 🔌 API Endpoints

```bash
# Execute workflow
curl -X POST http://localhost:8000/api/topology/execute-workflow \
  -H "Content-Type: application/json" \
  -d '{"fortigate_host": "192.168.1.99", "fortigate_token": "token"}'

# Get Babylon.js format (for 3D viewer)
curl http://localhost:8000/api/topology/babylon-lab-format

# Get devices list
curl http://localhost:8000/api/topology/devices

# Get connections
curl http://localhost:8000/api/topology/connections
```

## 🎨 Workflow Overview

```
FortiOS API → Device Discovery → MAC Identification → SVG Generation → 3D Export
    ↓              ↓                    ↓                    ↓              ↓
FortiGate    FortiSwitch         OUI Lookup          Device Icons    Babylon.js
FortiSwitch   FortiAP            Vendor Match        Status Colors   DrawIO
FortiAP      WiFi Clients        Device Type         Icon Library    JSON
```

## 💡 Common Use Cases

### Use Case 1: Live 3D Network Map
```bash
# Start API server
uvicorn src.enhanced_network_api.api.main:app --host 0.0.0.0 --port 8000

# Open 3D viewer in browser
http://localhost:8000/static/babylon_lab_view.html
```

### Use Case 2: Automated Topology Discovery
```python
import asyncio
from src.enhanced_network_api.network_topology_workflow import NetworkTopologyWorkflow

async def discover_network():
    workflow = NetworkTopologyWorkflow(
        fortigate_host='192.168.1.99',
        fortigate_token='your-token'
    )
    result = await workflow.execute_workflow()
    print(f"Found {len(result['devices'])} devices")

asyncio.run(discover_network())
```

### Use Case 3: Export to DrawIO
```bash
# Get topology and export to DrawIO
curl http://localhost:8000/api/topology/babylon-lab-format | \
  jq '.' > network_topology.json
```

## 🔧 Configuration Options

```python
workflow = NetworkTopologyWorkflow(
    fortigate_host='192.168.1.99',           # Required
    fortigate_token='your-token',            # Required
    verify_ssl=False,                        # Optional (default: False)
    oui_database_path='/path/to/oui.csv',   # Optional
    model_library_path='/path/to/models',   # Optional
    svg_output_dir='realistic_device_svgs'  # Optional
)
```

## 🎯 Device Types Detected

**Infrastructure:**
- FortiGate (Firewall) - Red
- FortiSwitch - Green
- FortiAP - Yellow

**Restaurant Technology:**
- POS Terminal - Purple
- Kitchen Display (KDS) - Blue
- Payment Terminal - Purple
- Digital Menu Board - Cyan

**Generic:**
- Client Devices - Gray
- Servers - Dark Gray

## 📚 Full Documentation

See `docs/NETWORK_TOPOLOGY_WORKFLOW_GUIDE.md` for:
- Detailed architecture
- Step-by-step workflow explanation
- Troubleshooting guide
- Advanced usage examples
- API reference
- Integration examples

## ⚡ Performance Tips

1. **Cache Results**: Use `/api/topology/babylon-lab-format?use_cache=true`
2. **Batch Processing**: Process large networks in chunks
3. **Background Jobs**: Use async execution for long-running workflows
4. **Local OUI Database**: Use local OUI CSV for faster lookups

## 🐛 Quick Troubleshooting

| Issue | Solution |
|-------|----------|
| Authentication fails | Check API token and permissions |
| No devices found | Verify FortiSwitch/AP are managed by FortiGate |
| 3D viewer empty | Check `/api/topology/babylon-lab-format` returns data |
| SVG not generated | Ensure `realistic_device_svgs/` directory is writable |

## 📞 Need Help?

1. Check the full guide: `docs/NETWORK_TOPOLOGY_WORKFLOW_GUIDE.md`
2. Test API at: `http://localhost:8000/docs`
3. Enable debug logging: `logging.basicConfig(level=logging.DEBUG)`

---

**Ready to go? Start with the 2-step quick start above! 🚀**
