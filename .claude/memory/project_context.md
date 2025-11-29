# Project Context

- 2025-11-28: VSS Linux extraction script now emits realistic cuboid GLTFs sized per Fortinet device specs. Models stay under `/vss_extraction/vss_exports`, ensuring Babylon 3D lab can load solid meshes instead of zero-geometry placeholders.

- 2025-11-29: Enhanced 3D topology with:
  - **Error handling**: Comprehensive model loading error handling with timeout (10s), fallback chains, and detailed logging
  - **Optimization**: Quantized normals (signed bytes) and UVs (uint16) reduce model size by ~50%. Models now ~5-6KB vs ~10KB+ before
  - **Texture support**: Procedural device-specific textures (256x256 PNG) with patterns:
    - FortiGate: Port indicators + status LED
    - FortiSwitch: Grid pattern + port indicators  
    - FortiAP: Antenna pattern with radial lines
  - **Improved loading**: VSS models prioritized in fallback chain, better error messages, geometry validation
