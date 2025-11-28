"""
Module for exporting 2D icons to a format compatible with Babylon.js for 3D rendering.
"""

import json
from pathlib import Path
from typing import List, Dict, Optional
import logging

log = logging.getLogger(__name__)

class BabylonExporter:
    """
    Exports 2D icons to a format compatible with Babylon.js for 3D rendering.
    """

    def __init__(self, output_dir: str = "babylon_export"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.models_dir = self.output_dir / "models"
        self.models_dir.mkdir(exist_ok=True)

    def export_to_babylon(self, icons: List[Dict]):
        """
        Exports a list of icons to a Babylon.js compatible format.
        """
        manifest = {
            "version": "1.0",
            "models": []
        }

        for icon in icons:
            model_info = self._create_model_info(icon)
            manifest["models"].append(model_info)
            self._create_obj_file(icon)

        manifest_path = self.output_dir / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2))
        log.info(f"Created manifest: {manifest_path.name}")

        self._create_babylon_loader_script(manifest_path)

    def _create_model_info(self, icon: Dict) -> Dict:
        """
        Creates the model info for the manifest.
        """
        return {
            "name": icon["device_type"],
            "svgPath": None,  # Not applicable in this simplified version
            "objPath": f"models/{icon['device_type']}.obj",
            "category": self.categorize_device(icon["device_type"]),
            "tags": self.extract_tags(icon["device_type"])
        }

    def _create_obj_file(self, icon: Dict):
        """
        Creates a placeholder OBJ file for the icon.
        """
        obj_path = self.models_dir / f"{icon['device_type']}.obj"
        obj_content = f"""# Generated from {icon['device_type']}
o {icon['device_type']}
v 0 0 0
v 1 0 0
v 1 1 0
v 0 1 0
v 0 0 0.1
v 1 0 0.1
v 1 1 0.1
v 0 1 0.1
f 1 2 3 4
f 5 8 7 6
f 1 5 6 2
f 2 6 7 3
f 3 7 8 4
f 4 8 5 1
"""
        obj_path.write_text(obj_content)

    def categorize_device(self, device_type: str) -> str:
        """
        Categorizes a device based on its type.
        """
        device_type_lower = device_type.lower()
        if "fortigate" in device_type_lower or "firewall" in device_type_lower:
            return "firewall"
        elif "switch" in device_type_lower:
            return "switch"
        elif "access point" in device_type_lower:
            return "access_point"
        return "unknown"

    def extract_tags(self, device_type: str) -> List[str]:
        """
        Extracts tags from the device type.
        """
        tags = []
        device_type_lower = device_type.lower()
        if "fortinet" in device_type_lower:
            tags.append("fortinet")
        if "meraki" in device_type_lower:
            tags.append("meraki")
        return tags

    def _create_babylon_loader_script(self, manifest_path: Path):
        """
        Creates a Babylon.js loader script.
        """
        script_content = f"""
class Icon3DLoader {{
    constructor(scene) {{
        this.scene = scene;
        this.models = new Map();
        this.loadManifest();
    }}

    async loadManifest() {{
        const response = await fetch('{manifest_path.name}');
        const manifest = await response.json();
        for (const modelInfo of manifest.models) {{
            await this.loadModel(modelInfo);
        }}
    }}

    async loadModel(modelInfo) {{
        const mesh = BABYLON.MeshBuilder.CreateBox(modelInfo.name, {{width: 1, height: 1, depth: 0.1}}, this.scene);
        mesh.metadata = {{
            name: modelInfo.name,
            category: modelInfo.category,
            tags: modelInfo.tags,
        }};
        const material = new BABYLON.StandardMaterial(`${{modelInfo.name}}_mat`, this.scene);
        material.diffuseColor = new BABYLON.Color3(0.2, 0.4, 0.8);
        mesh.material = material;
        this.models.set(modelInfo.name, mesh);
    }}
}}
"""
        script_path = self.output_dir / "babylon-icon-loader.js"
        script_path.write_text(script_content)
        log.info(f"Created Babylon.js loader: {script_path.name}")
