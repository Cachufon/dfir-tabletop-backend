#!/usr/bin/env python3
"""Quick intake wizard for required foundational fields."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def prompt(text: str, default: str = "") -> str:
    if default:
        value = input(f"{text} [{default}]: ").strip()
        return value if value else default
    return input(f"{text}: ").strip()


def split_csv_or_tbd(raw: str) -> List[str]:
    items = [item.strip() for item in raw.split(",") if item.strip()]
    return items if items else ["TBD"]


def parse_primary_objectives() -> List[str]:
    raw = input("Primary objectives (comma-separated or leave blank for multi-line): ").strip()
    if raw:
        return split_csv_or_tbd(raw)

    print("Enter primary objectives (one per line). Submit an empty line to finish.")
    lines: List[str] = []
    while True:
        line = input("- ").strip()
        if not line:
            break
        lines.append(line)
    return lines if lines else ["TBD"]


def parse_critical_services() -> List[str]:
    raw = input("Critical services (comma-separated or leave blank for multi-line): ").strip()
    if raw:
        return split_csv_or_tbd(raw)

    print("Enter critical services (one per line). Submit an empty line to finish.")
    lines: List[str] = []
    while True:
        line = input("- ").strip()
        if not line:
            break
        lines.append(line)
    return lines if lines else ["TBD"]


def read_taxonomy_categories(repo_root: Path) -> List[str]:
    taxonomy_path = repo_root / "dfir_backend" / "ttx" / "scenario_taxonomy.md"
    if not taxonomy_path.exists():
        return []
    categories: List[str] = []
    for line in taxonomy_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("## ") and not stripped.startswith("## Category naming rules"):
            category = stripped.replace("## ", "", 1).strip()
            if category:
                categories.append(category)
    return categories


def normalize_value(value: str) -> str:
    return value.strip() or "TBD"


def parse_preferred_scenario_category(categories: List[str], default: str) -> str:
    allowed_categories = categories + ["No preference"]
    canonical_lookup = {category.lower(): category for category in allowed_categories}

    for attempt in range(1, 4):
        raw_value = prompt("Preferred scenario category", default)
        candidate = raw_value.strip()

        if candidate.isdigit():
            selected_index = int(candidate)
            if 1 <= selected_index <= len(allowed_categories):
                return allowed_categories[selected_index - 1]
        else:
            canonical = canonical_lookup.get(candidate.lower())
            if canonical:
                return canonical

        print(
            "ERROR: Invalid preferred scenario category. Enter a listed number or category name (or 'No preference').",
            file=sys.stderr,
        )
        if attempt == 3:
            print("ERROR: Maximum attempts reached for preferred scenario category.", file=sys.stderr)
            raise ValueError("Maximum attempts reached")

    raise ValueError("Maximum attempts reached")


def render_top_section(data: Dict[str, Any]) -> str:
    objectives = data["primary_objectives"]
    crown_jewels = data["crown_jewels"]
    outcomes = data["high_impact_outcomes_to_avoid"]
    concerns = data["top_3_leadership_concerns"]

    lines = [
        "## Minimum required (auto-filled)",
        "",
        f"- Client / Organization: {data['client_organization']}",
        f"- Timezone: {data['timezone']}",
        f"- Delivery format: {data['delivery_format']}",
        f"- Duration: {data['duration_minutes']}",
        f"- Desired audience roles: {', '.join(data['desired_audience_roles'])}",
        f"- Preferred scenario category: {data['preferred_scenario_category']}",
        f"- Updated at (UTC): {data['updated_at_utc']}",
        "",
        "### Primary objectives",
    ]
    lines.extend([f"- {item}" for item in objectives])
    lines.append("")
    lines.append("### Crown jewels")
    lines.extend([f"- {item}" for item in crown_jewels])
    lines.append("")
    lines.append("### High-impact outcomes to avoid")
    lines.extend([f"- {item}" for item in outcomes])
    lines.append("")
    lines.append("### Top 3 leadership concerns")
    lines.extend([f"- {item}" for item in concerns])
    lines.append("")
    return "\n".join(lines)


def replace_or_insert_top_section(intake_notes_path: Path, section_text: str, force: bool) -> None:
    if not intake_notes_path.exists():
        intake_notes_path.parent.mkdir(parents=True, exist_ok=True)
        intake_notes_path.write_text(section_text + "\n", encoding="utf-8")
        return

    original = intake_notes_path.read_text(encoding="utf-8")
    lines = original.splitlines()
    marker = "## Minimum required (auto-filled)"

    start_idx = None
    for idx, line in enumerate(lines):
        if line.strip() == marker:
            start_idx = idx
            break

    if start_idx is None:
        intake_notes_path.write_text(section_text + "\n\n" + original.lstrip("\n"), encoding="utf-8")
        return

    if not force:
        raise RuntimeError(
            "Minimum required (auto-filled) section already exists in intake_notes.md. Re-run with --force to rewrite it."
        )

    end_idx = len(lines)
    for idx in range(start_idx + 1, len(lines)):
        if lines[idx].startswith("## "):
            end_idx = idx
            break

    prefix = lines[:start_idx]
    suffix = lines[end_idx:]
    new_lines: List[str] = []
    new_lines.extend(prefix)
    if new_lines and new_lines[-1].strip():
        new_lines.append("")
    new_lines.extend(section_text.splitlines())
    if suffix:
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        new_lines.extend(suffix)
    intake_notes_path.write_text("\n".join(new_lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run quick intake wizard and write structured intake fields.")
    parser.add_argument("--case-dir", required=True, help="Case folder containing case_manifest.json")
    parser.add_argument("--force", action="store_true", help="Overwrite intake_structured.json and rewrite the auto-filled minimum required section.")
    args = parser.parse_args()

    case_dir = Path(args.case_dir).expanduser().resolve()
    manifest_path = case_dir / "case_manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: case_manifest.json not found: {manifest_path}", file=sys.stderr)
        return 2

    manifest = read_json(manifest_path)

    client_default = str(manifest.get("client_name") or manifest.get("case_id") or "").strip()
    timezone_default = str(manifest.get("timezone") or "").strip()
    duration_default = manifest.get("duration_minutes") or 90

    audience_default = ""
    audience_roles = manifest.get("audience_roles")
    if isinstance(audience_roles, list):
        audience_default = ", ".join(str(role).strip() for role in audience_roles if str(role).strip())

    scenario = manifest.get("scenario")
    scenario_category = ""
    if isinstance(scenario, dict):
        scenario_category = str(scenario.get("category") or "").strip()

    repo_root = Path(__file__).resolve().parents[3]
    categories = read_taxonomy_categories(repo_root)
    preferred_category_default = scenario_category or "No preference"
    if preferred_category_default.lower() not in {category.lower() for category in (categories + ["No preference"])}:
        preferred_category_default = "No preference"

    print("Quick Intake Wizard — foundational fields only")
    print("------------------------------------------------")

    client_organization = normalize_value(prompt("Client / Organization (alias ok)", client_default))
    timezone = normalize_value(prompt("Timezone", timezone_default))

    delivery_raw = prompt("Delivery format (Virtual/In-person)", "Virtual")
    delivery_format = normalize_value(delivery_raw)
    if delivery_format.lower() == "in-person":
        delivery_format = "In-person"
    elif delivery_format.lower() == "virtual":
        delivery_format = "Virtual"

    duration_raw = prompt("Duration minutes (60/90/120)", str(duration_default))
    duration_minutes = duration_raw.strip()
    if duration_minutes not in {"60", "90", "120"}:
        print("ERROR: Duration minutes must be one of: 60, 90, 120", file=sys.stderr)
        return 2

    desired_audience_roles = split_csv_or_tbd(prompt("Desired audience roles (comma-separated)", audience_default))
    primary_objectives = parse_primary_objectives()
    critical_services = parse_critical_services()
    crown_jewels = split_csv_or_tbd(prompt("Crown jewels (comma-separated)"))
    high_impact_outcomes_to_avoid = split_csv_or_tbd(prompt("High-impact outcomes to avoid (comma-separated)"))
    top_3_leadership_concerns = split_csv_or_tbd(prompt("Top 3 leadership concerns (comma-separated)"))

    if categories:
        print("\nPreferred scenario category options:")
        for idx, category in enumerate(categories, start=1):
            print(f"{idx}) {category}")
        print(f"{len(categories)+1}) No preference")

    try:
        preferred_scenario_category = parse_preferred_scenario_category(categories, preferred_category_default)
    except ValueError:
        return 2

    intake_structured = {
        "client_organization": client_organization,
        "client_alias": client_organization,
        "timezone": timezone,
        "delivery_format": delivery_format,
        "duration_minutes": int(duration_minutes),
        "desired_audience_roles": desired_audience_roles,
        "audience_roles": desired_audience_roles,
        "primary_objectives": primary_objectives,
        "critical_services": critical_services,
        "crown_jewels": crown_jewels,
        "high_impact_outcomes_to_avoid": high_impact_outcomes_to_avoid,
        "top_3_leadership_concerns": top_3_leadership_concerns,
        "leadership_concerns": top_3_leadership_concerns,
        "preferred_scenario_category": preferred_scenario_category,
        "preferred_category": preferred_scenario_category,
        "updated_at_utc": now_iso(),
    }

    structured_path = case_dir / "10_inputs" / "intake_structured.json"
    if structured_path.exists() and not args.force:
        print(f"ERROR: {structured_path} already exists. Re-run with --force to overwrite.", file=sys.stderr)
        return 2

    write_json(structured_path, intake_structured)

    intake_notes_path = case_dir / "10_inputs" / "intake_notes.md"
    try:
        replace_or_insert_top_section(intake_notes_path, render_top_section(intake_structured), args.force)
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"Wrote: {structured_path}")
    print(f"Updated: {intake_notes_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
