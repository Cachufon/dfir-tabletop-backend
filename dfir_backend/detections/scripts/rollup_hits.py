#!/usr/bin/env python3
"""Roll up detection hits across scope areas."""

import argparse
import json
from collections import defaultdict
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate detections rollup summary")
    parser.add_argument(
        "--case_dir",
        required=True,
        help="Path to dfir_backend/custom/<case_id> directory containing analysis/detections",
    )
    parser.add_argument("--output_file", required=False, help="Optional override for rollup output file")
    return parser


def load_hits(hits_path: Path) -> list:
    try:
        return json.loads(hits_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []


def generate_rollup(case_dir: Path, output_file: Path) -> None:
    detections_dir = case_dir / "analysis" / "detections"
    rollup = defaultdict(lambda: defaultdict(int))

    if detections_dir.exists():
        for scope_dir in detections_dir.iterdir():
            if not scope_dir.is_dir():
                continue
            hits_path = scope_dir / "hits.json"
            hits = load_hits(hits_path)
            scope_area = scope_dir.name
            if not isinstance(hits, list):
                continue
            for hit in hits:
                rule_type = hit.get("rule_type", "unknown") if isinstance(hit, dict) else "unknown"
                rollup[scope_area][rule_type] += 1

    lines = ["# Detections Rollup (stub)", ""]
    if not rollup:
        lines.append("No hits found. Populate hits.json files before running a rollup.")
    else:
        lines.append("| Scope Area | Rule Type | Count |")
        lines.append("| --- | --- | --- |")
        for scope_area, rule_counts in sorted(rollup.items()):
            for rule_type, count in sorted(rule_counts.items()):
                lines.append(f"| {scope_area} | {rule_type} | {count} |")
    lines.append("")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text("\n".join(lines), encoding="utf-8")

    print(
        "Rollup stub completed. Placeholder counts generated. "
        f"Review {output_file} for the aggregated view."
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    case_dir = Path(args.case_dir).resolve()
    output_file = (
        Path(args.output_file).resolve()
        if args.output_file
        else case_dir / "analysis" / "detections_rollup.md"
    )

    generate_rollup(case_dir, output_file)


if __name__ == "__main__":
    main()
