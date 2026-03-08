"""Validation stub for normalized outputs.

This script checks for the presence of normalized outputs per scope area
and prepares a simple markdown report. Refer to `normalized_data_contract.md`
for the authoritative schema requirements.
"""

import argparse
from pathlib import Path
from typing import Dict, List


EXPECTED_FILES: Dict[str, str] = {
    "identity": "identity.json",
    "saas": "saas.json",
    "cloud": "cloud.json",
    "endpoint": "endpoint.json",
    "ai": "ai_artifacts.json",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate normalized outputs against expected scaffolding.")
    parser.add_argument("--normalized_dir", required=True, help="Directory containing normalized outputs.")
    parser.add_argument("--output_report", required=True, help="Path to write a markdown validation report.")
    return parser.parse_args()


def check_expected_files(base_dir: str) -> Dict[str, bool]:
    status: Dict[str, bool] = {}
    for scope, filename in EXPECTED_FILES.items():
        path = Path(base_dir) / filename
        status[scope] = path.exists()
    return status


def build_report(base_dir: str, statuses: Dict[str, bool]) -> List[str]:
    lines: List[str] = ["# Normalized Validation Report", ""]
    lines.append(f"Normalized directory: {Path(base_dir).resolve()}")
    lines.append("")
    lines.append("## Expected Files")
    for scope, filename in EXPECTED_FILES.items():
        presence = "present" if statuses.get(scope) else "missing"
        lines.append(f"- {scope}: `{filename}` ({presence})")
    lines.append("")
    lines.append("## Placeholder Checks")
    lines.append("- Field-level validation not yet implemented; review normalized outputs manually.")
    lines.append("- Missing required fields should be noted as confidence limitations in reporting.")
    return lines


def write_report(report_path: str, lines: List[str]) -> None:
    path = Path(report_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    statuses = check_expected_files(args.normalized_dir)

    for scope, filename in EXPECTED_FILES.items():
        exists = "found" if statuses[scope] else "missing"
        print(f"[INFO] {scope} -> {filename}: {exists} in {args.normalized_dir}")

    report_lines = build_report(args.normalized_dir, statuses)
    write_report(args.output_report, report_lines)
    print(f"Validation report written to {args.output_report}.")


if __name__ == "__main__":
    main()
