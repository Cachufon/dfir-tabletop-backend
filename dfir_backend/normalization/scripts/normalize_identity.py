"""Stub normalization script for identity events.

This script outlines the interface for converting raw identity telemetry
into the normalized schema defined in `normalized_data_contract.md`.
"""

import argparse
import json
import os
from pathlib import Path
from typing import List


SUPPORTED_EXTENSIONS = {".json", ".csv"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Normalize identity events into the standard contract.")
    parser.add_argument("--input_dir", required=True, help="Directory containing raw identity inputs.")
    parser.add_argument("--output_file", required=True, help="Path to write normalized identity output (JSON).")
    parser.add_argument("--source", required=True, help="Identifier for the raw source/vendor.")
    return parser.parse_args()


def discover_input_files(input_dir: str) -> List[Path]:
    discovered: List[Path] = []
    for root, _, files in os.walk(input_dir):
        for name in files:
            path = Path(root) / name
            if path.suffix.lower() in SUPPORTED_EXTENSIONS:
                discovered.append(path)
    return discovered


def write_placeholder(output_file: str, source: str, discovered: List[Path]) -> None:
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    placeholder_record = {
        "note": "TODO: implement identity normalization pipeline",
        "source": source,
        "input_files": [str(p) for p in discovered],
    }
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump([placeholder_record], handle, indent=2)
        handle.write("\n")


def main() -> None:
    args = parse_args()
    input_files = discover_input_files(args.input_dir)

    print("[TODO] Identity normalization not yet implemented.")
    print(f"Discovered {len(input_files)} candidate files under {args.input_dir} (json/csv only).")
    for path in input_files:
        print(f" - {path}")

    write_placeholder(args.output_file, args.source, input_files)
    print(f"Placeholder output written to {args.output_file}.")


if __name__ == "__main__":
    main()
