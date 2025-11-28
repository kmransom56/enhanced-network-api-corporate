#!/usr/bin/env python3
"""
Lightweight static asset bundler for the Enhanced Network API project.

Minifies core JavaScript and CSS assets using a simple whitespace/comment
stripping routine to avoid introducing a full Node.js toolchain dependency.
Generated files are written alongside the originals using `.min` suffixes.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Callable

STATIC_DIR = Path("src/enhanced_network_api/static")


def _minify_js(content: str) -> str:
    # Remove single-line comments.
    content = re.sub(r"//.*", "", content)
    # Remove multi-line comments.
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.S)
    # Collapse whitespace.
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    return " ".join(lines)


def _minify_css(content: str) -> str:
    content = re.sub(r"/\*.*?\*/", "", content, flags=re.S)
    content = re.sub(r"\s+", " ", content)
    content = re.sub(r"\s*([{};:,])\s*", r"\1", content)
    return content.strip()


def _write_minified(src: Path, target: Path, minifier: Callable[[str], str]) -> None:
    original = src.read_text(encoding="utf-8")
    minified = minifier(original)
    target.write_text(minified, encoding="utf-8")
    print(f"Minified {src.relative_to(STATIC_DIR)} -> {target.relative_to(STATIC_DIR)}")


def build() -> None:
    targets = [
        ("app.js", _minify_js, "app.min.js"),
        ("style.css", _minify_css, "style.min.css"),
    ]

    for source_name, minifier, output_name in targets:
        source_path = STATIC_DIR / source_name
        if not source_path.exists():
            print(f"Skipping {source_name}: not found.")
            continue
        output_path = STATIC_DIR / output_name
        _write_minified(source_path, output_path, minifier)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Minify core static assets.")
    parser.parse_args()
    build()
