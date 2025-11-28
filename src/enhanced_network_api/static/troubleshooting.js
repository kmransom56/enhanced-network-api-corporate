// Troubleshooting integration module for Fortinet/Meraki networks
// Combines custom Fortinet LLM with MCP servers and visualization

class TroubleshootingEngine {
  constructor() {
    this.llmEndpoint = '/api/fortinet-llm/chat';
    this.mcpEndpoints = {
      fortinet: 'http://127.0.0.1:11110/mcp/call-tool',
      meraki: 'http://127.0.0.1:11112/mcp/call-tool'
    };
    this.activeSession = null;
    this.devices = new Map();
  }

  // Initialize troubleshooting with current topology
  async initialize(topologyData) {
    this.devices.clear();
    if (topologyData && topologyData.nodes) {
      topologyData.nodes.forEach(node => {
        this.devices.set(node.id, node);
      });
    }
    console.log(`Troubleshooting initialized with ${this.devices.size} devices`);
  }

  // Main troubleshooting orchestration
  async troubleshootDevice(deviceId, issue) {
    const device = this.devices.get(deviceId);
    if (!device) {
      throw new Error(`Device ${deviceId} not found in topology`);
    }

    const session = {
      id: this.generateSessionId(),
      deviceId,
      issue,
      startTime: new Date(),
      steps: [],
      findings: [],
      recommendations: []
    };

    this.activeSession = session;

    try {
      // Step 1: Gather device data via MCP
      await this.gatherDeviceData(device);

      // Step 2: Analyze with custom Fortinet LLM
      await this.analyzeWithLLM(device, issue);

      // Step 3: Cross-platform analysis if needed
      if (device.type === 'fortigate' && issue.includes('connectivity')) {
        await this.crossPlatformAnalysis(device);
      }

      // Step 4: Generate actionable recommendations
      await this.generateRecommendations(device, issue);

      return session;
    } catch (error) {
      session.error = error.message;
      throw error;
    }
  }

  // Step 1: Gather device data via MCP servers
  async gatherDeviceData(device) {
    this.addStep('Gathering device data via MCP');

    const mcpPromises = [];

    // Fortinet MCP data
    if (device.type.includes('forti')) {
      mcpPromises.push(
        this.callMCP('fortinet', 'get_device_status', { device_id: device.id })
          .catch(err => ({ error: err.message, source: 'fortinet-mcp' }))
      );

      mcpPromises.push(
        this.callMCP('fortinet', 'get_device_logs', { 
          device_id: device.id, 
          time_range: '1h' 
        }).catch(err => ({ error: err.message, source: 'fortinet-mcp' }))
      );
    }

    // Meraki MCP data (if relevant)
    if (device.type.includes('meraki') || this.hasMerakiIntegration()) {
      mcpPromises.push(
        this.callMCP('meraki', 'get_device_status', { serial: device.serial })
          .catch(err => ({ error: err.message, source: 'meraki-mcp' }))
      );
    }

    const results = await Promise.all(mcpPromises);
    this.activeSession.findings.push(...results.filter(r => !r.error));
    this.activeSession.errors = results.filter(r => r.error);
  }

  // Step 2: Analyze with custom Fortinet LLM
  async analyzeWithLLM(device, issue) {
    this.addStep('Analyzing with Fortinet LLM');

    const context = {
      device: {
        id: device.id,
        type: device.type,
        model: device.model,
        ip: device.ip,
        serial: device.serial
      },
      issue,
      findings: this.activeSession.findings,
      topology: Array.from(this.devices.values()).map(d => ({
        id: d.id,
        type: d.type,
        ip: d.ip,
        status: d.status
      }))
    };

    const prompt = this.buildLLMPrompt(context);

    try {
      const response = await fetch(this.llmEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt,
          context: 'fortinet_troubleshooting',
          device_type: device.type
        })
      });

      if (!response.ok) {
        throw new Error(`LLM request failed: ${response.status}`);
      }

      const llmResult = await response.json();
      this.activeSession.llmAnalysis = llmResult;
      this.activeSession.findings.push({
        type: 'llm-analysis',
        source: 'fortinet-llm',
        data: llmResult
      });

    } catch (error) {
      this.activeSession.errors.push({
        type: 'llm-error',
        source: 'fortinet-llm',
        error: error.message
      });
    }
  }

  // Step 3: Cross-platform analysis
  async crossPlatformAnalysis(device) {
    this.addStep('Cross-platform analysis');

    // Check Meraki devices that might be affected
    const merakiDevices = Array.from(this.devices.values())
      .filter(d => d.type.includes('meraki'));

    for (const merakiDevice of merakiDevices) {
      try {
        const connectivity = await this.callMCP('meraki', 'check_connectivity', {
          source_device: device.id,
          target_device: merakiDevice.serial
        });

        this.activeSession.findings.push({
          type: 'cross-platform-connectivity',
          source: 'meraki-mcp',
          data: connectivity
        });
      } catch (err) {
        // Continue with other devices
      }
    }
  }

  // Step 4: Generate recommendations
  async generateRecommendations(device, issue) {
    this.addStep('Generating recommendations');

    const recommendations = [];

    // LLM-based recommendations
    if (this.activeSession.llmAnalysis) {
      recommendations.push(...this.extractLLMRecommendations());
    }

    // Rule-based recommendations
    recommendations.push(...this.generateRuleBasedRecommendations(device, issue));

    // MCP-based recommendations
    recommendations.push(...this.generateMCPRecommendations(device));

    this.activeSession.recommendations = recommendations;
  }

  // MCP server communication
  async callMCP(platform, toolName, args) {
    const endpoint = this.mcpEndpoints[platform];
    if (!endpoint) {
      throw new Error(`MCP endpoint for ${platform} not configured`);
    }

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: toolName,
        arguments: args
      })
    });

    if (!response.ok) {
      throw new Error(`MCP call failed: ${response.status}`);
    }

    return await response.json();
  }

  // Utility methods
  buildLLMPrompt(context) {
    return `
Device: ${context.device.type} (${context.device.model})
IP: ${context.device.ip}
Issue: ${context.issue}

Findings from MCP servers:
${JSON.stringify(context.findings, null, 2)}

Network topology:
${JSON.stringify(context.topology, null, 2)}

Analyze this issue and provide:
1. Root cause analysis
2. Immediate troubleshooting steps
3. Long-term recommendations
4. Related systems that might be affected

Focus on Fortinet best practices and security implications.
    `.trim();
  }

  extractLLMRecommendations() {
    const analysis = this.activeSession.llmAnalysis;
    if (!analysis || !analysis.recommendations) return [];

    return analysis.recommendations.map(rec => ({
      type: 'llm-recommendation',
      priority: rec.priority || 'medium',
      action: rec.action,
      rationale: rec.rationale,
      automated: rec.automated || false
    }));
  }

  generateRuleBasedRecommendations(device, issue) {
    const recommendations = [];

    // Connectivity issues
    if (issue.includes('connectivity') || issue.includes('ping')) {
      recommendations.push({
        type: 'rule-based',
        priority: 'high',
        action: 'Check firewall policies and routing table',
        rationale: 'Connectivity issues often stem from misconfigured policies or routes',
        automated: false
      });
    }

    // Performance issues
    if (issue.includes('slow') || issue.includes('performance')) {
      recommendations.push({
        type: 'rule-based',
        priority: 'medium',
        action: 'Review CPU/memory utilization and traffic patterns',
        rationale: 'Performance degradation requires resource analysis',
        automated: true
      });
    }

    // Security issues
    if (issue.includes('security') || issue.includes('threat')) {
      recommendations.push({
        type: 'rule-based',
        priority: 'critical',
        action: 'Review threat logs and IPS/AV status',
        rationale: 'Security issues require immediate investigation',
        automated: true
      });
    }

    return recommendations;
  }

  generateMCPRecommendations(device) {
    const recommendations = [];

    // Based on MCP findings
    this.activeSession.findings.forEach(finding => {
      if (finding.type === 'device-status' && finding.data.status !== 'online') {
        recommendations.push({
          type: 'mcp-recommendation',
          priority: 'high',
          action: `Device ${device.id} is ${finding.data.status}. Check power and network connectivity.`,
          rationale: 'Device status indicates operational issues',
          automated: false
        });
      }

      if (finding.type === 'device-logs' && finding.data.critical_errors > 0) {
        recommendations.push({
          type: 'mcp-recommendation',
          priority: 'critical',
          action: `Found ${finding.data.critical_errors} critical errors. Review logs immediately.`,
          rationale: 'Critical errors require immediate attention',
          automated: false
        });
      }
    });

    return recommendations;
  }

  addStep(description) {
    this.activeSession.steps.push({
      description,
      timestamp: new Date(),
      status: 'completed'
    });
  }

  generateSessionId() {
    return `troubleshoot_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  hasMerakiIntegration() {
    return Array.from(this.devices.values()).some(d => d.type.includes('meraki'));
  }

  // Visualization integration
  visualizeTroubleshootingResults(session) {
    // Update 3D topology visualization with troubleshooting results
    if (window.updateTopologyWithTroubleshooting) {
      window.updateTopologyWithTroubleshooting(session);
    }

    // Highlight affected devices
    if (window.highlightDevice) {
      window.highlightDevice(session.deviceId, 'troubleshooting');
    }

    // Show troubleshooting panel
    if (window.showTroubleshootingPanel) {
      window.showTroubleshootingPanel(session);
    }
  }
}

// Global troubleshooting engine instance
window.troubleshootingEngine = new TroubleshootingEngine();

// Integration with existing topology UI
window.startTroubleshooting = async function(deviceId, issue) {
  try {
    const session = await window.troubleshootingEngine.troubleshootDevice(deviceId, issue);
    window.troubleshootingEngine.visualizeTroubleshootingResults(session);
    return session;
  } catch (error) {
    console.error('Troubleshooting failed:', error);
    alert(`Troubleshooting failed: ${error.message}`);
  }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { TroubleshootingEngine };
}
