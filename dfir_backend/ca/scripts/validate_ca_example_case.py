#!/usr/bin/env python3
"""Validate example CA case structure and execute detection stubs."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
EXAMPLE_CASE = REPO_ROOT / "dfir_backend" / "custom" / "example_case"
DETECTION_SCRIPTS_DIR = REPO_ROOT / "dfir_backend" / "detections" / "scripts"

REQUIRED_PATHS = [
    "intel",
    "raw",
    "raw/identity",
    "raw/saas",
    "normalized",
    "analysis/detections",
    "analysis/triage",
    "analysis/findings",
    "reports",
]



def validate_structure(case_root: Path) -> None:
    missing = [entry for entry in REQUIRED_PATHS if not (case_root / entry).exists()]
    if missing:
        missing_str = ", ".join(missing)
        raise SystemExit(f"Missing required paths in example_case: {missing_str}")


def run_detection_stubs(case_root: Path) -> None:
    commands = [
        [sys.executable, str(DETECTION_SCRIPTS_DIR / "run_sigma_stub.py"), "--case_dir", str(case_root), "--scope_area", "identity"],
        [sys.executable, str(DETECTION_SCRIPTS_DIR / "run_sigma_stub.py"), "--case_dir", str(case_root), "--scope_area", "saas"],
        [sys.executable, str(DETECTION_SCRIPTS_DIR / "run_maps_stub.py"), "--case_dir", str(case_root), "--scope_area", "ai"],
        [sys.executable, str(DETECTION_SCRIPTS_DIR / "run_yara_stub.py"), "--case_dir", str(case_root), "--scope_area", "endpoint"],
        [sys.executable, str(DETECTION_SCRIPTS_DIR / "run_ioc_sweep_stub.py"), "--case_dir", str(case_root), "--scope_area", "cloud"],
    ]

    for command in commands:
        subprocess.run(command, check=True, cwd=REPO_ROOT)


def main() -> None:
    validate_structure(EXAMPLE_CASE)

    with tempfile.TemporaryDirectory(prefix="dfir_example_case_") as tmp_dir:
        working_case = Path(tmp_dir) / "example_case"
        shutil.copytree(EXAMPLE_CASE, working_case)
        run_detection_stubs(working_case)


if __name__ == "__main__":
    main()
