#!/usr/bin/env python3
"""
Generate combined topology artifacts from FortiManager and Meraki API payloads.

Example usage:

    uv run python scripts/generate_topology_artifacts.py \
        --fortimanager-json ./data/fortimanager_topology.json \
        --meraki-json ./data/meraki_topology.json \
        --output-dir ./data/generated

If inputs are omitted the helper falls back to the built-in sample payloads so
the workflow remains functional without credentials.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from src.enhanced_network_api.shared import topology_workflow


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate FortiManager + Meraki topology artifacts."
    )
    parser.add_argument(
        "--fortigate-json",
        type=str,
        help="Path to FortiGate topology JSON payload.",
    )
    parser.add_argument(
        "--fortimanager-json",
        type=str,
        help="Path to FortiManager topology JSON payload.",
    )
    parser.add_argument(
        "--meraki-json",
        type=str,
        help="Path to Meraki topology JSON payload.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(topology_workflow.DEFAULT_OUTPUT_DIR),
        help=f"Directory to write artifacts (default: {topology_workflow.DEFAULT_OUTPUT_DIR})",
    )
    parser.add_argument(
        "--fortigate-host",
        type=str,
        help="FortiGate host (optionally host:port) for live collection.",
    )
    parser.add_argument(
        "--fortigate-token",
        type=str,
        help="FortiGate API token for live collection.",
    )
    parser.add_argument(
        "--fortigate-user",
        type=str,
        help="FortiGate username (if using basic authentication).",
    )
    parser.add_argument(
        "--fortigate-password",
        type=str,
        help="FortiGate password (if using basic authentication).",
    )
    parser.add_argument(
        "--fortigate-verify",
        action="store_true",
        help="Verify SSL certificates when contacting FortiGate.",
    )
    parser.add_argument(
        "--graphml-name",
        default="combined_topology.graphml",
        help="Filename for GraphML output (default: combined_topology.graphml)",
    )
    parser.add_argument(
        "--json-name",
        default="combined_topology.json",
        help="Filename for JSON output (default: combined_topology.json)",
    )
    parser.add_argument(
        "--no-samples",
        action="store_true",
        help="Fail if payloads are missing instead of using bundled samples.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    fortigate_creds = None
    if any(
        value
        for value in [
            args.fortigate_host,
            args.fortigate_token,
            args.fortigate_user,
            args.fortigate_password,
        ]
    ):
        fortigate_creds = topology_workflow.FortiGateCredentials(
            host=args.fortigate_host,
            token=args.fortigate_token,
            username=args.fortigate_user,
            password=args.fortigate_password,
            verify_ssl=args.fortigate_verify,
        )
    result = topology_workflow.generate_artifacts(
        fortigate_json=args.fortigate_json,
        fortimanager_json=args.fortimanager_json,
        meraki_json=args.meraki_json,
        fortigate_credentials=fortigate_creds,
        use_samples=not args.no_samples,
        output_dir=Path(args.output_dir),
        json_name=args.json_name,
        graphml_name=args.graphml_name,
        write_files=True,
    )

    artifacts = result.get("artifacts") or {}
    topology = result["topology"]
    summary = topology.get("metadata", {})

    if artifacts.get("json_path"):
        print(f"[+] Wrote {artifacts.get('json_path')}")
    if artifacts.get("graphml_path"):
        print(f"[+] Wrote {artifacts.get('graphml_path')}")
    if artifacts.get("drawio_path"):
        print(f"[+] Wrote {artifacts.get('drawio_path')}")
    print(
        f"[+] Topology nodes={summary.get('node_count')} links={summary.get('link_count')} "
        f"(Fortinet={summary.get('fortimanager_device_count')}, Meraki={summary.get('meraki_device_count')})"
    )


if __name__ == "__main__":
    main()
