// network_map_renderer.js

const canvas = document.getElementById('renderCanvas');
const engine = new BABYLON.Engine(canvas, true);
const scene = new BABYLON.Scene(engine);

// Camera
const camera = new BABYLON.ArcRotateCamera('camera', -Math.PI / 2, Math.PI / 2.5, 15, BABYLON.Vector3.Zero(), scene);
camera.attachControl(canvas, true);

// Light
const light = new BABYLON.HemisphericLight('light', new BABYLON.Vector3(0, 1, 0), scene);

// Ground
const ground = BABYLON.MeshBuilder.CreateGround('ground', {width: 20, height: 20}, scene);
const groundMaterial = new BABYLON.StandardMaterial('groundMat', scene);
groundMaterial.diffuseColor = new BABYLON.Color3(0.2, 0.2, 0.2);
ground.material = groundMaterial;

async function loadNetworkMap() {
    try {
        const response = await fetch('network_map.json');
        const networkMap = await response.json();
        
        const nodeMeshes = {};

        // Load nodes
        for (const node of networkMap.nodes) {
            // For now, create a simple box mesh for each icon
            // In a real implementation, you'd load the actual 3D model
            const mesh = BABYLON.MeshBuilder.CreateBox(node.id, {width: 1, height: 1, depth: 0.1}, scene);
            
            // Add metadata
            mesh.metadata = {
                id: node.id,
                label: node.label,
                type: node.type,
            };
            
            // Create a simple material
            const material = new BABYLON.StandardMaterial(`${node.id}_mat`, scene);
            material.diffuseColor = new BABYLON.Color3(Math.random(), Math.random(), Math.random());
            mesh.material = material;

            // Add a label
            const labelTexture = new BABYLON.DynamicTexture("dynamic texture", {width:512, height:256}, scene, false);
            labelTexture.drawText(node.label, 75, 135, "bold 72px Arial", "white", "transparent", true, true);
            const labelMaterial = new BABYLON.StandardMaterial("mat", scene);
            labelMaterial.diffuseTexture = labelTexture;
            const labelPlane = BABYLON.MeshBuilder.CreatePlane("labelPlane", {height:1, width: 2}, scene);
            labelPlane.material = labelMaterial;
            labelPlane.parent = mesh;
            labelPlane.position.y = -0.75;


            nodeMeshes[node.id] = mesh;
        }

        // Position nodes in a circle
        const radius = 5;
        const angleStep = (2 * Math.PI) / Object.keys(nodeMeshes).length;
        let i = 0;
        for (const nodeId in nodeMeshes) {
            const mesh = nodeMeshes[nodeId];
            mesh.position.x = radius * Math.cos(i * angleStep);
            mesh.position.z = radius * Math.sin(i * angleStep);
            mesh.position.y = 0.5;
            i++;
        }


        // Draw edges
        for (const edge of networkMap.edges) {
            const fromMesh = nodeMeshes[edge.from];
            const toMesh = nodeMeshes[edge.to];
            if (fromMesh && toMesh) {
                const line = BABYLON.MeshBuilder.CreateLines("line", {
                    points: [fromMesh.position, toMesh.position],
                    updatable: true
                }, scene);
                line.color = new BABYLON.Color3(1, 1, 1);
            }
        }

    } catch (error) {
        console.error('Failed to load network map:', error);
    }
}

loadNetworkMap();

// Run render loop
engine.runRenderLoop(() => {
    scene.render();
});

// Handle window resize
window.addEventListener('resize', () => {
    engine.resize();
});
