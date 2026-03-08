#!/usr/bin/env python3
"""
Create three synthetic demo TTX cases outside git and run full end-to-end workflow:
init -> scenario -> package -> handouts -> synthetic logs -> AAR.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
import re



REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / "dfir_backend" / "ttx" / "scripts"


LIBRARY_CASE_CATEGORIES = [
    "SaaS / Identity",
    "Ransomware / Extortion",
    "Business Email Compromise (BEC) / Fraud",
    "Web Application / API Breach",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def run_cmd(args: List[str]) -> None:
    subprocess.run(args, check=True)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_scenario_yaml(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    category_match = re.search(r"^\s{2}category:\s*(.+?)\s*$", text, flags=re.MULTILINE)
    duration_match = re.search(r"^\s{2}duration_minutes:\s*(\d+)\s*$", text, flags=re.MULTILINE)

    injects: List[Dict[str, Any]] = []
    lines = text.splitlines()
    current: Dict[str, Any] | None = None
    for line in lines:
        id_match = re.match(r"^\s*-\s+id:\s*(\S+)\s*$", line)
        if id_match:
            if current:
                injects.append(current)
            current = {"id": id_match.group(1), "participant_prompt": ""}
            continue
        if current is not None:
            prompt_match = re.match(r"^\s+participant_prompt:\s*(.+?)\s*$", line)
            if prompt_match:
                current["participant_prompt"] = prompt_match.group(1).strip().strip('"')
    if current:
        injects.append(current)

    return {
        "scenario": {
            "category": category_match.group(1).strip().strip('"') if category_match else "",
            "duration_minutes": int(duration_match.group(1)) if duration_match else 90,
        },
        "injects": injects,
    }


def load_manifest(path: Path) -> Dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"Manifest must be a JSON object: {path}")
    return obj


def write_manifest(path: Path, manifest: Dict[str, Any]) -> None:
    path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def write_case_inputs(case_dir: Path, case_name: str) -> None:
    inputs_dir = case_dir / "10_inputs"

    intake_notes = f"""# Intake Notes

## Engagement Context
- Case label: {case_name}
- Exercise sponsor: Global CISO
- Facilitation mode: Virtual workshop with leadership and operations stakeholders
- Date window: Synthetic planning cycle for readiness testing

## Participants (Roles)
- Executive leadership, Security Operations, IT Infrastructure, Legal/Privacy, Communications
- Incident Commander and Deputy IC
- Identity/Cloud platform owner and business continuity lead

## Business Priorities
- Maintain critical customer-facing services
- Preserve forensic fidelity for any impacted systems
- Reduce time to executive decisioning for containment and communications
- Validate cross-functional escalation and legal/compliance notification paths

## Constraints and Assumptions
- No live production systems are touched (discussion-only tabletop)
- Team must document assumptions when facts are incomplete
- External communications require legal review before release
- Simulated timeline compressed to decision-relevant checkpoints

## Success Criteria
- Clear incident command activation and ownership assignment
- Time-bounded containment and communication decisions at each inject
- Actionable improvements captured for 0/30/90-day remediation planning
"""

    ir_plan = f"""IR PLAN EXCERPT (SYNTHETIC) - {case_name}

1) Incident Classification and Activation
- Declare SEV-1 for verified business-impacting compromise indicators.
- Activate Incident Commander, Deputy IC, and legal/privacy liaison within 15 minutes.

2) Containment Decision Framework
- Prioritize identity/session revocation and access hardening where compromise is suspected.
- Isolate impacted workloads only after validating customer-facing downtime implications.
- Preserve logs and volatile evidence before any destructive remediation action.

3) Communications Governance
- Internal leadership briefing cadence: every 30 minutes during active escalation.
- External customer/regulatory communications require legal approval and documented rationale.
- Public statements must align to confirmed facts; avoid attribution without evidence.

4) Recovery and Lessons Learned
- Define service restoration milestones and acceptance criteria.
- Capture timeline, decisions, action owners, and unresolved questions for post-incident AAR.
"""

    threat_brief = f"""# Threat Brief (Synthetic)

## Executive Summary
This synthetic scenario reflects a realistic campaign pattern affecting modern enterprises in 2025-2026: adversaries exploit identity weaknesses, third-party trust paths, or endpoint control gaps, then accelerate pressure through operational disruption and reputational leverage.

## Threat Activity Highlights
- Adversaries blend credential abuse and stealthy persistence to evade early detection.
- Cloud/SaaS control plane misuse can produce high-impact privilege escalation with limited malware artifacts.
- Extortion and disclosure pressure increasingly target executive decision timelines.

## Defensive Implications
- Identity telemetry, administrative action logging, and cross-platform correlation are critical for early triage.
- Incident command clarity materially affects containment speed and communication quality.
- Pre-approved legal/comms playbooks reduce delay in mandatory and customer notifications.

## Recommended Exercise Focus
- Decision rights and escalation thresholds under ambiguity
- Cross-functional coordination between security, IT, legal, and communications
- Translation of inject-level observations into specific 0/30/90-day improvements
"""

    (inputs_dir / "intake_notes.md").write_text(intake_notes, encoding="utf-8")
    (inputs_dir / "ir_plan.txt").write_text(ir_plan, encoding="utf-8")
    (inputs_dir / "threat_brief.md").write_text(threat_brief, encoding="utf-8")


def write_library_intake_structured(case_dir: Path, category: str, case_name: str) -> None:
    payload: Dict[str, Any] = {
        "client_organization": f"{case_name.upper()} Holdings",
        "client_alias": case_name.upper(),
        "desired_audience_roles": [
            "Executive",
            "IT",
            "Security",
            "Legal/Privacy",
            "PR/Comms",
        ],
        "audience_roles": [
            "Executive",
            "IT",
            "Security",
            "Legal/Privacy",
            "PR/Comms",
        ],
        "top_3_leadership_concerns": [
            "Service uptime and customer trust",
            "Regulatory and contractual notification obligations",
            "Containment speed without over-disruption",
        ],
        "leadership_concerns": [
            "Service uptime and customer trust",
            "Regulatory and contractual notification obligations",
            "Containment speed without over-disruption",
        ],
        "primary_objectives": [
            "Exercise incident command decision flow",
            "Validate legal/comms escalation",
            "Capture 0/30/90-day remediation owners",
        ],
        "ttx_objectives": [
            "Exercise incident command decision flow",
            "Validate legal/comms escalation",
            "Capture 0/30/90-day remediation owners",
        ],
        "crown_jewels": [
            "Identity providers and privileged admin accounts",
            "Customer data and financial workflows",
            "Critical SaaS and production control planes",
        ],
        "critical_assets": [
            "Identity providers and privileged admin accounts",
            "Customer data and financial workflows",
            "Critical SaaS and production control planes",
        ],
        "critical_services": [
            "Customer portal",
            "Email and collaboration",
            "Core business transaction platform",
        ],
        "business_critical_services": [
            "Customer portal",
            "Email and collaboration",
            "Core business transaction platform",
        ],
        "preferred_scenario_category": category,
    }
    intake_path = case_dir / "10_inputs" / "intake_structured.json"
    intake_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def deterministic_runtime_json(case_dir: Path, scenario_obj: Dict[str, Any]) -> Path:
    scenario = scenario_obj.get("scenario", {})
    injects = scenario_obj.get("injects", [])
    notes_by_inject: Dict[str, Dict[str, str]] = {}

    for idx, inject in enumerate(injects, start=1):
        inject_id = str(inject.get("id", f"i{idx:02d}"))
        prompt = str(inject.get("participant_prompt", "")).strip()
        notes_by_inject[inject_id] = {
            "discussion": f"Team reviewed inject context and assumptions for {inject_id}. Prompt focus: {prompt[:180] or 'operational escalation and containment'}.",
            "decisions": f"Assigned Incident Commander authority and approved immediate triage track for {inject_id}; leadership checkpoint scheduled.",
            "actions": f"[0] Open investigation task for {inject_id}; [30] validate containment controls and stakeholder notifications; [90] confirm remediation owner and closure criteria.",
            "questions": f"What additional telemetry and legal/regulatory context are required to close uncertainty for {inject_id}?",
            "evidence": f"Synthetic evidence packet linked for {inject_id}: identity logs, endpoint timeline extracts, and communication draft artifacts.",
        }

    payload = {
        "exported_at_utc": "2026-01-15T18:00:00+00:00",
        "case_dir": str(case_dir),
        "scenario_path": str((case_dir / "20_delivery" / "scenario.yaml").resolve()),
        "t_plus_current_min": int(scenario.get("duration_minutes", 90)),
        "timer_started": True,
        "timer_start_utc": "2026-01-15T16:30:00+00:00",
        "notes_global": "Facilitator tracked escalation cadence, decision ownership, and communications governance assumptions across all injects.",
        "session_notes": "Facilitator tracked escalation cadence, decision ownership, and communications governance assumptions across all injects.",
        "notes_hotwash": """Strengths:
- Rapid incident command assignment with explicit deputy backup.
- Strong cross-functional collaboration between security, legal, and communications.
- Consistent documentation of assumptions, risks, and decision rationale.

Gaps:
- Notification trigger criteria were inconsistently applied across stakeholders.
- Evidence request workflow lacked clear ownership for rapid collection.
- 30/90-day remediation tracking process requires tighter governance.
""",
        "hotwash_notes": """Strengths:
- Rapid incident command assignment with explicit deputy backup.
- Strong cross-functional collaboration between security, legal, and communications.
- Consistent documentation of assumptions, risks, and decision rationale.

Gaps:
- Notification trigger criteria were inconsistently applied across stakeholders.
- Evidence request workflow lacked clear ownership for rapid collection.
- 30/90-day remediation tracking process requires tighter governance.
""",
        "parking_lot": "Confirm executive communication template ownership; validate third-party notification language.",
        "scoring": {
            "model_path": "dfir_backend/ttx/scoring_model.md",
            "scale": "1-5",
            "dimensions": {},
            "overall_avg": 3.8,
            "priority_gaps": ["Notification trigger consistency", "Evidence collection ownership"],
            "hide_numeric_in_md": True,
        },
        "hotwash_structured": {
            "went_well": "Incident command structure and role clarity were established early.",
            "gaps": "Notification thresholds and artifact collection ownership require standardization.",
            "improvements": "Define explicit 0/30/90-day owners for notification workflow and evidence intake.",
            "open_questions": "How quickly can cross-functional approvals be executed under regulator-driven deadlines?",
        },
        "notes_by_inject": notes_by_inject,
        "opening_script": "Welcome to the synthetic tabletop demo. Focus on decisions, escalation, and communications under pressure.",
        "facilitator_checklist": [
            "Set ground rules and assign facilitator/scribe roles.",
            "Capture decisions and owners at each inject.",
            "Run hotwash and confirm 0/30/90-day actions.",
        ],
        "scenario": scenario,
        "injects": injects,
    }

    logs_dir = case_dir / "30_outputs" / "ttx_logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    runtime_path = logs_dir / "scribe_runtime.json"
    runtime_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return runtime_path


def process_case(out_root: Path, timezone: str, force: bool, case_cfg: Dict[str, str]) -> Dict[str, Path]:
    case_name = case_cfg["case_name"]
    case_dir = out_root / case_name
    manifest_path = case_dir / "case_manifest.json"
    scenario_src = (REPO_ROOT / case_cfg["scenario_src"]).resolve()
    scenario_dst = case_dir / "20_delivery" / "scenario.yaml"

    if case_dir.exists() and force:
        shutil.rmtree(case_dir)

    init_cmd = [
        "python3",
        str(SCRIPTS_DIR / "init_ttx_case.py"),
        "--case-dir",
        str(case_dir),
        "--case-id",
        case_name,
        "--bundle-type",
        "HALF_DAY",
        "--duration-minutes",
        "120",
        "--timezone",
        timezone,
        "--handling-label",
        "INTERNAL",
        "--audience-roles",
        "Executive, IT, Security, Legal/Privacy, PR/Comms",
        "--industry",
        "Technology",
        "--region",
        "US",
    ]
    if force:
        init_cmd.append("--force")

    run_cmd(init_cmd)

    scenario_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(scenario_src, scenario_dst)

    write_case_inputs(case_dir, case_name)

    manifest = load_manifest(manifest_path)
    scenario_obj = parse_scenario_yaml(scenario_dst)
    scenario_category = str(scenario_obj.get("scenario", {}).get("category", "")).strip()

    manifest.setdefault("inputs", {})["inputs_complete"] = True
    manifest.setdefault("scenario", {})["category"] = scenario_category
    manifest["scenario"]["approved"] = True
    manifest["scenario"]["approved_by"] = "DEMO"
    manifest["scenario"]["approved_at_utc"] = now_iso()
    manifest["last_updated_at_utc"] = now_iso()
    write_manifest(manifest_path, manifest)

    run_cmd([
        "python3",
        str(SCRIPTS_DIR / "validate_ttx_scenario_file.py"),
        "--input",
        str(scenario_dst),
    ])

    run_cmd([
        "python3",
        str(SCRIPTS_DIR / "build_ttx_package_from_yaml.py"),
        "--case-dir",
        str(case_dir),
        "--input",
        str(scenario_dst),
        "--out-dir",
        str(case_dir / "20_delivery" / "ttx_package"),
    ])

    run_cmd([
        "python3",
        str(SCRIPTS_DIR / "export_ttx_handouts_html.py"),
        "--package-dir",
        str(case_dir / "20_delivery" / "ttx_package"),
        "--out-dir",
        str(case_dir / "20_delivery" / "handouts_html"),
        "--zip",
    ])

    runtime_path = deterministic_runtime_json(case_dir, scenario_obj)

    run_cmd([
        "python3",
        str(SCRIPTS_DIR / "build_aar_draft_from_runtime.py"),
        "--case-dir",
        str(case_dir),
    ])

    return {
        "case_dir": case_dir,
        "scenario_yaml": scenario_dst,
        "package_dir": case_dir / "20_delivery" / "ttx_package",
        "handouts_dir": case_dir / "20_delivery" / "handouts_html",
        "handouts_zip": case_dir / "20_delivery" / "handouts_html" / "handouts_html.zip",
        "runtime_json": runtime_path,
        "aar_draft": case_dir / "30_outputs" / "after_action_report_draft.md",
    }


def process_library_compile_case(
    out_root: Path,
    timezone: str,
    force: bool,
    case_cfg: Dict[str, str],
) -> Dict[str, Path]:
    case_name = case_cfg["case_name"]
    category = case_cfg["category"]
    if category not in LIBRARY_CASE_CATEGORIES:
        raise ValueError(f"Unsupported library compile category: {category}")
    case_dir = out_root / case_name
    manifest_path = case_dir / "case_manifest.json"
    scenario_path = case_dir / "20_delivery" / "scenario.yaml"

    if case_dir.exists() and force:
        shutil.rmtree(case_dir)

    init_cmd = [
        "python3",
        str(SCRIPTS_DIR / "init_ttx_case.py"),
        "--case-dir",
        str(case_dir),
        "--case-id",
        case_name,
        "--bundle-type",
        "HALF_DAY",
        "--duration-minutes",
        "120",
        "--timezone",
        timezone,
        "--handling-label",
        "INTERNAL",
        "--audience-roles",
        "Executive, IT, Security, Legal/Privacy, PR/Comms",
        "--industry",
        "Technology",
        "--region",
        "US",
    ]
    if force:
        init_cmd.append("--force")
    run_cmd(init_cmd)

    write_case_inputs(case_dir, case_name)
    write_library_intake_structured(case_dir, category, case_name)

    manifest = load_manifest(manifest_path)
    manifest.setdefault("inputs", {})["inputs_complete"] = True
    manifest.setdefault("scenario", {})["category"] = category
    manifest["scenario"]["approved"] = False
    manifest["scenario"]["approved_by"] = ""
    manifest["scenario"]["approved_at_utc"] = ""
    manifest["last_updated_at_utc"] = now_iso()
    write_manifest(manifest_path, manifest)

    run_cmd(["python3", str(SCRIPTS_DIR / "validate_ttx_library.py")])

    compile_cmd = [
        "python3",
        str(SCRIPTS_DIR / "compile_ttx_scenario_from_library.py"),
        "--case-dir",
        str(case_dir),
        "--force",
    ]
    run_cmd(compile_cmd)
    first_hash = sha256_file(scenario_path)
    run_cmd(compile_cmd)
    second_hash = sha256_file(scenario_path)
    if first_hash != second_hash:
        raise RuntimeError(
            f"Determinism check failed for {case_name}: scenario.yaml hash changed ({first_hash} != {second_hash})"
        )

    run_cmd([
        "python3",
        str(SCRIPTS_DIR / "validate_ttx_scenario_file.py"),
        "--input",
        str(scenario_path),
    ])

    manifest = load_manifest(manifest_path)
    manifest.setdefault("scenario", {})["approved"] = True
    manifest["scenario"]["approved_by"] = "SYNTHETIC_MODE"
    manifest["scenario"]["approved_at_utc"] = now_iso()
    manifest["last_updated_at_utc"] = now_iso()
    write_manifest(manifest_path, manifest)

    run_cmd([
        "python3",
        str(SCRIPTS_DIR / "build_ttx_package_from_yaml.py"),
        "--case-dir",
        str(case_dir),
        "--input",
        str(scenario_path),
        "--out-dir",
        str(case_dir / "20_delivery" / "ttx_package"),
    ])

    run_cmd([
        "python3",
        str(SCRIPTS_DIR / "export_ttx_handouts_html.py"),
        "--package-dir",
        str(case_dir / "20_delivery" / "ttx_package"),
        "--out-dir",
        str(case_dir / "20_delivery" / "handouts_html"),
        "--zip",
    ])

    scenario_obj = parse_scenario_yaml(scenario_path)
    runtime_path = deterministic_runtime_json(case_dir, scenario_obj)

    run_cmd([
        "python3",
        str(SCRIPTS_DIR / "build_aar_draft_from_runtime.py"),
        "--case-dir",
        str(case_dir),
    ])

    return {
        "case_dir": case_dir,
        "scenario_yaml": scenario_path,
        "package_dir": case_dir / "20_delivery" / "ttx_package",
        "handouts_dir": case_dir / "20_delivery" / "handouts_html",
        "handouts_zip": case_dir / "20_delivery" / "handouts_html" / "handouts_html.zip",
        "runtime_json": runtime_path,
        "aar_draft": case_dir / "30_outputs" / "after_action_report_draft.md",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed three synthetic TTX demo cases and run end-to-end workflow.")
    parser.add_argument("--out-root", default="~/ttx_cases/examples", help="Output root for synthetic examples.")
    parser.add_argument("--timezone", default="America/Los_Angeles", help="Timezone for created case manifests.")
    parser.add_argument("--force", action="store_true", help="Overwrite existing example case folders.")
    parser.add_argument(
        "--include-library-compile",
        action="store_true",
        help="Include four category-coverage cases that compile scenarios from the TTX library.",
    )
    args = parser.parse_args()

    out_root = Path(args.out_root).expanduser().resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    cases = [
        {
            "case_name": "001_saas_identity_compromise",
            "scenario_src": "dfir_backend/ttx/scenarios/example_ttx_saas_identity_compromise.yaml",
        },
        {
            "case_name": "002_ransomware_extortion",
            "scenario_src": "dfir_backend/ttx/scenarios/example_ttx_ransomware_extortion.yaml",
        },
        {
            "case_name": "003_third_party_supply_chain",
            "scenario_src": "dfir_backend/ttx/scenarios/example_ttx_third_party_supply_chain.yaml",
        },
    ]

    results = [process_case(out_root, args.timezone, args.force, case_cfg) for case_cfg in cases]

    if args.include_library_compile:
        library_cases = [
            {
                "case_name": "004_library_compile_saas_identity",
                "category": "SaaS / Identity",
            },
            {
                "case_name": "005_library_compile_ransomware_extortion",
                "category": "Ransomware / Extortion",
            },
            {
                "case_name": "006_library_compile_bec_fraud",
                "category": "Business Email Compromise (BEC) / Fraud",
            },
            {
                "case_name": "007_library_compile_webapp_api_breach",
                "category": "Web Application / API Breach",
            },
        ]
        results.extend(process_library_compile_case(out_root, args.timezone, args.force, case_cfg) for case_cfg in library_cases)

    print("\nSynthetic demo cases generated successfully:\n")
    for result in results:
        print(f"- Case dir: {result['case_dir']}")
        print(f"  - Scenario YAML: {result['scenario_yaml']}")
        print(f"  - Package dir: {result['package_dir']}")
        print(f"  - Handouts HTML dir: {result['handouts_dir']}")
        print(f"  - Handouts ZIP: {result['handouts_zip']}")
        print(f"  - Runtime logs JSON: {result['runtime_json']}")
        print(f"  - AAR draft: {result['aar_draft']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
