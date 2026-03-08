#!/usr/bin/env python3
"""
Deterministic IR plan mapper.

Writes 10_inputs/ir_plan_profile.json from either:
- interactive answers, or
- tagged excerpts file.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


ALLOWED_ROLES = ["incident_commander", "legal", "comms", "IT", "exec_sponsor"]
ALLOWED_EXTERNAL_PARTIES = ["ir_retainer", "pr_firm", "cyber_insurance"]


def prompt_required(text: str) -> str:
    while True:
        value = input(f"{text}: ").strip()
        if value:
            return value
        print("Value is required.")


def prompt_optional(text: str, default: str = "") -> str:
    raw = input(f"{text}" + (f" [{default}]" if default else "") + ": ").strip()
    if raw:
        return raw
    return default


def prompt_int(text: str, default: int) -> int:
    while True:
        raw = prompt_optional(text, str(default))
        if raw.isdigit():
            return int(raw)
        print("Enter a non-negative integer.")


def prompt_bool(text: str, default: bool) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    raw = input(f"{text} {suffix}: ").strip().lower()
    if not raw:
        return default
    return raw in ("y", "yes", "true", "1")


def parse_tag_blocks(text: str) -> Dict[str, List[str]]:
    blocks: Dict[str, List[str]] = {}
    current = ""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]") and not stripped.startswith("[/"):
            current = stripped[1:-1]
            blocks[current] = []
            continue
        if stripped.startswith("[/") and stripped.endswith("]"):
            current = ""
            continue
        if current:
            blocks[current].append(line.rstrip())
    return blocks


def build_from_tagged_excerpts(path: Path) -> Dict[str, Any]:
    blocks = parse_tag_blocks(path.read_text(encoding="utf-8"))

    severity_levels: List[Dict[str, str]] = []
    for line in blocks.get("severity_levels", []):
        parts = [p.strip() for p in line.split("|", 1)]
        if len(parts) == 2 and parts[0] and parts[1]:
            severity_levels.append({"name": parts[0], "definition": parts[1]})

    roles_and_contacts: Dict[str, Dict[str, str]] = {role: {"name": "", "contact": ""} for role in ALLOWED_ROLES}
    for line in blocks.get("roles_and_contacts", []):
        parts = [p.strip() for p in line.split("|", 2)]
        if len(parts) == 3 and parts[0] in roles_and_contacts:
            roles_and_contacts[parts[0]] = {"name": parts[1], "contact": parts[2]}

    escalation_timeboxes: Dict[str, int] = {
        "notify_legal_within_minutes": 60,
        "notify_exec_sponsor_within_minutes": 120,
        "declare_incident_within_minutes": 30,
    }
    for line in blocks.get("escalation_timeboxes", []):
        parts = [p.strip() for p in line.split("|", 1)]
        if len(parts) == 2 and parts[0] in escalation_timeboxes and parts[1].isdigit():
            escalation_timeboxes[parts[0]] = int(parts[1])

    external_parties: Dict[str, Dict[str, str]] = {
        party: {"provider": "", "contact": "", "policy_or_contract_id": ""} for party in ALLOWED_EXTERNAL_PARTIES
    }
    for line in blocks.get("external_parties", []):
        parts = [p.strip() for p in line.split("|", 3)]
        if len(parts) == 4 and parts[0] in external_parties:
            external_parties[parts[0]] = {
                "provider": parts[1],
                "contact": parts[2],
                "policy_or_contract_id": parts[3],
            }

    channels: Dict[str, str] = {"war_room_tool": "", "incident_ticketing": ""}
    for line in blocks.get("communications_channels", []):
        parts = [p.strip() for p in line.split("|", 1)]
        if len(parts) == 2 and parts[0] in channels:
            channels[parts[0]] = parts[1]

    regulatory: Dict[str, Any] = {"applicable": False, "deadline_hours": None, "notes": ""}
    for line in blocks.get("regulatory_notification", []):
        parts = [p.strip() for p in line.split("|", 1)]
        if len(parts) != 2:
            continue
        if parts[0] == "applicable":
            regulatory["applicable"] = parts[1].lower() in ("y", "yes", "true", "1")
        elif parts[0] == "deadline_hours":
            regulatory["deadline_hours"] = int(parts[1]) if parts[1].isdigit() else None
        elif parts[0] == "notes":
            regulatory["notes"] = parts[1]

    return {
        "severity_levels": severity_levels,
        "roles_and_contacts": roles_and_contacts,
        "escalation_timeboxes": escalation_timeboxes,
        "external_parties": external_parties,
        "communications_channels": channels,
        "regulatory_notification": regulatory,
    }


def build_from_answers() -> Dict[str, Any]:
    print("IR Plan Mapper Wizard (deterministic)")
    print("------------------------------------")

    severity_count = prompt_int("Number of severity levels", 3)
    severity_levels: List[Dict[str, str]] = []
    for idx in range(1, severity_count + 1):
        name = prompt_required(f"severity_levels[{idx}].name")
        definition = prompt_required(f"severity_levels[{idx}].definition")
        severity_levels.append({"name": name, "definition": definition})

    roles_and_contacts: Dict[str, Dict[str, str]] = {}
    for role in ALLOWED_ROLES:
        roles_and_contacts[role] = {
            "name": prompt_optional(f"roles_and_contacts.{role}.name"),
            "contact": prompt_optional(f"roles_and_contacts.{role}.contact"),
        }

    escalation_timeboxes = {
        "notify_legal_within_minutes": prompt_int("escalation_timeboxes.notify_legal_within_minutes", 60),
        "notify_exec_sponsor_within_minutes": prompt_int("escalation_timeboxes.notify_exec_sponsor_within_minutes", 120),
        "declare_incident_within_minutes": prompt_int("escalation_timeboxes.declare_incident_within_minutes", 30),
    }

    external_parties: Dict[str, Dict[str, str]] = {}
    for party in ALLOWED_EXTERNAL_PARTIES:
        external_parties[party] = {
            "provider": prompt_optional(f"external_parties.{party}.provider"),
            "contact": prompt_optional(f"external_parties.{party}.contact"),
            "policy_or_contract_id": prompt_optional(f"external_parties.{party}.policy_or_contract_id"),
        }

    communications_channels = {
        "war_room_tool": prompt_optional("communications_channels.war_room_tool"),
        "incident_ticketing": prompt_optional("communications_channels.incident_ticketing"),
    }

    reg_applicable = prompt_bool("regulatory_notification.applicable", False)
    reg_deadline = None
    if reg_applicable:
        reg_deadline = prompt_int("regulatory_notification.deadline_hours", 72)
    reg_notes = prompt_optional("regulatory_notification.notes")

    return {
        "severity_levels": severity_levels,
        "roles_and_contacts": roles_and_contacts,
        "escalation_timeboxes": escalation_timeboxes,
        "external_parties": external_parties,
        "communications_channels": communications_channels,
        "regulatory_notification": {
            "applicable": reg_applicable,
            "deadline_hours": reg_deadline,
            "notes": reg_notes,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build deterministic 10_inputs/ir_plan_profile.json.")
    parser.add_argument("--case-dir", required=True, help="Case root directory.")
    parser.add_argument(
        "--tagged-excerpts",
        default="",
        help="Optional tagged excerpts file. If provided, wizard is skipped and tags are parsed.",
    )
    args = parser.parse_args()

    case_dir = Path(args.case_dir).expanduser().resolve()
    output_path = case_dir / "10_inputs" / "ir_plan_profile.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if args.tagged_excerpts:
        profile = build_from_tagged_excerpts(Path(args.tagged_excerpts).expanduser().resolve())
    else:
        profile = build_from_answers()

    output_path.write_text(json.dumps(profile, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
