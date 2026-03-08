#!/usr/bin/env python3
"""
Compile a deterministic TTX scenario YAML from scenario library module maps + inject banks.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml  # type: ignore
from jsonschema import Draft202012Validator  # type: ignore


CATEGORY_SLUGS: Dict[str, str] = {
    "SaaS / Identity": "saas_identity",
    "Ransomware / Extortion": "ransomware_extortion",
    "Business Email Compromise (BEC) / Fraud": "bec_fraud",
    "Web Application / API Breach": "webapp_api_breach",
}

PLACEHOLDERS = [
    "CLIENT_ALIAS",
    "CROWN_JEWELS",
    "CRITICAL_SERVICES",
    "LEADERSHIP_CONCERNS",
    "PRIMARY_OBJECTIVES",
    "IDP_TOOLS",
    "EMAIL_TOOLS",
    "EDR_TOOLS",
    "CLOUD_PLATFORMS",
    "AUDIENCES",
]


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[3]


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_yaml(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(obj, sort_keys=False, allow_unicode=True), encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def as_string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    for item in value:
        text = str(item).strip()
        if text:
            out.append(text)
    return out


def read_optional_profile_file(path: Path) -> Dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {}
    try:
        if path.suffix.lower() in {".yaml", ".yml"}:
            obj = load_yaml(path)
        else:
            obj = load_json(path)
    except Exception:
        return {}
    return obj if isinstance(obj, dict) else {}


def load_client_test_profiles(case_dir: Path) -> Dict[str, Any]:
    base_tests = {
        "ir_plan_capabilities": [],
        "crown_jewel_ids": [],
        "threat_ttps": [],
    }

    candidates = [
        case_dir / "10_inputs" / "client_profiles.json",
        case_dir / "10_inputs" / "client_profiles.yaml",
        case_dir / "10_inputs" / "client_profiles.yml",
        case_dir / "10_inputs" / "client_profile.json",
        case_dir / "10_inputs" / "client_profile.yaml",
        case_dir / "10_inputs" / "client_profile.yml",
    ]

    loaded: Dict[str, Any] = {}
    for candidate in candidates:
        obj = read_optional_profile_file(candidate)
        if obj:
            loaded = obj
            break

    profile_roots: List[Dict[str, Any]] = []
    if loaded:
        profile_roots.append(loaded)
        tests_obj = loaded.get("tests")
        if isinstance(tests_obj, dict):
            profile_roots.append(tests_obj)
        profile_obj = loaded.get("profile")
        if isinstance(profile_obj, dict):
            profile_roots.append(profile_obj)

    for root in profile_roots:
        for key in base_tests:
            values = as_string_list(root.get(key))
            if values:
                base_tests[key] = values

    per_inject: Dict[str, Dict[str, List[str]]] = {}
    for root in profile_roots:
        inject_tests_obj = root.get("inject_tests")
        if not isinstance(inject_tests_obj, dict):
            continue
        for inject_id, inject_test_values in inject_tests_obj.items():
            if not isinstance(inject_id, str) or not inject_id:
                continue
            if not isinstance(inject_test_values, dict):
                continue
            current = per_inject.setdefault(
                inject_id,
                {
                    "ir_plan_capabilities": [],
                    "crown_jewel_ids": [],
                    "threat_ttps": [],
                },
            )
            for key in current:
                values = as_string_list(inject_test_values.get(key))
                if values:
                    current[key] = values

    return {
        "base_tests": base_tests,
        "per_inject": per_inject,
    }


def infer_profile(duration_minutes: Any) -> str:
    if isinstance(duration_minutes, int):
        if duration_minutes >= 360:
            return "FULL_DAY"
        if duration_minutes == 240:
            return "HALF_DAY"
        if duration_minutes <= 120:
            return "EXEC_90"
    return "EXEC_90"


def parse_checkbox_selections(notes_text: str) -> Dict[str, List[str]]:
    selections = {
        "identity_sso": [],
        "email_collaboration": [],
        "endpoint_edr": [],
        "cloud": [],
        "topics_to_avoid_redlines": [],
    }
    checked_line = re.compile(r"^\s*[-*]\s*\[x\]\s*(.+)$", re.IGNORECASE)
    header_strip_re = re.compile(r"^\s*#+\s*")
    list_strip_re = re.compile(r"^\s*[-*]\s*")
    section_label_re = re.compile(r"^\s*(?:#+\s*)?(.+?):\s*$")

    def normalize_header(line: str) -> str:
        value = header_strip_re.sub("", line)
        value = list_strip_re.sub("", value)
        value = value.strip()
        if value.endswith(":"):
            value = value[:-1].rstrip()
        return value.lower()

    def detect_section_key(normalized: str) -> Optional[str]:
        if normalized.startswith("identity / sso"):
            return "identity_sso"
        if normalized.startswith("email / collaboration"):
            return "email_collaboration"
        if normalized.startswith("endpoint / edr"):
            return "endpoint_edr"
        if normalized.startswith("cloud"):
            return "cloud"
        if normalized.startswith("topics to avoid (check all that apply)"):
            return "topics_to_avoid_redlines"
        return None

    section_key: Optional[str] = None

    for raw_line in notes_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue

        normalized = normalize_header(line)
        detected_section = detect_section_key(normalized)
        if detected_section:
            section_key = detected_section
            continue

        if line.lstrip().startswith("#"):
            section_key = None
            continue

        if section_label_re.match(line) and not checked_line.match(line):
            section_key = None
            continue

        m = checked_line.match(line)
        if m and section_key:
            selections[section_key].append(m.group(1).strip())

    selections["cloud_platforms"] = selections.get("cloud", [])
    selections["redlines"] = selections.get("topics_to_avoid_redlines", [])

    return selections


def file_fingerprint(path: Path) -> Dict[str, Any]:
    obj: Dict[str, Any] = {
        "filename": path.name,
        "path": str(path),
        "exists": path.exists(),
    }
    if not path.exists() or not path.is_file():
        return obj
    data = path.read_bytes()
    obj["size"] = len(data)
    obj["sha256"] = hashlib.sha256(data).hexdigest()
    return obj


def list_to_text(value: Any) -> str:
    if isinstance(value, list):
        items = [str(v).strip() for v in value if str(v).strip()]
        return ", ".join(items) if items else "TBD"
    if isinstance(value, str):
        return value.strip() or "TBD"
    return "TBD"


def clean_string_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    out: List[str] = []
    for item in value:
        text = str(item).strip()
        if text and text.upper() != "TBD":
            out.append(text)
    return out


def clean_text_value(value: Any) -> str:
    if isinstance(value, list):
        cleaned = clean_string_list(value)
        return ", ".join(cleaned)
    if isinstance(value, str):
        text = value.strip()
        if text and text.upper() != "TBD":
            return text
    return ""


def category_threat_context(category: str) -> str:
    mapping = {
        "Ransomware / Extortion": (
            "A threat actor gains initial access, moves laterally, encrypts critical systems, and issues "
            "extortion demands that force high-pressure outage governance and recovery decisions."
        ),
        "SaaS / Identity": (
            "A credential or session compromise enables mailbox and SaaS abuse, creating customer-impact risk "
            "and urgent identity containment and communications decisions."
        ),
        "Business Email Compromise (BEC) / Fraud": (
            "Social engineering and business email compromise drive payment diversion attempts, requiring rapid "
            "financial control, legal, and stakeholder communication decisions."
        ),
        "Web Application / API Breach": (
            "Adversary activity against web application and API surfaces exposes sensitive data and disrupts "
            "services, requiring coordinated containment, investigation, and disclosure decisions."
        ),
    }
    return mapping.get(
        category,
        "A realistic cyber incident evolves rapidly and requires coordinated executive decisions on escalation, "
        "containment, communications, and recovery priorities.",
    )


def make_safe_scenario_id(case_id: Any) -> str:
    case_id_text = str(case_id).strip() if case_id is not None else ""
    if not case_id_text:
        return "ttx-case"
    safe_case_id = re.sub(r"[^a-zA-Z0-9]+", "-", case_id_text).strip("-").lower()
    if not safe_case_id:
        return "ttx-case"
    return f"ttx-{safe_case_id}"


def build_placeholder_map(manifest: Dict[str, Any], intake: Dict[str, Any], selections: Dict[str, List[str]]) -> Dict[str, str]:
    client_alias = (
        intake.get("client_alias")
        or intake.get("client_organization")
        or manifest.get("client_name")
        or manifest.get("case_id")
        or "TBD"
    )
    audience_roles = intake.get("audiences") or intake.get("audience_roles") or intake.get("desired_audience_roles")
    if not isinstance(audience_roles, list) or not audience_roles:
        audience_roles = manifest.get("audience_roles") if isinstance(manifest.get("audience_roles"), list) else ["Executive"]

    placeholder_map = {
        "CLIENT_ALIAS": str(client_alias),
        "CROWN_JEWELS": list_to_text(intake.get("crown_jewels") or intake.get("critical_assets")),
        "CRITICAL_SERVICES": list_to_text(intake.get("critical_services") or intake.get("business_critical_services")),
        "LEADERSHIP_CONCERNS": list_to_text(
            intake.get("leadership_concerns")
            or intake.get("top_3_leadership_concerns")
            or intake.get("executive_concerns")
        ),
        "PRIMARY_OBJECTIVES": list_to_text(intake.get("primary_objectives") or intake.get("ttx_objectives")),
        "IDP_TOOLS": list_to_text(intake.get("idp_tools") or selections.get("identity_sso", [])),
        "EMAIL_TOOLS": list_to_text(intake.get("email_tools") or selections.get("email_collaboration", [])),
        "EDR_TOOLS": list_to_text(intake.get("edr_tools") or selections.get("endpoint_edr", [])),
        "CLOUD_PLATFORMS": list_to_text(intake.get("cloud_platforms") or selections.get("cloud", [])),
        "AUDIENCES": list_to_text(audience_roles),
    }

    return {k: (v if v else "TBD") for k, v in placeholder_map.items()}


def choose_category(manifest: Dict[str, Any], intake_structured: Dict[str, Any]) -> str:
    scenario_meta = manifest.get("scenario", {})
    manifest_category = ""
    if isinstance(scenario_meta, dict):
        manifest_category = str(scenario_meta.get("category", "")).strip()
    if manifest_category:
        chosen = manifest_category
    else:
        preferred_scenario_category = str(intake_structured.get("preferred_scenario_category", "")).strip()
        preferred_category = str(intake_structured.get("preferred_category", "")).strip()
        if preferred_scenario_category in CATEGORY_SLUGS:
            chosen = preferred_scenario_category
        elif preferred_category in CATEGORY_SLUGS:
            chosen = preferred_category
        else:
            print(
                "ERROR: scenario category is required. Set manifest['scenario']['category'] or "
                "10_inputs/intake_structured.json['preferred_scenario_category'] (or ['preferred_category']) "
                "to a supported category.",
                file=sys.stderr,
            )
            raise ValueError("category required")

    if chosen not in CATEGORY_SLUGS:
        print(
            "ERROR: unsupported category for library compile. "
            f"Got: {chosen}. Allowed: {', '.join(CATEGORY_SLUGS.keys())}",
            file=sys.stderr,
        )
        raise ValueError("invalid category")

    return chosen


def build_tooling_summary(placeholder_map: Dict[str, str]) -> str:
    tooling_fields: List[str] = [
        "IDP_TOOLS",
        "EMAIL_TOOLS",
        "EDR_TOOLS",
        "CLOUD_PLATFORMS",
    ]

    components: List[str] = []
    for key in tooling_fields:
        raw_value = str(placeholder_map.get(key, "")).strip()
        if not raw_value or raw_value.upper() == "TBD":
            continue
        components.append(f"{key}={raw_value}")

    if not components:
        return ""

    return "Tooling summary: " + "; ".join(components)


def apply_placeholders(text: str, placeholder_map: Dict[str, str]) -> str:
    out = text
    for key in PLACEHOLDERS:
        out = out.replace("{" + key + "}", placeholder_map.get(key, "TBD"))
    return out


def schema_validate_scenario(repo_root: Path, scenario_obj: Dict[str, Any]) -> List[str]:
    schema_path = repo_root / "dfir_backend" / "ttx" / "schemas" / "ttx_scenario.schema.json"
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema)
    issues: List[str] = []
    for err in sorted(validator.iter_errors(scenario_obj), key=lambda e: list(e.path)):
        where = "$"
        if err.path:
            where = "$." + ".".join(str(p) for p in err.path)
        issues.append(f"scenario schema error at {where}: {err.message}")
    return issues


def build_inject_registry(paths: List[Path]) -> Dict[str, Dict[str, Any]]:
    registry: Dict[str, Dict[str, Any]] = {}
    for p in paths:
        obj = load_yaml(p)
        if not isinstance(obj, dict):
            raise ValueError(f"Inject bank root must be an object: {p}")
        injects = obj.get("injects", [])
        if not isinstance(injects, list):
            raise ValueError(f"Inject bank 'injects' must be a list: {p}")
        for item in injects:
            if not isinstance(item, dict):
                continue
            inject_id = item.get("id")
            if not isinstance(inject_id, str) or not inject_id:
                continue
            if inject_id in registry:
                raise ValueError(f"Duplicate inject id '{inject_id}' across banks")
            registry[inject_id] = {
                "inject": item,
                "source_bank": p.name,
            }
    return registry


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile TTX scenario YAML from scenario library")
    parser.add_argument("--case-dir", required=True, help="Case directory")
    parser.add_argument("--profile", choices=["EXEC_90", "HALF_DAY", "FULL_DAY"], default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--allow-in-repo", action="store_true")
    args = parser.parse_args()

    repo_root = repo_root_from_here()
    case_dir = Path(args.case_dir).expanduser().resolve()

    if not case_dir.exists() or not case_dir.is_dir():
        print(f"ERROR: case dir not found: {case_dir}", file=sys.stderr)
        return 2

    if not args.allow_in_repo and repo_root in [case_dir, *case_dir.parents]:
        print("ERROR: refusing to operate in repo directory without --allow-in-repo", file=sys.stderr)
        return 2

    manifest_path = case_dir / "case_manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: case manifest not found: {manifest_path}", file=sys.stderr)
        return 2

    manifest = load_json(manifest_path)
    if not isinstance(manifest, dict):
        print("ERROR: case_manifest.json root must be an object", file=sys.stderr)
        return 2

    profile = args.profile or infer_profile(manifest.get("duration_minutes"))

    intake_structured_path = case_dir / "10_inputs" / "intake_structured.json"
    intake_structured: Dict[str, Any] = {}
    if intake_structured_path.exists():
        loaded_intake = load_json(intake_structured_path)
        if isinstance(loaded_intake, dict):
            intake_structured = loaded_intake
    else:
        print(f"WARN: intake structured metadata not found: {intake_structured_path}", file=sys.stderr)

    try:
        category = choose_category(manifest, intake_structured)
    except ValueError:
        return 2

    slug = CATEGORY_SLUGS[category]

    intake_notes_path = case_dir / "10_inputs" / "intake_notes.md"
    parsed_selections = {
        "identity_sso": [],
        "email_collaboration": [],
        "endpoint_edr": [],
        "cloud": [],
        "topics_to_avoid_redlines": [],
    }
    if intake_notes_path.exists():
        parsed_selections = parse_checkbox_selections(intake_notes_path.read_text(encoding="utf-8"))

    parsed_selections["cloud_platforms"] = parsed_selections.get("cloud", [])
    parsed_selections["redlines"] = parsed_selections.get("topics_to_avoid_redlines", [])

    module_map_path = repo_root / "dfir_backend" / "ttx" / "library" / "module_maps" / f"{slug}.yaml"
    core_bank_path = repo_root / "dfir_backend" / "ttx" / "library" / "inject_bank" / "core_common.yaml"
    category_bank_path = repo_root / "dfir_backend" / "ttx" / "library" / "inject_bank" / f"{slug}.yaml"

    for p in [module_map_path, core_bank_path, category_bank_path]:
        if not p.exists():
            print(f"ERROR: required library file missing: {p}", file=sys.stderr)
            return 2

    module_map = load_yaml(module_map_path)
    if not isinstance(module_map, dict):
        print(f"ERROR: module map root must be an object: {module_map_path}", file=sys.stderr)
        return 2

    profiles = module_map.get("profiles", {})
    if not isinstance(profiles, dict) or profile not in profiles:
        print(f"ERROR: profile '{profile}' missing from module map: {module_map_path}", file=sys.stderr)
        return 2
    profile_obj = profiles[profile]
    if not isinstance(profile_obj, dict):
        print(f"ERROR: profile '{profile}' must be an object", file=sys.stderr)
        return 2

    inject_registry = build_inject_registry([core_bank_path, category_bank_path])
    client_test_profiles = load_client_test_profiles(case_dir)

    placeholder_map = build_placeholder_map(manifest, intake_structured, parsed_selections)

    audience_roles = (
        intake_structured.get("audiences")
        or intake_structured.get("audience_roles")
        or intake_structured.get("desired_audience_roles")
    )
    if not isinstance(audience_roles, list) or not audience_roles:
        audience_roles = manifest.get("audience_roles") if isinstance(manifest.get("audience_roles"), list) else ["Executive"]

    client_alias = placeholder_map["CLIENT_ALIAS"]
    profile_description = str(profile_obj.get("description", "")).strip()
    modules = profile_obj.get("modules", []) if isinstance(profile_obj.get("modules"), list) else []

    tooling_summary = build_tooling_summary(placeholder_map)
    business_segments = [f"Client: {client_alias}"]
    crown_jewels_text = clean_text_value(intake_structured.get("crown_jewels") or intake_structured.get("critical_assets"))
    critical_services_text = clean_text_value(
        intake_structured.get("critical_services") or intake_structured.get("business_critical_services")
    )
    if crown_jewels_text:
        business_segments.append(f"Crown jewels: {crown_jewels_text}")
    if critical_services_text:
        business_segments.append(f"Critical services: {critical_services_text}")
    business_context = ". ".join(business_segments) + "."
    if tooling_summary:
        business_context = f"{business_context}. {tooling_summary}"

    summary_text = profile_description or f"{category} tabletop exercise tailored to the client environment and IR plan inputs."

    base_objectives = [
        f"Assess readiness for {category} response decisions.",
        "Validate escalation, containment, communications, and recovery decision rights under time pressure.",
        "Confirm prioritization of crown jewels and critical services.",
    ]
    intake_objectives = clean_string_list(intake_structured.get("primary_objectives") or intake_structured.get("ttx_objectives"))
    objectives: List[str] = []
    seen_objectives = set()
    for objective in base_objectives + intake_objectives:
        if "profile " in objective.lower():
            continue
        if objective in seen_objectives:
            continue
        objectives.append(objective)
        seen_objectives.add(objective)

    facilitator_notes_parts = [
        (
            f"[COMPILER_META] module_map={module_map_path.name} banks=core_common.yaml,{slug}.yaml "
            f"profile={profile}"
        )
    ]
    primary_objectives_text = clean_text_value(
        intake_structured.get("primary_objectives") or intake_structured.get("ttx_objectives")
    )
    if primary_objectives_text:
        facilitator_notes_parts.append(f"Primary objectives from intake: {primary_objectives_text}")
    leadership_concerns_text = clean_text_value(
        intake_structured.get("leadership_concerns")
        or intake_structured.get("top_3_leadership_concerns")
        or intake_structured.get("executive_concerns")
    )
    if leadership_concerns_text:
        facilitator_notes_parts.append(f"Leadership concerns from intake: {leadership_concerns_text}")

    redline_topics = as_string_list(parsed_selections.get("topics_to_avoid_redlines", []))
    constraints = ["No live production system changes are performed during discussion."]
    if redline_topics:
        constraints.insert(0, f"Redline topics: {', '.join(redline_topics)}")

    scenario_obj: Dict[str, Any] = {
        "version": 1,
        "scenario": {
            "id": make_safe_scenario_id(manifest.get("case_id")),
            "title": f"{category} TTX — {client_alias}",
            "category": category,
            "duration_minutes": int(profile_obj.get("duration_minutes", 90)),
            "audiences": [str(a) for a in audience_roles] if audience_roles else ["Executive"],
            "summary": summary_text,
            "business_context": business_context,
            "threat_context": category_threat_context(category),
            "objectives": objectives,
            "assumptions": [
                "Facilitator controls exercise pace and timeboxes.",
                "Participants respond based on current documented processes.",
                "Unknown environment details are documented as follow-up items during facilitation.",
            ],
            "constraints": constraints,
            "success_criteria": [
                "Clear ownership and escalation decisions are articulated.",
                "Decision rationale is captured with required follow-up actions.",
            ],
            "pre_read": [
                "Review applicable incident response plans and escalation protocols.",
                "Review relevant security architecture and service ownership documentation.",
            ],
            "out_of_scope": [
                "Tool-specific implementation tasks outside tabletop decision flow.",
                "Forensic deep-dive artifacts not required for executive decision-making.",
            ],
            "facilitator_notes": "\n".join(facilitator_notes_parts),
        },
        "injects": [],
    }

    planned_injects: List[Tuple[int, int, int, Dict[str, Any]]] = []
    for module_index, module in enumerate(modules):
        if not isinstance(module, dict):
            continue
        slots = module.get("inject_slots", [])
        if not isinstance(slots, list):
            continue
        for slot_index, slot in enumerate(slots):
            if not isinstance(slot, dict):
                continue
            planned_injects.append((int(slot.get("t_plus_min", 0)), module_index, slot_index, slot))

    planned_injects.sort(key=lambda item: (item[0], item[1], item[2]))

    if len(planned_injects) > 99:
        print("ERROR: compiled scenario exceeds inject ID policy cap (max 99 injects for iNN format)", file=sys.stderr)
        return 1

    used_inject_ids: List[str] = []
    inject_id_map: List[Dict[str, Any]] = []
    trace_injects: List[Dict[str, Any]] = []
    for inject_counter, (t_plus_min, _module_index, _slot_index, slot) in enumerate(planned_injects, start=1):
            inject_id = slot.get("inject_id")
            if not isinstance(inject_id, str) or inject_id not in inject_registry:
                print(f"ERROR: inject_id '{inject_id}' from module map not found in inject banks", file=sys.stderr)
                return 1

            source_entry = inject_registry[inject_id]
            source_inject = source_entry.get("inject", {})
            source_bank = str(source_entry.get("source_bank", "unknown"))
            inject_payload = source_inject.get("inject", {})
            if not isinstance(inject_payload, dict):
                print(f"ERROR: inject '{inject_id}' missing inject payload", file=sys.stderr)
                return 1

            scenario_inject_id = f"i{inject_counter:02d}"

            base_audience = str(inject_payload.get("audience", "Executive"))
            audience_override = slot.get("audience_override")
            final_audience = str(audience_override) if isinstance(audience_override, str) and audience_override else base_audience

            base_delivery = str(inject_payload.get("delivery_method", "Facilitator briefing"))
            delivery_override = slot.get("delivery_override")
            final_delivery = str(delivery_override) if isinstance(delivery_override, str) and delivery_override else base_delivery

            source_marker = f"[LIBRARY_SOURCE] inject_id={inject_id} bank={source_bank}"
            base_notes = apply_placeholders(str(inject_payload.get("facilitator_notes", "")), placeholder_map).strip()
            facilitator_notes = f"{base_notes}\n{source_marker}" if base_notes else source_marker

            scenario_inject = {
                "id": scenario_inject_id,
                "t_plus_min": t_plus_min,
                "delivery_method": final_delivery,
                "audience": [final_audience],
                "participant_prompt": apply_placeholders(str(inject_payload.get("participant_prompt", "TBD")), placeholder_map),
                "expected_discussion": [apply_placeholders(str(x), placeholder_map) for x in inject_payload.get("expected_discussion", [])],
                "expected_decisions": [apply_placeholders(str(x), placeholder_map) for x in inject_payload.get("expected_decisions", [])],
                "evaluation_criteria": [apply_placeholders(str(x), placeholder_map) for x in inject_payload.get("evaluation_criteria", [])],
                "facilitator_notes": facilitator_notes,
                "evidence_refs": [str(x) for x in inject_payload.get("evidence_refs", [])],
            }
            scenario_obj["injects"].append(scenario_inject)
            used_inject_ids.append(inject_id)
            inject_id_map.append(
                {
                    "scenario_inject_id": scenario_inject_id,
                    "library_inject_id": inject_id,
                    "source_bank": source_bank,
                    "t_plus_min": t_plus_min,
                }
            )

            base_tests = client_test_profiles.get("base_tests", {}) if isinstance(client_test_profiles, dict) else {}
            per_inject = client_test_profiles.get("per_inject", {}) if isinstance(client_test_profiles, dict) else {}
            inject_overrides = per_inject.get(inject_id, {}) if isinstance(per_inject, dict) else {}
            ir_plan_capabilities = as_string_list(inject_overrides.get("ir_plan_capabilities")) or as_string_list(
                base_tests.get("ir_plan_capabilities")
            )
            crown_jewel_ids = as_string_list(inject_overrides.get("crown_jewel_ids")) or as_string_list(
                base_tests.get("crown_jewel_ids")
            )
            threat_ttps = as_string_list(inject_overrides.get("threat_ttps"))
            if not threat_ttps:
                source_tags = source_inject.get("tags", {}) if isinstance(source_inject, dict) else {}
                threat_ttps = as_string_list(source_tags.get("mitre_attack"))

            trace_injects.append(
                {
                    "scenario_inject_id": scenario_inject_id,
                    "source_bank": source_bank,
                    "library_inject_id": inject_id,
                    "tests": {
                        "ir_plan_capabilities": ir_plan_capabilities,
                        "crown_jewel_ids": crown_jewel_ids,
                        "threat_ttps": threat_ttps,
                    },
                }
            )

    scenario_issues = schema_validate_scenario(repo_root, scenario_obj)
    if scenario_issues:
        print("ERROR: compiled scenario failed schema validation", file=sys.stderr)
        for issue in scenario_issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    scenario_rel = manifest.get("scenario", {}).get("scenario_yaml_path") if isinstance(manifest.get("scenario"), dict) else None
    if not isinstance(scenario_rel, str) or not scenario_rel.strip():
        scenario_rel = "20_delivery/scenario.yaml"
    scenario_out_path = (case_dir / scenario_rel).resolve()

    if scenario_out_path.exists() and not args.force:
        print(f"ERROR: output exists; use --force to overwrite: {scenario_out_path}", file=sys.stderr)
        return 2

    write_yaml(scenario_out_path, scenario_obj)

    scenario_sha256 = hashlib.sha256(scenario_out_path.read_bytes()).hexdigest()
    trace_map_path = case_dir / "20_delivery" / "scenario_trace_map.json"
    trace_map_obj = {
        "scenario_yaml_sha256": scenario_sha256,
        "injects": trace_injects,
    }
    write_json(trace_map_path, trace_map_obj)

    snapshot_path = case_dir / "20_delivery" / "scenario_inputs_snapshot.json"
    snapshot_obj = {
        "intake_structured": intake_structured,
        "parsed_selections": parsed_selections,
        "placeholder_map": placeholder_map,
        "placeholder_map_used": placeholder_map,
        "category": category,
        "profile": profile,
        "module_map_filename": module_map_path.name,
        "inject_bank_filenames": [core_bank_path.name, category_bank_path.name],
        "file_fingerprints": {
            "case_manifest_json": file_fingerprint(manifest_path),
            "intake_structured_json": file_fingerprint(intake_structured_path),
            "intake_notes_md": file_fingerprint(intake_notes_path),
            "module_map": file_fingerprint(module_map_path),
            "inject_bank_core": file_fingerprint(core_bank_path),
            "inject_bank_category": file_fingerprint(category_bank_path),
        },
        "inject_ids_used": used_inject_ids,
        "inject_id_map": inject_id_map,
        "timestamp": now_utc_iso(),
    }
    write_json(snapshot_path, snapshot_obj)

    manifest["last_updated_at_utc"] = now_utc_iso()
    history = manifest.get("history")
    if isinstance(history, list):
        history.append(
            {
                "at_utc": now_utc_iso(),
                "event": "compile_scenario_from_library",
                "from_state": manifest.get("state"),
                "to_state": str(manifest.get("state", "")),
                "note": f"Compiled scenario from library using profile {profile} and category {category}.",
            }
        )
    write_json(manifest_path, manifest)

    print(f"Compiled scenario written: {scenario_out_path}")
    print(f"Scenario trace map written: {trace_map_path}")
    print(f"Inputs snapshot written: {snapshot_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
