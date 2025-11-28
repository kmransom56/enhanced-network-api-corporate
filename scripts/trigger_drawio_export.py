#!/usr/bin/env python3
"""
Trigger the FastAPI DrawIO export endpoint so long-interval schedulers or CI jobs
can refresh topology diagrams without duplicating curl logic.

Examples
--------
uv run python scripts/trigger_drawio_export.py --output-dir data/generated

uv run python scripts/trigger_drawio_export.py \\
    --url http://127.0.0.1:9000/api/topology/automated/drawio \\
    --layout hierarchical --group-by vendor --filename weekly.drawio
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict

import requests

DEFAULT_URL = os.getenv(
    "DRAWIO_EXPORT_URL", "http://127.0.0.1:8000/api/topology/automated/drawio"
)


def _build_payload(args: argparse.Namespace) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "layout": args.layout,
        "group_by": args.group_by,
        "show_details": not args.no_details,
        "color_code": not args.no_color,
        "refresh_topology": not args.no_refresh,
        "write_file": not args.no_write,
    }
    if args.filename:
        payload["filename"] = args.filename
    if args.output_dir:
        payload["output_dir"] = args.output_dir
    return payload


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Invoke /api/topology/automated/drawio for scheduled exports."
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Target DrawIO export endpoint (default: {DEFAULT_URL}).",
    )
    parser.add_argument(
        "--layout",
        default="hierarchical",
        choices=["hierarchical", "circular", "force-directed", "custom"],
        help="DrawIO layout style.",
    )
    parser.add_argument(
        "--group-by",
        default="type",
        choices=["type", "site", "vendor", "none"],
        help="Grouping strategy for the generated diagram.",
    )
    parser.add_argument(
        "--filename",
        help="Optional filename when write_file is enabled (e.g., weekly.drawio).",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory for persisted artifacts when write_file is enabled.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP timeout in seconds (default: 30).",
    )
    parser.add_argument(
        "--no-refresh",
        action="store_true",
        help="Skip forcing the MCP bridge to refresh cached topology.",
    )
    parser.add_argument(
        "--no-write",
        action="store_true",
        help="Return DrawIO XML without writing a .drawio file to disk.",
    )
    parser.add_argument(
        "--no-details",
        action="store_true",
        help="Exclude detailed device labels in the diagram.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable color coding in the generated diagram.",
    )
    parser.add_argument(
        "--print-xml",
        action="store_true",
        help="Echo DrawIO XML to stdout (useful for piping into other tools).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    payload = _build_payload(args)

    try:
        response = requests.post(args.url, json=payload, timeout=args.timeout)
    except requests.RequestException as exc:
        print(f"[drawio-export] request failed: {exc}", file=sys.stderr)
        sys.exit(1)

    if response.status_code != 200:
        snippet = response.text.strip()
        snippet = snippet[:500] + ("…" if len(snippet) > 500 else "")
        print(
            f"[drawio-export] endpoint returned HTTP {response.status_code}: {snippet}",
            file=sys.stderr,
        )
        sys.exit(response.status_code if response.status_code < 256 else 1)

    try:
        data = response.json()
    except json.JSONDecodeError as exc:
        print(f"[drawio-export] invalid JSON response: {exc}", file=sys.stderr)
        sys.exit(1)

    artifacts = data.get("artifacts") or {}
    diagram_path = artifacts.get("drawio_path")

    if args.print_xml:
        print(data.get("diagram_xml", ""))
    else:
        summary_parts = [
            "DrawIO export succeeded",
            f"layout={data.get('layout')}",
            f"group_by={data.get('group_by')}",
            "write_file=" + ("yes" if payload["write_file"] else "no"),
        ]
        if diagram_path:
            summary_parts.append(f"path={diagram_path}")
        print("[drawio-export]", ", ".join(summary_parts))


if __name__ == "__main__":
    main()
