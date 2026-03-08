#!/usr/bin/env python3
"""Initialize a compromise assessment case skeleton."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATES_DIR = REPO_ROOT / "dfir_backend" / "ca" / "templates"
FIXED_TIMESTAMP = "2024-01-01T00:00:00Z"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize a compromise assessment case skeleton")
    parser.add_argument("--case_dir", required=True, help="Destination directory for the new case")
    parser.add_argument("--scope_area", required=True, help="Scope area (identity|saas|cloud|endpoint|ai)")
    parser.add_argument("--deterministic", action="store_true", help="Use fixed timestamps in case_manifest.json")
    parser.add_argument(
        "--allow-in-repo",
        action="store_true",
        help="Allow creating synthetic case folders inside the current git repository",
    )
    return parser


def _is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _timestamp(deterministic: bool) -> str:
    if deterministic:
        return FIXED_TIMESTAMP
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def initialize_case(case_dir: Path, scope_area: str, deterministic: bool, allow_in_repo: bool) -> None:
    case_dir = case_dir.resolve()

    if _is_within(case_dir, REPO_ROOT) and not allow_in_repo:
        raise SystemExit(
            "Refusing to create case directory inside this git repository. "
            "Pass --allow-in-repo only for synthetic/testing use."
        )

    directories = [
        case_dir / "00_admin",
        case_dir / "intel",
        case_dir / "raw" / scope_area,
        case_dir / "normalized",
        case_dir / "analysis" / "detections" / scope_area,
        case_dir / "analysis" / "triage",
        case_dir / "analysis" / "findings",
        case_dir / "reports",
        case_dir / "iocs",
        case_dir / "sigma",
        case_dir / "yara",
        case_dir / "ai_prompts",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    for template_path in sorted(TEMPLATES_DIR.iterdir()):
        if template_path.is_file():
            shutil.copy2(template_path, case_dir / "00_admin" / template_path.name)

    manifest = {
        "case_name": case_dir.name,
        "scope_area": scope_area,
        "created_at": _timestamp(deterministic),
        "updated_at": _timestamp(deterministic),
        "deterministic": deterministic,
    }
    (case_dir / "case_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    args = build_parser().parse_args()
    initialize_case(
        case_dir=Path(args.case_dir),
        scope_area=args.scope_area,
        deterministic=args.deterministic,
        allow_in_repo=args.allow_in_repo,
    )


if __name__ == "__main__":
    main()
