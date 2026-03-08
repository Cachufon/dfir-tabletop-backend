#!/usr/bin/env python3
"""Deterministically tailor base scenario text fields using intake_structured.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml  # type: ignore
except Exception:
    print("ERROR: Missing dependency PyYAML. Install with: pip install pyyaml", file=sys.stderr)
    raise


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> Dict[str, Any]:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("scenario YAML root must be a mapping")
    return loaded


def dump_yaml(path: Path, obj: Dict[str, Any]) -> None:
    path.write_text(yaml.safe_dump(obj, sort_keys=False, allow_unicode=True), encoding="utf-8")


def as_string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        out: List[str] = []
        for item in value:
            s = str(item).strip()
            if s:
                out.append(s)
        return out
    if isinstance(value, str):
        s = value.strip()
        return [s] if s else []
    return []


def append_lines(base: str, heading: str, values: List[str]) -> str:
    if not values:
        return base
    block = f"{heading}: " + "; ".join(values)
    if not base.strip():
        return block
    return base.rstrip() + "\n" + block


def append_objectives(existing: List[str], additions: List[str]) -> List[str]:
    out = list(existing)
    seen = set(existing)
    for item in additions:
        if item not in seen:
            out.append(item)
            seen.add(item)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Tailor base scenario text fields from intake_structured.json")
    parser.add_argument("--case-dir", required=True, help="Case directory path")
    args = parser.parse_args()

    case_dir = Path(args.case_dir).expanduser().resolve()
    scenario_path = case_dir / "20_delivery" / "scenario.yaml"
    intake_path = case_dir / "10_inputs" / "intake_structured.json"

    if not scenario_path.exists():
        print(f"ERROR: scenario.yaml not found: {scenario_path}", file=sys.stderr)
        return 2

    obj = load_yaml(scenario_path)
    scenario = obj.get("scenario")
    if not isinstance(scenario, dict):
        print("ERROR: scenario.yaml missing top-level 'scenario' mapping", file=sys.stderr)
        return 2

    original_injects = json.dumps(obj.get("injects"), sort_keys=True)

    intake: Dict[str, Any] = {}
    if intake_path.exists():
        loaded_intake = load_json(intake_path)
        if isinstance(loaded_intake, dict):
            intake = loaded_intake

    crown_jewels = as_string_list(intake.get("crown_jewels"))
    primary_objectives = as_string_list(intake.get("primary_objectives"))
    outcomes_to_avoid = as_string_list(intake.get("high_impact_outcomes_to_avoid"))
    leadership_concerns = as_string_list(intake.get("leadership_concerns"))
    if not leadership_concerns:
        leadership_concerns = as_string_list(intake.get("top_3_leadership_concerns"))

    business_context = str(scenario.get("business_context", "") or "")
    facilitator_notes = str(scenario.get("facilitator_notes", "") or "")

    if crown_jewels:
        if business_context.strip():
            scenario["business_context"] = append_lines(business_context, "Crown jewels", crown_jewels)
        else:
            scenario["facilitator_notes"] = append_lines(facilitator_notes, "Crown jewels", crown_jewels)
            facilitator_notes = str(scenario.get("facilitator_notes", "") or "")

    existing_objectives = as_string_list(scenario.get("objectives"))
    scenario["objectives"] = append_objectives(existing_objectives, primary_objectives)

    if outcomes_to_avoid:
        scenario["facilitator_notes"] = append_lines(str(scenario.get("facilitator_notes", "") or ""), "Outcomes to avoid", outcomes_to_avoid)
    if leadership_concerns:
        scenario["facilitator_notes"] = append_lines(str(scenario.get("facilitator_notes", "") or ""), "Leadership concerns", leadership_concerns)

    for field in ("summary", "business_context", "facilitator_notes"):
        if field in scenario and scenario[field] is None:
            scenario[field] = ""

    new_injects = json.dumps(obj.get("injects"), sort_keys=True)
    if new_injects != original_injects:
        print("ERROR: injects changed during tailoring; refusing to write.", file=sys.stderr)
        return 2

    dump_yaml(scenario_path, obj)
    print(f"SUCCESS: tailored scenario text fields in {scenario_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
