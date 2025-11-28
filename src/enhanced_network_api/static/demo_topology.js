// Demo topology data to show full icon system
function createDemoTopology() {
    return {
        nodes: [
            {
                id: "fg-192.168.0.254",
                type: "fortigate",
                role: "gateway",
                name: "Lab-FortiGate",
                ip: "192.168.0.254",
                model: "FGT61F",
                serial: "FGT61FTK20020975",
                status: "online",
                metadata: {
                    hostname: "fg-lab",
                    version: "v7.6.4",
                    firmware: "FG61F-7.6.4"
                }
            },
            {
                id: "fsw-FGS124EPOE",
                type: "fortiswitch",
                role: "switch",
                name: "Lab-Switch-01",
                ip: "192.168.0.100",
                model: "FGS-124E-POE",
                serial: "S124E123456789",
                status: "online",
                metadata: {
                    firmware: "v6.4.8",
                    ports: 24,
                    poe_budget: "370W",
                    vlan_count: 10
                }
            },
            {
                id: "fsw-FGS124EPOE-02",
                type: "fortiswitch",
                role: "switch",
                name: "Lab-Switch-02",
                ip: "192.168.0.101",
                model: "FGS-124E-POE",
                serial: "S124E987654321",
                status: "online",
                metadata: {
                    firmware: "v6.4.8",
                    ports: 24,
                    poe_budget: "370W",
                    vlan_count: 8
                }
            },
            {
                id: "fap-FAP231F",
                type: "fortiap",
                role: "access_point",
                name: "Lab-AP-Office",
                ip: "192.168.0.110",
                model: "FAP-231F",
                serial: "FAP231F123456789",
                status: "online",
                metadata: {
                    firmware: "v7.0.5",
                    ssid: "Lab-Network",
                    band: "WiFi 6",
                    clients: 15,
                    channel: 36
                }
            },
            {
                id: "fap-FAP231F-02",
                type: "fortiap",
                role: "access_point",
                name: "Lab-AP-Guest",
                ip: "192.168.0.111",
                model: "FAP-231F",
                serial: "FAP231F987654321",
                status: "online",
                metadata: {
                    firmware: "v7.0.5",
                    ssid: "Lab-Guest",
                    band: "WiFi 6",
                    clients: 8,
                    channel: 149
                }
            },
            {
                id: "fap-FAP221E",
                type: "fortiap",
                role: "access_point",
                name: "Lab-AP-Warehouse",
                ip: "192.168.0.112",
                model: "FAP-221E",
                serial: "FAP221E123456789",
                status: "online",
                metadata: {
                    firmware: "v7.0.5",
                    ssid: "Lab-Industrial",
                    band: "WiFi 6E",
                    clients: 3,
                    channel: 1
                }
            }
        ],
        links: [
            {
                from: "fg-192.168.0.254",
                to: "fsw-FGS124EPOE",
                type: "fortilink",
                status: "online",
                metadata: {
                    bandwidth: "1Gbps",
                    protocol: "FortiLink"
                }
            },
            {
                from: "fg-192.168.0.254",
                to: "fsw-FGS124EPOE-02",
                type: "fortilink",
                status: "online",
                metadata: {
                    bandwidth: "1Gbps",
                    protocol: "FortiLink"
                }
            },
            {
                from: "fsw-FGS124EPOE",
                to: "fap-FAP231F",
                type: "wired",
                status: "online",
                metadata: {
                    port: "1",
                    poe: true,
                    speed: "1Gbps"
                }
            },
            {
                from: "fsw-FGS124EPOE",
                to: "fap-FAP231F-02",
                type: "wired",
                status: "online",
                metadata: {
                    port: "2",
                    poe: true,
                    speed: "1Gbps"
                }
            },
            {
                from: "fsw-FGS124EPOE-02",
                to: "fap-FAP221E",
                type: "wired",
                status: "online",
                metadata: {
                    port: "24",
                    poe: true,
                    speed: "1Gbps"
                }
            }
        ],
        triageHints: []
    };
}

// Load demo topology
window.loadDemoTopology = function() {
    const demoData = createDemoTopology();
    console.log('🎭 Loading demo topology with full device support:', demoData);
    
    if (window.loadFortinetTopologyScene) {
        window.topologyData = demoData;
        window.loadFortinetTopologyScene();
    } else {
        window.topologyData = demoData;
        displayTopologyInfo(demoData);
    }
    
    updateDeviceCounts(demoData);
};
