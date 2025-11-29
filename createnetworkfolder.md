Here is the script:
bash
#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Base directory for the project (optional, remove if you want to create in current dir)
PROJECT_ROOT="./network_mapper"
mkdir -p "$PROJECT_ROOT"
cd "$PROJECT_ROOT" || exit

# Create all necessary directories first using the -p option
mkdir -p inventory/ classifier/ layout/ export/ viewer/assets/icons/ viewer/assets/models/ viewer/assets/stencils/ tools/

# Create all necessary empty files
touch fortinet_agent.py meraki_agent.py classifier/device_matcher.py classifier/device_model_rules.json layout/layout_strategy.py export/export_manifest.py export/export_gltf.py viewer/index.html tools/vss_to_svg.py tools/svg_to_glb.py main.py

echo "Directory structure and files created successfully in $PROJECT_ROOT."
How to use the script:
Save the script: Save the code above as a file named create_structure.sh.
Make the script executable: Open your terminal and run the following command:
bash
chmod +x create_structure.sh
Run the script: Execute the script from your terminal:
bash
./create_structure.sh
 
This will create a main directory called network_mapper in your current location, and populate it with the entire specified folder and file structure.
Resulting Structure
After running the script, your directory tree will look like this (you can use the tree command in Linux to verify this): 
network_mapper/
├── classifier/
│   ├── device_matcher.py
│   └── device_model_rules.json
├── export/
│   ├── export_gltf.py
│   └── export_manifest.py
├── fortinet_agent.py
├── inventory/
├── layout/
│   └── layout_strategy.py
├── main.py
├── meraki_agent.py
├── tools/
│   ├── svg_to_glb.py
│   └── vss_to_svg.py
└── viewer/
    ├── assets/
    │   ├── icons/
    │   ├── models/
    │   └── stencils/
    └── index.html