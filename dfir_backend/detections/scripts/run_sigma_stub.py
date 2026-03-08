#!/usr/bin/env python3
"""Stub executor for Sigma-based detections."""

import argparse
import json
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Sigma detections stub")
    parser.add_argument("--case_dir", required=True, help="Path to dfir_backend/custom/<case_id> directory")
    parser.add_argument("--scope_area", required=True, help="Scope area (identity|saas|cloud|endpoint|ai)")
    parser.add_argument("--output_dir", required=False, help="Optional override for output directory")
    return parser


def write_stub_outputs(case_dir: Path, scope_area: str, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    hits_path = output_dir / "hits.json"
    summary_path = output_dir / "hits_summary.md"

    hits_path.write_text(json.dumps([], indent=2) + "\n", encoding="utf-8")
    summary_path.write_text(
        "# Sigma detection summary (stub)\n\n"
        "Placeholder summary for Sigma detections. Populate with real counts and key actors/assets once executed.\n",
        encoding="utf-8",
    )

    print(
        "Sigma stub execution completed. No real detections were run. "
        f"Outputs scaffolded at: {hits_path} and {summary_path}"
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    case_dir = Path(args.case_dir).resolve()
    scope_area = args.scope_area
    output_dir = Path(args.output_dir).resolve() if args.output_dir else case_dir / "analysis" / "detections" / scope_area

    write_stub_outputs(case_dir, scope_area, output_dir)


if __name__ == "__main__":
    main()
