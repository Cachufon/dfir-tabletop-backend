#!/usr/bin/env python3
"""
Initialize a TTX case folder (outside git) and create a case_manifest.json.

SAFETY:
- Refuses to write inside the git repo directory by default.
- Use --allow-in-repo ONLY for synthetic examples.

Creates:
- 00_admin/
- 10_inputs/
- 20_delivery/
- 30_outputs/
- 90_internal/
- case_manifest.json
- starter input placeholders in 10_inputs/

Example:
  python3 dfir_backend/ttx/scripts/init_ttx_case.py \
    --case-dir /secure_storage/ttx/TTX-20260211-CLIENT \
    --case-id TTX-20260211-CLIENT \
    --bundle-type EXECUTIVE \
    --duration-minutes 90 \
    --timezone America/Los_Angeles \
    --handling-label CLIENT_CONFIDENTIAL \
    --audience-roles "Executive, IT, Security, Legal/Privacy, PR/Comms" \
    --industry Healthcare \
    --region US
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

try:
    from jsonschema import Draft202012Validator  # type: ignore
except Exception:
    print("ERROR: Missing dependency jsonschema. Install with: pip install jsonschema", file=sys.stderr)
    raise


def repo_root_from_here() -> Path:
    # .../dfir_backend/ttx/scripts/init_ttx_case.py -> repo root is parents[3]
    return Path(__file__).resolve().parents[3]


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_manifest(schema_path: Path, manifest: Dict[str, Any]) -> None:
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(manifest), key=lambda e: list(e.path))
    if errors:
        msgs: List[str] = []
        for e in errors:
            where = "$"
            if e.path:
                where = "$." + ".".join(str(p) for p in e.path)
            msgs.append(f"{where}: {e.message}")
        raise ValueError("Manifest schema validation failed:\n" + "\n".join(msgs))


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a TTX case folder and case_manifest.json.")
    parser.add_argument("--case-dir", required=True, help="Case folder path (recommended: secure storage outside git).")
    parser.add_argument("--case-id", default="", help="Case/engagement identifier (optional; defaults to folder name).")
    parser.add_argument("--client-name", default="", help="Client name (optional).")
    parser.add_argument("--bundle-type", required=True, choices=["EXECUTIVE", "HALF_DAY", "FULL_DAY", "CUSTOM"])
    parser.add_argument("--duration-minutes", required=True, type=int)
    parser.add_argument("--timezone", required=True)
    parser.add_argument(
        "--handling-label",
        default="CLIENT_CONFIDENTIAL",
        choices=["PUBLIC", "INTERNAL", "CONFIDENTIAL", "CLIENT_CONFIDENTIAL"],
        help="Optional internal handling label for commercial engagements.",
    )
    parser.add_argument("--audience-roles", required=True, help="Comma-separated roles.")
    parser.add_argument("--industry", default="", help="Industry (high level).")
    parser.add_argument("--region", default="", help="Region (high level).")
    parser.add_argument("--force", action="store_true", help="Overwrite existing case_manifest.json if present.")
    parser.add_argument("--allow-in-repo", action="store_true", help="Allow writing inside repo (synthetic only).")
    args = parser.parse_args()

    repo_root = repo_root_from_here()
    case_dir = Path(args.case_dir).expanduser().resolve()

    if not args.allow_in_repo and is_within(case_dir, repo_root):
        print(
            "ERROR: Refusing to create case folder inside the git repo directory.\n"
            f"- Repo root: {repo_root}\n"
            f"- Case dir: {case_dir}\n\n"
            "Create case folders in secure project storage outside git, or use --allow-in-repo ONLY for synthetic examples.",
            file=sys.stderr,
        )
        return 2

    case_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = case_dir / "case_manifest.json"
    if manifest_path.exists() and not args.force:
        print(f"ERROR: case_manifest.json already exists: {manifest_path}\nUse --force to overwrite.", file=sys.stderr)
        return 2

    # Folder skeleton
    admin_dir = case_dir / "00_admin"
    inputs_dir = case_dir / "10_inputs"
    delivery_dir = case_dir / "20_delivery"
    outputs_dir = case_dir / "30_outputs"
    internal_dir = case_dir / "90_internal"

    for d in (admin_dir, inputs_dir, delivery_dir, outputs_dir, internal_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Starter input placeholders (copy templates if present; otherwise stub)
    intake_template_repo = repo_root / "dfir_backend" / "ttx" / "intake_template.md"
    intake_path = inputs_dir / "intake_notes.md"
    if intake_template_repo.exists():
        # Keep intake_notes.md synchronized by copying the template directly.
        content = intake_template_repo.read_text(encoding="utf-8")
        write_text(intake_path, content.rstrip() + "\n")
    else:
        write_text(
            intake_path,
            "# Intake Notes\n\nFill this file in secure storage. Do NOT commit to git.\n\n- Audience:\n- Duration:\n- Constraints:\n- Key systems:\n- Key concerns:\n",
        )

    ir_plan_path = inputs_dir / "ir_plan.txt"
    if not ir_plan_path.exists() or args.force:
        write_text(
            ir_plan_path,
            "Paste IR plan excerpts here (text). Store in secure storage. Do NOT commit to git.\n",
        )

    threat_brief_path = inputs_dir / "threat_brief.md"
    if not threat_brief_path.exists() or args.force:
        write_text(
            threat_brief_path,
            "# Threat Brief (Optional)\n\nHigh-level industry threat intel summary (no client secrets).\n",
        )

    inputs_readme_path = inputs_dir / "README.md"
    write_text(
        inputs_readme_path,
        "# 10_inputs Guide\n\n"
        "This folder should contain real case inputs only. Template JSON files stay in the repository and are not copied here.\n\n"
        "- `intake_notes.md` is required (manual entry or quick wizard).\n"
        "- `intake_structured.json` is generated by the quick wizard.\n"
        "- `ir_plan.txt` is optional.\n"
        "- `ir_plan_profile.json` is optional; generate it with `python3 dfir_backend/ttx/scripts/run_ir_plan_mapper.py --case-dir <CASE_DIR>`.\n"
        "- Crown jewels are captured via the intake wizard/notes for now.\n",
    )

    scenario_generation_dir = inputs_dir / "ttx_scenario_generation"
    scenario_generation_dir.mkdir(parents=True, exist_ok=True)

    inputs_tracker_path = admin_dir / "inputs_tracker.md"
    write_text(
        inputs_tracker_path,
        "# Inputs Tracker\n\n"
        "Use this checklist to verify key case inputs before scenario drafting.\n\n"
        "- [ ] `10_inputs/intake_notes.md` (required; manual or quick wizard)\n"
        "- [ ] `10_inputs/intake_structured.json` (optional; generated by quick wizard)\n"
        "- [ ] `10_inputs/ir_plan.txt` (optional but recommended)\n"
        "- [ ] `10_inputs/ir_plan_profile.json` (optional; generate with `python3 dfir_backend/ttx/scripts/run_ir_plan_mapper.py --case-dir <CASE_DIR>`)\n"
        "- [ ] `10_inputs/threat_brief.md` (optional)\n"
        "- [ ] Crown jewels captured in intake wizard/notes\n"
        "- [ ] `10_inputs/ttx_scenario_generation/` (workspace)\n",
    )

    # Canonical paths within the case
    scenario_yaml_path = delivery_dir / "scenario.yaml"
    package_dir = delivery_dir / "ttx_package"
    handouts_dir = delivery_dir / "handouts_html"
    handouts_zip_path = handouts_dir / "handouts_html.zip"
    logs_dir = outputs_dir / "ttx_logs"
    scribe_runtime_json_path = logs_dir / "scribe_runtime.json"
    aar_draft_path = outputs_dir / "after_action_report_draft.md"
    aar_ai_bundle_path = outputs_dir / "aar_ai_bundle.txt"
    executive_readout_path = outputs_dir / "executive_readout.md"

    case_id = args.case_id.strip() or case_dir.name

    manifest: Dict[str, Any] = {
        "schema_version": "1.1",
        "case_id": case_id,
        "client_name": args.client_name.strip(),
        "created_at_utc": now_iso(),
        "last_updated_at_utc": now_iso(),
        "state": "S1_CASE_INITIALIZED",
        "bundle_type": args.bundle_type,
        "duration_minutes": args.duration_minutes,
        "timezone": args.timezone.strip(),
        "handling_label": args.handling_label,
        "audience_roles": [r.strip() for r in args.audience_roles.split(",") if r.strip()],
        "industry": args.industry.strip(),
        "region": args.region.strip(),
        "paths": {
            "admin_dir": "00_admin",
            "inputs_dir": "10_inputs",
            "delivery_dir": "20_delivery",
            "outputs_dir": "30_outputs",
            "internal_dir": "90_internal",
        },
        "inputs": {
            "inputs_complete": False,
            "intake_notes_path": "10_inputs/intake_notes.md",
            "ir_plan_path": "10_inputs/ir_plan.txt",
            "threat_brief_path": "10_inputs/threat_brief.md",
            "scenario_generation_dir": "10_inputs/ttx_scenario_generation",
        },
        "scenario": {
            "scenario_yaml_path": "20_delivery/scenario.yaml",
            "category": "",
            "title_hint": "",
            "draft_method": "UNSET",
            "validated": False,
            "validation_last_run_utc": "",
            "validation_errors": [],
            "approved": False,
            "approved_by": "",
            "approved_at_utc": "",
        },
        "package": {
            "package_dir": "20_delivery/ttx_package",
            "built": False,
            "built_at_utc": "",
        },
        "handouts": {
            "handouts_dir": "20_delivery/handouts_html",
            "zip_path": "20_delivery/handouts_html/handouts_html.zip",
            "exported": False,
            "exported_at_utc": "",
        },
        "facilitation": {
            "status": "NOT_STARTED",
            "started_at_utc": "",
            "completed_at_utc": "",
        },
        "outputs": {
            "logs_dir": "30_outputs/ttx_logs",
            "scribe_runtime_json_path": "30_outputs/ttx_logs/scribe_runtime.json",
            "aar_draft_path": "30_outputs/after_action_report_draft.md",
            "aar_ai_bundle_path": "30_outputs/aar_ai_bundle.txt",
            "executive_readout_path": "30_outputs/executive_readout.md",
        },
        "history": [
            {
                "at_utc": now_iso(),
                "event": "init_case",
                "from_state": None,
                "to_state": "S1_CASE_INITIALIZED",
                "note": "Case initialized and folder skeleton created.",
            }
        ],
    }

    schema_path = repo_root / "dfir_backend" / "ttx" / "schemas" / "ttx_case_manifest.schema.json"
    if not schema_path.exists():
        print(f"ERROR: Manifest schema not found in repo: {schema_path}", file=sys.stderr)
        return 2

    validate_manifest(schema_path, manifest)

    write_text(manifest_path, json.dumps(manifest, indent=2) + "\n")

    print("Initialized TTX case:")
    print(f"- Case dir: {case_dir}")
    print(f"- Manifest: {manifest_path}")
    print("\nNext recommended steps:")
    print("1) Fill 10_inputs/intake_notes.md")
    print("2) Add IR plan excerpts to 10_inputs/ir_plan.txt (optional but recommended)")
    print("3) Run run_ir_plan_mapper.py to produce 10_inputs/ir_plan_profile.json (optional but recommended)")
    print("4) Run the case workflow runner to draft/validate scenario and generate deliverables.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
