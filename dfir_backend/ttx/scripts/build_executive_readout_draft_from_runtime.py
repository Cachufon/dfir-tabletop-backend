#!/usr/bin/env python3
"""
Generate a deterministic executive readout draft from:
- Scenario YAML
- scribe_runtime.json exported by TTX Studio
- Optional case_manifest.json

This does NOT call external AI.

SAFETY:
- By default, refuses to write outputs inside the git repo directory.
- Use --allow-in-repo ONLY for synthetic examples.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

try:
    import yaml  # type: ignore
except Exception:
    print("ERROR: Missing dependency PyYAML. Install with: pip install pyyaml", file=sys.stderr)
    raise


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[3]


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load_yaml(path: Path) -> Dict[str, Any]:
    obj = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError("Scenario YAML root must be an object/mapping.")
    return obj


def load_json(path: Path) -> Dict[str, Any]:
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, dict):
        raise ValueError(f"JSON root must be an object/mapping: {path}")
    return obj


def safe(value: Any) -> str:
    return str(value or "").strip()


def split_bullet_lines(text: Any) -> List[str]:
    if not isinstance(text, str):
        return []
    out: List[str] = []
    for raw in text.splitlines():
        item = raw.strip()
        if not item:
            continue
        if item.startswith("-") or item.startswith("*") or item.startswith("•"):
            item = item[1:].strip()
        if item:
            out.append(item)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic executive readout draft from TTX runtime exports.")
    parser.add_argument("--scenario-yaml", required=True, help="Path to scenario YAML.")
    parser.add_argument("--runtime-json", required=True, help="Path to scribe_runtime.json exported by TTX Studio.")
    parser.add_argument("--out-path", required=True, help="Output path for executive readout markdown.")
    parser.add_argument("--case-manifest", default="", help="Optional path to case_manifest.json.")
    parser.add_argument("--allow-in-repo", action="store_true", help="Allow writing outputs inside the repo (synthetic only).")
    parser.add_argument("--force", action="store_true", help="Overwrite --out-path if it already exists.")
    args = parser.parse_args()

    repo_root = repo_root_from_here()

    scenario_path = Path(args.scenario_yaml).expanduser().resolve()
    runtime_path = Path(args.runtime_json).expanduser().resolve()
    out_path = Path(args.out_path).expanduser().resolve()

    if not scenario_path.exists():
        print(f"ERROR: scenario-yaml not found: {scenario_path}", file=sys.stderr)
        return 2
    if not runtime_path.exists():
        print(f"ERROR: runtime-json not found: {runtime_path}", file=sys.stderr)
        return 2

    if args.case_manifest.strip():
        case_manifest_path = Path(args.case_manifest).expanduser().resolve()
        if not case_manifest_path.exists():
            print(f"ERROR: case-manifest not found: {case_manifest_path}", file=sys.stderr)
            return 2
    else:
        case_manifest_path = None

    if out_path.exists() and not args.force:
        print(f"ERROR: out-path already exists: {out_path}\nUse --force to overwrite.", file=sys.stderr)
        return 2

    if not args.allow_in_repo and is_within(out_path, repo_root):
        print(
            "ERROR: Refusing to write outputs inside the git repo directory.\n"
            f"- Repo root: {repo_root}\n"
            f"- Output path: {out_path}\n\n"
            "Write outputs to secure project storage outside git, or use --allow-in-repo ONLY for synthetic examples.",
            file=sys.stderr,
        )
        return 2

    scenario_obj = load_yaml(scenario_path)
    runtime_obj = load_json(runtime_path)
    case_manifest: Dict[str, Any] = load_json(case_manifest_path) if case_manifest_path else {}

    scenario = scenario_obj.get("scenario", {})
    if not isinstance(scenario, dict):
        scenario = {}
    injects = scenario_obj.get("injects", [])
    if not isinstance(injects, list):
        injects = []

    notes_by_inject = runtime_obj.get("notes_by_inject", {})
    if not isinstance(notes_by_inject, dict):
        notes_by_inject = {}

    decision_items: List[str] = []
    action_items: List[str] = []
    open_questions_count = 0

    for inj in injects:
        if not isinstance(inj, dict):
            continue
        iid = safe(inj.get("id"))
        note = notes_by_inject.get(iid, {})
        if not isinstance(note, dict):
            continue

        for entry in split_bullet_lines(note.get("decisions")):
            decision_items.append(f"{entry} (Inject {iid})")

        for entry in split_bullet_lines(note.get("actions")):
            action_items.append(f"{entry} (Inject {iid})")

        open_questions_count += len(split_bullet_lines(note.get("questions")))

    case_id = safe(case_manifest.get("case_id")) or safe(runtime_obj.get("case_id")) or safe(scenario.get("id"))
    client_name = safe(case_manifest.get("client_name"))
    timezone_name = safe(case_manifest.get("timezone")) or safe(runtime_obj.get("timezone"))
    duration_minutes = safe(case_manifest.get("duration_minutes")) or safe(scenario.get("duration_minutes"))

    lines: List[str] = []
    lines.append("# Executive Readout — Draft\n\n")

    lines.append("## Document control\n\n")
    lines.append(f"- Engagement / Case ID: {case_id or '(not captured)'}\n")
    lines.append(f"- Client / Organization: {client_name or '(not captured)'}\n")
    lines.append(f"- Scenario ID: {safe(scenario.get('id')) or '(not captured)'}\n")
    lines.append(f"- Scenario title: {safe(scenario.get('title')) or '(not captured)'}\n")
    lines.append(f"- Timezone: {timezone_name or '(not captured)'}\n")
    lines.append(f"- Exercise duration (minutes): {duration_minutes or '(not captured)'}\n")
    lines.append(f"- Exported at (UTC): {now_iso()}\n")
    lines.append("\n")

    observed_line = (
        f"Observed: {len(decision_items)} decisions, {len(action_items)} action items, "
        f"{open_questions_count} open questions captured."
    )

    lines.append("## Executive summary\n\n")
    lines.append(f"- {observed_line}\n")
    lines.append("- (not captured)\n")
    lines.append("- (not captured)\n\n")

    lines.append("## What went well\n\n")
    lines.append(f"- {observed_line}\n")
    lines.append("- (not captured)\n")
    lines.append("- (not captured)\n\n")

    lines.append("## Key risks/gaps\n\n")
    lines.append(f"- {observed_line} Why it matters: decision and action tracking clarity drives follow-through.\n")
    lines.append("- (not captured) Why it matters: (not captured)\n")
    lines.append("- (not captured) Why it matters: (not captured)\n\n")

    lines.append("## Decisions that mattered\n\n")
    if decision_items:
        for entry in decision_items:
            lines.append(f"- {entry}\n")
    else:
        lines.append("- (not captured)\n")
    lines.append("\n")

    lines.append("## Recommended improvements\n\n")
    lines.append("| Timeframe (0/30/90) | Recommendation | Owner role | Effort (S/M/L) |\n")
    lines.append("|---|---|---|---|\n")
    if action_items:
        for entry in action_items:
            lines.append(f"| 30 | {entry.replace('|', '/')} | (not captured) | M |\n")
    else:
        lines.append("| (not captured) | (not captured) | (not captured) | (not captured) |\n")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("".join(lines), encoding="utf-8")

    print(f"Wrote executive readout draft: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
