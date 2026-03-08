#!/usr/bin/env python3
"""
Generate a deterministic, schema-valid scenario.yaml from case_manifest.json.

Behavior:
- Reads <case_dir>/case_manifest.json
- Requires manifest.scenario.category to be set and taxonomy-valid
- Writes scenario YAML to manifest.scenario.scenario_yaml_path (if present), else 20_delivery/scenario.yaml
- Updates manifest scenario flags and state metadata
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml  # type: ignore
except Exception:
    print("ERROR: Missing dependency PyYAML. Install with: pip install pyyaml", file=sys.stderr)
    raise

try:
    from jsonschema import Draft202012Validator  # type: ignore
except Exception:
    print("ERROR: Missing dependency jsonschema. Install with: pip install jsonschema", file=sys.stderr)
    raise


def repo_root_from_here() -> Path:
    # .../dfir_backend/ttx/scripts/generate_ttx_scenario_skeleton_from_case.py -> repo root is parents[3]
    return Path(__file__).resolve().parents[3]


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def read_taxonomy_headings(path: Path) -> List[str]:
    headings: List[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        t = line.strip()
        if t.startswith("## "):
            heading = t[3:].strip()
            if heading and heading != "Category naming rules (must follow)":
                headings.append(heading)
    return headings


def resolve_case_relative_strict(case_dir: Path, value: str) -> Path:
    p = Path(value.strip())
    if p.is_absolute():
        raise ValueError("manifest.scenario.scenario_yaml_path must be relative to case_dir")
    return (case_dir / p).resolve()


def normalize_id(text: str) -> str:
    base = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip()).strip("-").lower()
    if len(base) < 3:
        return "ttx-scenario"
    return base


def as_string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        cleaned = [str(item).strip() for item in value if str(item).strip()]
        return cleaned
    return []


def first_non_empty_list(*values: Any) -> List[str]:
    for value in values:
        parsed = as_string_list(value)
        if parsed:
            return parsed
    return []


def load_intake_structured(case_dir: Path, inputs_complete: bool) -> tuple[bool, Dict[str, Any]]:
    structured_path = case_dir / "10_inputs" / "intake_structured.json"
    if not structured_path.exists():
        message = f"WARN: intake_structured.json not found: {structured_path}; continuing with placeholders."
        if inputs_complete:
            print(
                "ERROR: manifest.inputs.inputs_complete is true but intake_structured.json is missing: "
                f"{structured_path}",
                file=sys.stderr,
            )
            raise FileNotFoundError("inputs_complete true and intake_structured missing")
        print(message)
        return False, {}
    return True, load_json(structured_path)


def parse_checked_checkbox_sections(intake_notes_path: Path) -> Dict[str, List[str]]:
    parsed: Dict[str, List[str]] = {
        "idp_tools": [],
        "email_tools": [],
        "edr_tools": [],
        "cloud_platforms": [],
        "redlines": [],
    }
    if not intake_notes_path.exists():
        return parsed

    section_to_key = {
        "Identity / SSO:": "idp_tools",
        "Email / collaboration:": "email_tools",
        "Endpoint / EDR:": "edr_tools",
        "Cloud:": "cloud_platforms",
        "- Topics to avoid (check all that apply):": "redlines",
        "Topics to avoid": "redlines",
    }

    lines = intake_notes_path.read_text(encoding="utf-8").splitlines()
    active_key = ""
    seen_checkbox = False
    checkbox_re = re.compile(r"^\s*-\s*\[x\]\s*(.+?)\s*$", re.IGNORECASE)

    for raw_line in lines:
        line = raw_line.strip()
        if line in section_to_key:
            active_key = section_to_key[line]
            seen_checkbox = False
            continue

        if not active_key:
            continue

        if line.startswith("#"):
            active_key = ""
            seen_checkbox = False
            continue

        if line == "" and seen_checkbox:
            active_key = ""
            seen_checkbox = False
            continue

        match = checkbox_re.match(raw_line)
        if match:
            value = match.group(1).strip()
            if value:
                parsed[active_key].append(value)
                seen_checkbox = True

    return parsed


def format_list(items: List[str], placeholder: str = "TBD") -> str:
    return ", ".join(items) if items else placeholder


def truncate_list(items: List[str], limit: int = 3) -> List[str]:
    return items[:limit]


def choose_category(
    manifest: Dict[str, Any],
    intake_structured: Dict[str, Any],
    valid_categories: List[str],
) -> str:
    scenario_meta = manifest.get("scenario", {})
    category = str(scenario_meta.get("category", "")).strip()
    if category:
        chosen = category
    else:
        preferred = str(
            intake_structured.get("preferred_category", intake_structured.get("preferred_scenario_category", ""))
        ).strip()
        if preferred and preferred != "No preference":
            chosen = preferred
            scenario_meta["category"] = chosen
        else:
            print(
                "ERROR: scenario category is required. Set manifest.scenario.category or intake_structured preferred category.",
                file=sys.stderr,
            )
            raise ValueError("category required")

    if chosen not in valid_categories:
        print(
            "ERROR: scenario category must match a taxonomy heading exactly.\n"
            f"- category: {chosen}\n"
            f"- allowed: {', '.join(valid_categories)}",
            file=sys.stderr,
        )
        raise ValueError("invalid category")
    return chosen


def build_scenario_obj(
    manifest: Dict[str, Any],
    category: str,
    intake_structured: Dict[str, Any],
    parsed_notes: Dict[str, List[str]],
) -> Dict[str, Any]:
    case_id = str(manifest.get("case_id", "ttx-case")).strip() or "ttx-case"
    client_alias = str(
        intake_structured.get("client_alias", intake_structured.get("client_organization", ""))
    ).strip()
    title = f"{category} TTX"
    if client_alias:
        title = f"{title} — {client_alias}"

    duration = intake_structured.get("duration_minutes", manifest.get("duration_minutes", 60))
    if not isinstance(duration, int) or duration < 15:
        duration = 60

    audiences = first_non_empty_list(
        intake_structured.get("audience_roles"),
        intake_structured.get("desired_audience_roles"),
        manifest.get("audience_roles"),
    )
    if not audiences:
        audiences = ["Security Team"]
    normalized_audiences = [str(a).strip() for a in audiences if str(a).strip()]
    if not normalized_audiences:
        normalized_audiences = ["Security Team"]

    crown_jewels = as_string_list(intake_structured.get("crown_jewels"))
    critical_services = as_string_list(intake_structured.get("critical_services"))
    high_impact_outcomes = as_string_list(intake_structured.get("high_impact_outcomes_to_avoid"))
    leadership_concerns = first_non_empty_list(
        intake_structured.get("leadership_concerns"),
        intake_structured.get("top_3_leadership_concerns"),
    )
    primary_objectives = as_string_list(intake_structured.get("primary_objectives"))

    summary = (
        "Objectives: "
        + format_list(primary_objectives)
        + "; Crown jewels: "
        + format_list(crown_jewels)
        + "; High-impact outcomes to avoid: "
        + format_list(high_impact_outcomes)
        + "."
    )

    business_context = (
        "Crown jewels: "
        + format_list(crown_jewels)
        + "; Critical services: "
        + format_list(critical_services)
        + "; Leadership concerns: "
        + format_list(leadership_concerns)
        + "."
    )

    threat_context = (
        f"Category focus: {category}. "
        f"Identity/SSO: {format_list(parsed_notes.get('idp_tools', []))}; "
        f"Email/collaboration: {format_list(parsed_notes.get('email_tools', []))}; "
        f"Endpoint/EDR: {format_list(parsed_notes.get('edr_tools', []))}; "
        f"Cloud platforms: {format_list(parsed_notes.get('cloud_platforms', []))}."
    )

    objectives = [
        "Establish incident command and ownership for the scenario.",
    ]
    for objective in primary_objectives:
        if objective not in objectives:
            objectives.append(objective)

    constraints = [
        "Exercise is discussion-based and does not execute live containment changes.",
    ]
    for redline in parsed_notes.get("redlines", []):
        constraints.append(f"Avoid: {redline}")
    confidentiality_level = str(intake_structured.get("confidentiality_level", "")).strip()
    if confidentiality_level:
        constraints.append(f"Confidentiality level: {confidentiality_level}")

    context_suffix = ""
    context_crown_jewels = truncate_list(crown_jewels)
    context_critical_services = truncate_list(critical_services)
    context_key_concerns = truncate_list(leadership_concerns)
    if context_crown_jewels or context_critical_services or context_key_concerns:
        context_suffix = (
            " Client context: "
            f"crown jewels={format_list(context_crown_jewels)}; "
            f"critical services={format_list(context_critical_services)}; "
            f"key concerns={format_list(context_key_concerns)}."
        )

    scenario_obj: Dict[str, Any] = {
        "version": 1,
        "scenario": {
            "id": normalize_id(case_id),
            "title": title,
            "category": category,
            "duration_minutes": duration,
            "audiences": normalized_audiences,
            "summary": summary,
            "threat_context": threat_context,
            "business_context": business_context,
            "objectives": objectives,
            "assumptions": [
                "Core logging and communications channels are available.",
            ],
            "constraints": constraints,
            "success_criteria": [
                "Participants produce timely decisions and escalation actions.",
            ],
            "pre_read": [
                "Review relevant incident response policies and playbooks.",
            ],
            "out_of_scope": [
                "Deep forensic analysis beyond tabletop discussion.",
            ],
            "facilitator_notes": "Tailor inject content to client environment before facilitation.",
        },
        "injects": [
            {
                "id": "i01",
                "t_plus_min": 0,
                "delivery_method": "facilitator_readout",
                "audience": normalized_audiences,
                "participant_prompt": "Initial incident indicators are reported. What are your first actions?" + context_suffix,
                "expected_discussion": [
                    "Confirm incident command roles and immediate triage actions.",
                ],
                "expected_decisions": [
                    "Decide initial containment posture and escalation path.",
                ],
                "evaluation_criteria": [
                    "Actions are prioritized with clear owners and timing.",
                ],
                "branching_guidance": "If containment is delayed, introduce business impact escalation.",
                "facilitator_notes": "Probe for communication and evidence-preservation decisions.",
                "evidence_refs": [
                    "10_inputs/intake_notes.md",
                ],
            }
        ],
    }
    return scenario_obj


def schema_validate(schema_path: Path, scenario_obj: Dict[str, Any]) -> List[str]:
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema)
    issues: List[str] = []
    for err in sorted(validator.iter_errors(scenario_obj), key=lambda e: list(e.path)):
        where = "$"
        if err.path:
            where = "$." + ".".join(str(p) for p in err.path)
        issues.append(f"Schema error at {where}: {err.message}")
    return issues


def manifest_schema_validate(schema_path: Path, manifest_obj: Dict[str, Any]) -> List[str]:
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema)
    issues: List[str] = []
    for err in sorted(validator.iter_errors(manifest_obj), key=lambda e: list(e.path)):
        where = "$"
        if err.path:
            where = "$." + ".".join(str(p) for p in err.path)
        issues.append(f"Schema error at {where}: {err.message}")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate deterministic TTX scenario skeleton from a case manifest.")
    parser.add_argument("--case-dir", required=True, help="Path to case directory containing case_manifest.json")
    parser.add_argument("--force", action="store_true", help="Overwrite existing scenario.yaml if present")
    args = parser.parse_args()

    repo_root = repo_root_from_here()
    schema_path = repo_root / "dfir_backend" / "ttx" / "schemas" / "ttx_scenario.schema.json"
    manifest_schema_path = repo_root / "dfir_backend" / "ttx" / "schemas" / "ttx_case_manifest.schema.json"
    taxonomy_path = repo_root / "dfir_backend" / "ttx" / "scenario_taxonomy.md"

    case_dir = Path(args.case_dir).expanduser().resolve()
    manifest_path = case_dir / "case_manifest.json"

    if not manifest_path.exists():
        print(f"ERROR: case_manifest.json not found: {manifest_path}", file=sys.stderr)
        return 2
    if not schema_path.exists():
        print(f"ERROR: Scenario schema not found: {schema_path}", file=sys.stderr)
        return 2
    if not manifest_schema_path.exists():
        print(f"ERROR: Manifest schema not found: {manifest_schema_path}", file=sys.stderr)
        return 2
    if not taxonomy_path.exists():
        print(f"ERROR: Taxonomy file not found: {taxonomy_path}", file=sys.stderr)
        return 2

    manifest = load_json(manifest_path)
    scenario_meta = manifest.get("scenario")
    if not isinstance(scenario_meta, dict):
        print("ERROR: manifest.scenario missing or not an object", file=sys.stderr)
        return 2

    valid_categories = read_taxonomy_headings(taxonomy_path)
    if not valid_categories:
        print("ERROR: No taxonomy headings found in scenario_taxonomy.md", file=sys.stderr)
        return 2

    inputs_complete = bool(manifest.get("inputs", {}).get("inputs_complete", False))
    try:
        intake_structured_present, intake_structured = load_intake_structured(case_dir, inputs_complete)
    except FileNotFoundError:
        return 2

    intake_notes_path = case_dir / "10_inputs" / "intake_notes.md"
    parsed_notes = parse_checked_checkbox_sections(intake_notes_path)

    try:
        category = choose_category(manifest, intake_structured, valid_categories)
    except ValueError:
        return 2

    scenario_yaml_value = scenario_meta.get("scenario_yaml_path")
    if isinstance(scenario_yaml_value, str) and scenario_yaml_value.strip():
        try:
            out_path = resolve_case_relative_strict(case_dir, scenario_yaml_value)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 2
    else:
        out_path = (case_dir / "20_delivery" / "scenario.yaml").resolve()

    if out_path.exists() and not args.force:
        print(f"ERROR: scenario.yaml already exists: {out_path}\nUse --force to overwrite.", file=sys.stderr)
        return 2

    scenario_obj = build_scenario_obj(manifest, category, intake_structured, parsed_notes)
    issues = schema_validate(schema_path, scenario_obj)
    if issues:
        print("ERROR: Generated scenario failed schema validation.", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    now = now_iso_utc()
    previous_state = manifest.get("state")
    scenario_meta["validated"] = False
    scenario_meta["approved"] = False
    scenario_meta["validation_errors"] = []
    scenario_meta["validation_last_run_utc"] = ""
    scenario_meta["draft_method"] = "OPTION_C_SKELETON"

    manifest["state"] = "S3_SCENARIO_DRAFTED"
    manifest["last_updated_at_utc"] = now

    history = manifest.get("history")
    if not isinstance(history, list):
        print("ERROR: manifest.history missing or not an array", file=sys.stderr)
        return 2
    history.append(
        {
            "at_utc": now,
            "event": "build_scenario_skeleton",
            "from_state": previous_state if isinstance(previous_state, str) else None,
            "to_state": "S3_SCENARIO_DRAFTED",
            "note": "Generated deterministic scenario skeleton from case.",
        }
    )

    manifest_issues = manifest_schema_validate(manifest_schema_path, manifest)
    if manifest_issues:
        print("ERROR: Updated manifest failed schema validation.", file=sys.stderr)
        for issue in manifest_issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    yaml_text = yaml.safe_dump(scenario_obj, sort_keys=False, allow_unicode=True)
    out_path.write_text(yaml_text, encoding="utf-8")

    snapshot_path = (case_dir / "20_delivery" / "scenario_inputs_snapshot.json").resolve()
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_obj = {
        "generated_at_utc": now,
        "intake_structured_present": intake_structured_present,
        "intake_structured": intake_structured if intake_structured else {},
        "parsed_environment": {
            "idp_tools": parsed_notes.get("idp_tools", []),
            "email_tools": parsed_notes.get("email_tools", []),
            "edr_tools": parsed_notes.get("edr_tools", []),
            "cloud_platforms": parsed_notes.get("cloud_platforms", []),
        },
        "parsed_redlines": parsed_notes.get("redlines", []),
        "category_used": category,
    }
    write_json(snapshot_path, snapshot_obj)

    write_json(manifest_path, manifest)

    print(f"OK: scenario skeleton generated: {out_path}")
    print(f"OK: scenario inputs snapshot generated: {snapshot_path}")
    print(f"OK: manifest updated: {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
