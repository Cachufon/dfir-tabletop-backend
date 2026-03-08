"""Starter script for flattening nested JSON logs.

The goal is to accept nested event payloads and emit flattened records that align
with the Phase 1 normalization schema. This file intentionally includes TODO
placeholders where parsing and output details will be implemented.
"""

import json
import argparse
from pathlib import Path
from typing import Any, Dict, Iterable, List


def flatten_record(record: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """Flatten a nested dictionary using dot-notation keys.

    TODO:
    - Extend to handle lists in a more flexible manner (e.g., emit multiple rows
      or index list items into separate columns).
    - Allow customization of separator based on downstream schema preferences.
    """

    items: List[tuple[str, Any]] = []
    for key, value in record.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key
        if isinstance(value, dict):
            items.extend(flatten_record(value, new_key, sep=sep).items())
        else:
            items.append((new_key, value))
    return dict(items)


def load_json_records(path: Path) -> Iterable[Dict[str, Any]]:
    """Load JSON objects from a file that may contain an array or newline-delimited entries."""
    with path.open("r", encoding="utf-8") as handle:
        first_char = handle.read(1)
        handle.seek(0)
        if first_char == "[":
            return json.load(handle)
        return (json.loads(line) for line in handle if line.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description="Flatten nested JSON events to normalized records.")
    parser.add_argument("input", type=Path, help="Path to a JSON file (array or newline-delimited JSON).")
    parser.add_argument("--output", type=Path, default=None, help="Optional CSV output path. Prints to stdout when omitted.")
    args = parser.parse_args()

    records = load_json_records(args.input)

    # TODO: replace print-based output with CSV writer or streaming pipeline
    # compatible with the normalization workflow.
    for record in records:
        flattened = flatten_record(record)
        print(flattened)


if __name__ == "__main__":
    main()
