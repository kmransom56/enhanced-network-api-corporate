#!/usr/bin/env python3
"""
Generate an HTML preview wrapper for a DrawIO diagram.

Reads a .drawio XML file, encodes it for the diagrams.net viewer, and writes
a lightweight HTML page that can be opened locally. Optionally launches the
default browser after creating the preview.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from urllib.parse import quote
import webbrowser

DEFAULT_INPUT = Path("mcp_servers/drawio_fortinet_meraki/output/fortigate_live.drawio")
DEFAULT_OUTPUT = Path("mcp_servers/drawio_fortinet_meraki/output/fortigate_live_preview.html")
VIEWER_BASE_URL = "https://viewer.diagrams.net/?embed=1&ui=min&spin=1&proto=json#U"


def build_preview_html(encoded_diagram: str, title: str) -> str:
    viewer_url = VIEWER_BASE_URL + encoded_diagram
    return f"""<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>{title}</title>
    <style>
      html, body {{
        height: 100%;
        margin: 0;
        background: #111;
      }}
      iframe {{
        border: none;
        width: 100%;
        height: 100%;
      }}
    </style>
  </head>
  <body>
    <iframe src="{viewer_url}" allowfullscreen="true" title="{title}"></iframe>
  </body>
</html>
"""


def generate_preview(input_path: Path, output_path: Path, open_browser: bool) -> Path:
    if not input_path.exists():
        raise FileNotFoundError(f"Input diagram not found: {input_path}")

    diagram_xml = input_path.read_text(encoding="utf-8")
    if not diagram_xml.strip():
        raise ValueError(f"Input diagram is empty: {input_path}")

    encoded = quote(diagram_xml)
    html = build_preview_html(encoded, input_path.name)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")

    if open_browser:
        webbrowser.open(output_path.resolve().as_uri())

    return output_path


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an HTML preview for a DrawIO diagram.")
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help=f"Path to the .drawio file (default: {DEFAULT_INPUT})",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Path for the generated HTML preview (default: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the generated preview in the default web browser.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        preview_path = generate_preview(args.input, args.output, args.open)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Failed to generate preview: {exc}", file=sys.stderr)
        return 1

    print(f"Preview written to {preview_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
