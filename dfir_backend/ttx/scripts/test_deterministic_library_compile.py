#!/usr/bin/env python3
"""Determinism test for compile_ttx_scenario_from_library.py using a temp case."""

from __future__ import annotations

import hashlib
import json
import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(cmd: list[str], cwd: Path, verbose: bool) -> None:
    if verbose:
        completed = subprocess.run(cmd, cwd=cwd, check=False)
    else:
        completed = subprocess.run(cmd, cwd=cwd, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        error_lines = [f"Command failed ({completed.returncode}): {' '.join(cmd)}"]
        if not verbose:
            if completed.stdout:
                error_lines.append("stdout:")
                error_lines.append(completed.stdout)
            if completed.stderr:
                error_lines.append("stderr:")
                error_lines.append(completed.stderr)
        raise RuntimeError("\n".join(error_lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--keep-temp", action="store_true", help="Keep the temp case directory for debugging.")
    parser.add_argument("--verbose", action="store_true", help="Stream subprocess stdout/stderr.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    init_script = repo_root / "dfir_backend" / "ttx" / "scripts" / "init_ttx_case.py"
    compile_script = repo_root / "dfir_backend" / "ttx" / "scripts" / "compile_ttx_scenario_from_library.py"
    validate_script = repo_root / "dfir_backend" / "ttx" / "scripts" / "validate_ttx_scenario_file.py"
    tmp_dir = Path(tempfile.mkdtemp(prefix="ttx-determinism-"))
    case_dir = tmp_dir / "TTX-DETERMINISTIC-COMPILE"
    failed = False

    try:
        run(
            [
                sys.executable,
                str(init_script),
                "--case-dir",
                str(case_dir),
                "--case-id",
                "TTX-DETERMINISTIC-COMPILE",
                "--client-name",
                "Determinism Co",
                "--bundle-type",
                "EXECUTIVE",
                "--duration-minutes",
                "90",
                "--timezone",
                "UTC",
                "--handling-label",
                "CLIENT_CONFIDENTIAL",
                "--audience-roles",
                "Executive, IT, Security, Legal/Privacy, PR/Comms",
                "--industry",
                "Technology",
                "--region",
                "US",
            ],
            cwd=repo_root,
            verbose=args.verbose,
        )

        manifest_path = case_dir / "case_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["scenario"]["category"] = "SaaS / Identity"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        intake_structured_path = case_dir / "10_inputs" / "intake_structured.json"
        intake_structured = {
            "client_organization": "Determinism Co",
            "desired_audience_roles": ["Executive", "IT", "Security", "Legal/Privacy", "PR/Comms"],
            "top_3_leadership_concerns": [
                "Regulatory notification timing",
                "Identity control failure visibility",
                "Business continuity for customer access",
            ],
            "crown_jewels": ["Customer PII", "Identity tenant configuration", "Financial reporting data"],
            "critical_services": ["Single sign-on", "Corporate email", "Customer portal authentication"],
            "primary_objectives": [
                "Validate executive decision flow",
                "Exercise legal and comms coordination",
                "Verify containment priorities",
            ],
        }
        intake_structured_path.write_text(json.dumps(intake_structured, indent=2) + "\n", encoding="utf-8")

        intake_notes_path = case_dir / "10_inputs" / "intake_notes.md"
        intake_notes_path.write_text(
            "\n".join(
                [
                    "# Intake Notes",
                    "",
                    "Identity / SSO:",
                    "  - [x] Okta",
                    "  - [x] Microsoft Entra ID",
                    "",
                    "Cloud:",
                    "  - [x] AWS",
                    "",
                    "- Topics to avoid (check all that apply):",
                    "  - [x] Ransom payment discussion",
                    "  - [x] Law enforcement engagement",
                    "",
                    "### Desired audience(s) (roles) — REQUIRED",
                    "  - [x] Executive",
                ]
            ),
            encoding="utf-8",
        )

        scenario_path = case_dir / "20_delivery" / "scenario.yaml"

        run([sys.executable, str(compile_script), "--case-dir", str(case_dir)], cwd=repo_root, verbose=args.verbose)
        run([sys.executable, str(validate_script), "--input", str(scenario_path)], cwd=repo_root, verbose=args.verbose)

        snapshot = json.loads((case_dir / "20_delivery" / "scenario_inputs_snapshot.json").read_text(encoding="utf-8"))
        parsed = snapshot["parsed_selections"]
        if parsed.get("cloud_platforms") != ["AWS"]:
            raise RuntimeError(f"Expected cloud_platforms ['AWS']; got {parsed.get('cloud_platforms')}")
        if parsed.get("redlines") != ["Ransom payment discussion", "Law enforcement engagement"]:
            raise RuntimeError(f"Unexpected redlines parsed: {parsed.get('redlines')}")
        if any(item in parsed.get("cloud_platforms", []) for item in parsed.get("redlines", [])):
            raise RuntimeError("Redline values bled into cloud_platforms")

        scenario_text = scenario_path.read_text(encoding="utf-8")
        redline_constraint = "Redline topics: Ransom payment discussion, Law enforcement engagement"
        if redline_constraint not in scenario_text:
            raise RuntimeError("Redlines were not rendered into scenario constraints")
        if "Redline topics: AWS" in scenario_text:
            raise RuntimeError("Cloud platform value incorrectly rendered into redlines constraint")
        if "AWS" not in scenario_text:
            raise RuntimeError("Expected CLOUD_PLATFORMS placeholder rendering to include AWS")

        hash_run_1 = sha256_file(scenario_path)

        run(
            [sys.executable, str(compile_script), "--case-dir", str(case_dir), "--force"],
            cwd=repo_root,
            verbose=args.verbose,
        )
        run([sys.executable, str(validate_script), "--input", str(scenario_path)], cwd=repo_root, verbose=args.verbose)
        hash_run_2 = sha256_file(scenario_path)

        if hash_run_1 != hash_run_2:
            print("FAIL: scenario.yaml SHA256 mismatch across runs", file=sys.stderr)
            print(f"run_1={hash_run_1}", file=sys.stderr)
            print(f"run_2={hash_run_2}", file=sys.stderr)
            failed = True
            return 1

        print("PASS")
        return 0
    except Exception as exc:
        failed = True
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    finally:
        if args.keep_temp:
            print(f"Kept temp case dir: {tmp_dir}")
        else:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            if failed:
                print("Re-run with --keep-temp --verbose to inspect artifacts.", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
