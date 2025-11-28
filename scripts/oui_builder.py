#!/usr/bin/env python3
"""Download and build a local IEEE OUI database for fast MAC lookups."""

import argparse
import csv
import json
from pathlib import Path
from typing import Dict

import requests

OUI_CSV_URL = "https://standards-oui.ieee.org/oui/oui.csv"


def download_oui_csv(destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(OUI_CSV_URL, timeout=60)
    response.raise_for_status()
    destination.write_bytes(response.content)


def build_lookup(csv_path: Path, json_path: Path) -> None:
    lookup: Dict[str, Dict[str, str]] = {}
    with csv_path.open('r', encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            assignment = row.get('Assignment')
            if not assignment:
                continue
            oui = assignment.replace('-', ':').upper()
            lookup[oui] = {
                'vendor': row.get('Organization Name', '').strip(),
                'address': row.get('Organization Address', '').strip(),
            }
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(lookup, indent=2), encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description="Build local OUI lookup")
    parser.add_argument('--csv', type=Path, default=Path('data/oui/oui.csv'))
    parser.add_argument('--json', type=Path, default=Path('data/oui/lookup.json'))
    args = parser.parse_args()

    download_oui_csv(args.csv)
    build_lookup(args.csv, args.json)
    print(f"Built OUI lookup with {len(json.loads(args.json.read_text()))} entries -> {args.json}")


if __name__ == '__main__':
    main()
