#!/usr/bin/env python3
"""
AI Research Platform Web API
Provides web-accessible endpoints for platform discovery and interaction
"""

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import subprocess
import json
import os
from datetime import datetime
import requests

app = Flask(__name__)
CORS(app)  # Enable CORS for all web interfaces

# Direct HTTP call to a discovered service
@app.route('/api/platform/service/<int:service_id>/call', methods=['POST'])
def call_service(service_id):
    """Call a discovered service endpoint via HTTP"""
    data = load_platform_data()
    if not data:
        return jsonify({"error": "Platform not discovered"}), 404

    services = []
    service_mapping = data.get("service_mapping", {})
    categories = data.get("categories", {})
    for category, containers in categories.items():
        for container in containers:
            port = None
            for p, info in service_mapping.items():
                if info['container'] == container:
                    port = p
                    break
            if port:
                services.append({"name": container, "port": port})

    if not (1 <= service_id <= len(services)):
        return jsonify({"error": "Invalid service ID"}), 400

    service = services[service_id - 1]
    url = f"http://localhost:{service['port']}"

    payload = request.get_json(force=True)
    method = payload.get('method', 'GET').upper()
    path = payload.get('path', '/')
    body = payload.get('body', None)
    headers = payload.get('headers', {})
    full_url = url + path if path.startswith('/') else url + '/' + path

    try:
        resp = requests.request(method, full_url, headers=headers, data=body, timeout=10)
        return jsonify({
            "status_code": resp.status_code,
            "headers": dict(resp.headers),
            "body": resp.text,
            "url": full_url
        })
    except Exception as e:
        return jsonify({"error": str(e), "url": full_url}), 500
#!/usr/bin/env python3
"""
AI Research Platform Web API
Provides web-accessible endpoints for platform discovery and interaction
"""

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import subprocess
import json
import os
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all web interfaces

DISCOVERY_DIR = "/home/keith/cagent/platform_discovery"

def run_discovery():
    """Run the platform discovery process"""
    try:
        # Run the discovery command
        result = subprocess.run(["/home/keith/cagent/ai-platform", "discover"], 
                              capture_output=True, text=True, cwd="/home/keith/cagent")
        return result.returncode == 0
    except Exception as e:
        print(f"Discovery error: {e}")
        return False

def load_platform_data():
    """Load the current platform discovery data"""
    platform_file = os.path.join(DISCOVERY_DIR, "platform_map.json")
    if not os.path.exists(platform_file):
        return None
    
    try:
        with open(platform_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading platform data: {e}")
        return None

@app.route('/api/platform/status')
def platform_status():
    """Get overall platform status"""
    data = load_platform_data()
    if not data:
        return jsonify({
            "status": "not_discovered",
            "message": "Platform not yet discovered. Run discovery first."
        })
    
    return jsonify({
        "status": "active",
        "discovery_time": data.get("discovery_time"),
        "containers": len(data.get("docker_containers", {})),
        "open_ports": len(data.get("discovered_ports", {})),
        "categories": {k: len(v) for k, v in data.get("categories", {}).items()}
    })

@app.route('/api/platform/discover', methods=['POST'])
def discover_platform():
    """Trigger platform discovery"""
    success = run_discovery()
    if success:
        data = load_platform_data()
        return jsonify({
            "status": "success",
            "message": "Platform discovery completed",
            "data": data
        })
    else:
        return jsonify({
            "status": "error", 
            "message": "Discovery failed"
        }), 500

@app.route('/api/platform/services')
def list_services():
    """Get all discovered services"""
    data = load_platform_data()
    if not data:
        return jsonify({"error": "Platform not discovered"}), 404
    
    services = []
    service_mapping = data.get("service_mapping", {})
    categories = data.get("categories", {})
    
    category_icons = {
        'ai_interfaces': '🤖',
        'databases': '🗄️', 
        'monitoring': '📊',
        'automation': '⚙️',
        'mcp_services': '🔧',
        'development': '💻'
    }
    
    service_id = 1
    for category, containers in categories.items():
        category_name = category.replace('_', ' ').title()
        icon = category_icons.get(category, '📦')
        
        for container in containers:
            # Find port for this service
            port = None
            container_info = None
            for p, info in service_mapping.items():
                if info['container'] == container:
                    port = p
                    container_info = info
                    break
            
            services.append({
                "id": service_id,
                "name": container,
                "category": category_name,
                "icon": icon,
                "port": port,
                "url": f"http://localhost:{port}" if port else None,
                "accessible": port is not None,
                "status": container_info.get('status') if container_info else 'unknown',
                "image": container_info.get('image') if container_info else 'unknown'
            })
            service_id += 1
    
    return jsonify({
        "services": services,
        "categories": list(set([s["category"] for s in services]))
    })

@app.route('/api/platform/service/<int:service_id>/open', methods=['POST'])
def open_service(service_id):
    """Get service URL for opening"""
    data = load_platform_data()
    if not data:
        return jsonify({"error": "Platform not discovered"}), 404
    
    # Rebuild service list to find the service
    services = []
    service_mapping = data.get("service_mapping", {})
    categories = data.get("categories", {})
    
    for containers in categories.values():
        for container in containers:
            port = None
            for p, info in service_mapping.items():
                if info['container'] == container:
                    port = p
                    break
            if port:
                services.append({"name": container, "port": port})
    
    if 1 <= service_id <= len(services):
        service = services[service_id - 1]
        url = f"http://localhost:{service['port']}"
        return jsonify({
            "name": service['name'],
            "url": url,
            "action": f"window.open('{url}', '_blank')"
        })
    else:
        return jsonify({"error": "Invalid service ID"}), 400

# Web UI for standalone access
@app.route('/')
def dashboard():
    """Main dashboard interface"""
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🤖 AI Research Platform Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: #333;
        }
        .dashboard {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .status-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .services-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        .service-card {
            background: white;
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .service-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .service-header {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .service-icon {
            font-size: 1.5em;
            margin-right: 10px;
        }
        .service-name {
            font-weight: bold;
            font-size: 1.1em;
        }
        .service-url {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        .btn {
            background: #4CAF50;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            font-size: 0.9em;
        }
        .btn:hover {
            background: #45a049;
        }
        .btn-discover {
            background: #2196F3;
            padding: 12px 24px;
            font-size: 1em;
            border-radius: 6px;
        }
        .btn-discover:hover {
            background: #1976D2;
        }
        .loading {
            text-align: center;
            color: #666;
            font-style: italic;
        }
        .category-section {
            margin-bottom: 25px;
        }
        .category-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #444;
            margin-bottom: 15px;
            padding-bottom: 5px;
            border-bottom: 2px solid #eee;
        }
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🤖 AI Research Platform</h1>
            <p>Universal Access Dashboard</p>
        </div>
        
        <div class="status-card">
            <div id="platform-status">
                <div class="loading">Loading platform status...</div>
            </div>
            <div style="text-align: center; margin-top: 15px;">
                <button id="discover-btn" class="btn btn-discover" onclick="discoverPlatform()">
                    🔍 Discover Platform
                </button>
            </div>
        </div>
        
        <div id="services-container">
            <!-- Services will be loaded here -->
        </div>
    </div>

    <script>
        async function loadPlatformStatus() {
            try {
                const response = await fetch('/api/platform/status');
                const data = await response.json();
                
                const statusEl = document.getElementById('platform-status');
                if (data.status === 'active') {
                    statusEl.innerHTML = `
                        <h3>🌐 Platform Status: Active</h3>
                        <p><strong>Last Discovery:</strong> ${new Date(data.discovery_time).toLocaleString()}</p>
                        <p><strong>Containers:</strong> ${data.containers} | <strong>Open Ports:</strong> ${data.open_ports}</p>
                        <div style="display: flex; gap: 15px; margin-top: 10px; flex-wrap: wrap;">
                            ${Object.entries(data.categories).map(([cat, count]) => 
                                `<span style="background: #f0f0f0; padding: 5px 10px; border-radius: 15px;">
                                    ${cat.replace('_', ' ')}: ${count}
                                </span>`
                            ).join('')}
                        </div>
                    `;
                    loadServices();
                } else {
                    statusEl.innerHTML = `
                        <h3>⚠️ Platform Status: Not Discovered</h3>
                        <p>Click "Discover Platform" to scan your AI research ecosystem.</p>
                    `;
                }
            } catch (error) {
                console.error('Error loading status:', error);
                document.getElementById('platform-status').innerHTML = 
                    '<h3>❌ Error loading platform status</h3>';
            }
        }

        async function loadServices() {
            try {
                const response = await fetch('/api/platform/services');
                const data = await response.json();
                
                const container = document.getElementById('services-container');
                
                // Group services by category
                const servicesByCategory = {};
                data.services.forEach(service => {
                    if (!servicesByCategory[service.category]) {
                        servicesByCategory[service.category] = [];
                    }
                    servicesByCategory[service.category].push(service);
                });
                
                let html = '';
                Object.entries(servicesByCategory).forEach(([category, services]) => {
                    html += `
                        <div class="category-section">
                            <div class="category-title">${services[0].icon} ${category}</div>
                            <div class="services-grid">
                    `;
                    
                    services.forEach(service => {
                        html += `
                            <div class="service-card">
                                <div class="service-header">
                                    <span class="service-icon">${service.icon}</span>
                                    <span class="service-name">${service.name}</span>
                                </div>
                                ${service.accessible ? 
                                    `<div class="service-url">${service.url}</div>
                                     <a href="${service.url}" target="_blank" class="btn">🚀 Open Service</a>` :
                                    '<div style="color: #999;">Internal service only</div>'
                                }
                            </div>
                        `;
                    });
                    
                    html += `
                            </div>
                        </div>
                    `;
                });
                
                container.innerHTML = html;
                
            } catch (error) {
                console.error('Error loading services:', error);
            }
        }

        async function discoverPlatform() {
            const btn = document.getElementById('discover-btn');
            btn.textContent = '🔄 Discovering...';
            btn.disabled = true;
            
            try {
                const response = await fetch('/api/platform/discover', { method: 'POST' });
                const data = await response.json();
                
                if (data.status === 'success') {
                    await loadPlatformStatus();
                } else {
                    alert('Discovery failed: ' + data.message);
                }
            } catch (error) {
                console.error('Discovery error:', error);
                alert('Discovery failed');
            }
            
            btn.textContent = '🔍 Discover Platform';
            btn.disabled = false;
        }

        // Load initial status
        loadPlatformStatus();
    </script>
</body>
</html>
    ''')

if __name__ == '__main__':
    # Ensure discovery directory exists
    os.makedirs(DISCOVERY_DIR, exist_ok=True)
    
    print("🚀 Starting AI Research Platform Web API...")
    print("📊 Dashboard: http://localhost:9999")
    print("🔌 API Endpoints:")
    print("  GET  /api/platform/status")
    print("  POST /api/platform/discover") 
    print("  GET  /api/platform/services")
    print("  POST /api/platform/service/<id>/open")
    
    app.run(host='0.0.0.0', port=9999, debug=True)