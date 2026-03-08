#!/usr/bin/env python3
"""Test deterministic behavior of init_ca_case.py."""

from __future__ import annotations

import filecmp
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "dfir_backend" / "ca" / "scripts" / "init_ca_case.py"


def _collect_files(root: Path) -> list[Path]:
    return sorted(path.relative_to(root) for path in root.rglob("*") if path.is_file())


def _assert_dirs_match(dir_a: Path, dir_b: Path) -> None:
    files_a = _collect_files(dir_a)
    files_b = _collect_files(dir_b)
    assert files_a == files_b, "File trees differ between deterministic runs"

    for rel_path in files_a:
        file_a = dir_a / rel_path
        file_b = dir_b / rel_path
        assert filecmp.cmp(file_a, file_b, shallow=False), f"File contents differ: {rel_path}"


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="dfir_det_a_") as tmp_a, tempfile.TemporaryDirectory(prefix="dfir_det_b_") as tmp_b:
        case_a = Path(tmp_a) / "case"
        case_b = Path(tmp_b) / "case"

        cmd_a = [
            sys.executable,
            str(SCRIPT),
            "--case_dir",
            str(case_a),
            "--scope_area",
            "identity",
            "--deterministic",
        ]
        cmd_b = [
            sys.executable,
            str(SCRIPT),
            "--case_dir",
            str(case_b),
            "--scope_area",
            "identity",
            "--deterministic",
        ]

        subprocess.run(cmd_a, check=True, cwd=REPO_ROOT)
        subprocess.run(cmd_b, check=True, cwd=REPO_ROOT)

        _assert_dirs_match(case_a, case_b)


if __name__ == "__main__":
    main()
