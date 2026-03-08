#!/usr/bin/env python3
"""
Generate a deterministic After-Action Report (AAR) draft from:
- Scenario YAML (canonical content)
- scribe_runtime.json exported by TTX Studio

This does NOT call external AI. It creates a structured draft that a facilitator can edit.

SAFETY:
- By default, refuses to write outputs inside the git repo directory.
- Use --allow-in-repo ONLY for synthetic examples.

Outputs:
- after_action_report_draft.md

Example:
  python3 dfir_backend/ttx/scripts/build_aar_draft_from_runtime.py \
    --scenario-yaml /secure_storage/ttx/<case_id>/20_delivery/scenario.yaml \
    --runtime-json /secure_storage/ttx/<case_id>/30_outputs/ttx_logs/scribe_runtime.json \
    --out-dir /secure_storage/ttx/<case_id>/30_outputs/ttx_logs
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml  # type: ignore
except Exception:
    print("ERROR: Missing dependency PyYAML. Install with: pip install pyyaml", file=sys.stderr)
    raise


def repo_root_from_here() -> Path:
    # .../dfir_backend/ttx/scripts/build_aar_draft_from_runtime.py -> repo root is parents[3]
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
        raise ValueError("JSON root must be an object/mapping.")
    return obj


def bullets(items: Any) -> str:
    if not isinstance(items, list) or not items:
        return "- (not provided)\n"
    return "".join([f"- {str(x)}\n" for x in items])


def safe(s: Any) -> str:
    return str(s or "").strip()


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


def parse_text_items(value: Any) -> List[str]:
    if isinstance(value, str):
        return split_bullet_lines(value)
    if isinstance(value, list):
        out: List[str] = []
        for item in value:
            if isinstance(item, str):
                parsed = split_bullet_lines(item)
                if parsed:
                    out.extend(parsed)
                elif safe(item):
                    out.append(safe(item))
            elif safe(item):
                out.append(safe(item))
        return out
    return []


def parse_hotwash_lists(notes_hotwash: str) -> Tuple[List[str], List[str]]:
    strengths: List[str] = []
    gaps: List[str] = []
    mode = ""

    for raw in notes_hotwash.splitlines():
        line = raw.strip()
        if not line:
            continue

        if re.match(r"^strengths\s*:\s*$", line, re.IGNORECASE):
            mode = "strengths"
            continue
        if re.match(r"^gaps\s*:\s*$", line, re.IGNORECASE):
            mode = "gaps"
            continue

        if mode not in ("strengths", "gaps"):
            continue

        if line.startswith(("-", "*", "•")):
            item = line[1:].strip()
            if not item:
                continue
            if mode == "strengths" and len(strengths) < 5:
                strengths.append(item)
            elif mode == "gaps" and len(gaps) < 5:
                gaps.append(item)
        else:
            mode = ""

    return strengths, gaps


def timeframe_from_action(action: str) -> str:
    t = action.lower()
    if "[0]" in t or "(0)" in t or "0-day" in t:
        return "0"
    if "[30]" in t or "(30)" in t or "30-day" in t:
        return "30"
    if "[90]" in t or "(90)" in t or "90-day" in t:
        return "90"
    return ""


def timeframe_and_action_from_hotwash(action: str) -> Tuple[str, str]:
    if not action:
        return "", ""
    m = re.match(r"^\s*(0|30|90)\s*[:\-]\s*(.+)$", action)
    if m:
        return m.group(1), m.group(2).strip()
    m = re.match(r"^\s*[\[(]\s*(0|30|90)\s*[\])]\s*[:\-]?\s*(.+)$", action)
    if m:
        return m.group(1), m.group(2).strip()
    return "", action.strip()


def markdown_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    try:
        return json.dumps(value, ensure_ascii=False, indent=2)
    except Exception:
        return str(value)


def build_timeline_section(
    injects: List[Dict[str, Any]],
    notes_by_inject: Dict[str, Any],
    runtime: List[Dict[str, Any]],
    trace_by_inject: Optional[Dict[str, Dict[str, List[str]]]] = None,
) -> str:
    runtime_by_id = {safe(r.get("id")): r for r in runtime if isinstance(r, dict)}
    use_legacy_runtime = not bool(notes_by_inject) and bool(runtime_by_id)
    lines: List[str] = []
    lines.append("## Exercise timeline (inject-by-inject)\n\n")

    for inj in injects:
        iid = safe(inj.get("id"))
        planned = inj.get("t_plus_min", "")
        prompt = safe(inj.get("participant_prompt"))
        aud = inj.get("audience", [])
        aud_s = ", ".join([str(a) for a in aud]) if isinstance(aud, list) else safe(aud)

        r = runtime_by_id.get(iid, {}) if use_legacy_runtime else {}
        n = notes_by_inject.get(iid, {}) if isinstance(notes_by_inject, dict) else {}
        if not isinstance(n, dict):
            n = {}
        actual = safe(r.get("actual_t_plus_min"))
        discussion = safe(n.get("discussion")) or safe(r.get("discussion"))
        decisions = safe(n.get("decisions")) or safe(r.get("decisions"))
        actions = safe(n.get("actions")) or safe(r.get("actions"))
        questions = safe(n.get("questions")) or safe(r.get("questions"))
        evidence = safe(n.get("evidence")) or safe(r.get("evidence"))

        if actual:
            lines.append(f"### {iid} (Planned T+{planned} min; Actual T+{actual} min)\n\n")
        else:
            lines.append(f"### {iid} (Planned T+{planned} min)\n\n")
        lines.append(f"**Audience:** {aud_s}\n\n")
        lines.append("**Participant prompt:**\n")
        lines.append(f"{prompt}\n\n")
        if trace_by_inject is not None:
            trace_entry = trace_by_inject.get(iid, {}) if isinstance(trace_by_inject, dict) else {}
            capabilities = trace_entry.get("ir_plan_capabilities", []) if isinstance(trace_entry, dict) else []
            crown_jewels = trace_entry.get("crown_jewel_ids", []) if isinstance(trace_entry, dict) else []
            if not isinstance(capabilities, list):
                capabilities = []
            if not isinstance(crown_jewels, list):
                crown_jewels = []
            capabilities_text = ", ".join([safe(c) for c in capabilities if safe(c)]) or "(none mapped)"
            crown_jewels_text = ", ".join([safe(cj) for cj in crown_jewels if safe(cj)]) or "(none mapped)"
            lines.append("**Traceability:**\n")
            lines.append(f"- IR Plan capabilities tested: {capabilities_text}\n")
            lines.append(f"- Crown jewels affected: {crown_jewels_text}\n\n")
        lines.append("**Discussion:**\n")
        lines.append(f"{discussion or '(not captured)'}\n\n")
        lines.append("**Decisions:**\n")
        lines.append(f"{decisions or '(not captured)'}\n\n")
        lines.append("**Action items:**\n")
        lines.append(f"{actions or '(not captured)'}\n\n")
        lines.append("**Open questions:**\n")
        lines.append(f"{questions or '(not captured)'}\n\n")
        lines.append("**Evidence/Artifacts:**\n")
        lines.append(f"{evidence or '(not captured)'}\n\n")

    return "".join(lines)


def resolve_case_mode_paths(case_dir_arg: str) -> Tuple[Path, Path, Path, Dict[str, Any]]:
    case_dir = Path(case_dir_arg).expanduser().resolve()
    manifest_path = case_dir / "case_manifest.json"

    if not manifest_path.exists():
        raise FileNotFoundError(f"case_manifest.json not found: {manifest_path}")

    manifest = load_json(manifest_path)
    try:
        scenario_rel = str(manifest["scenario"]["scenario_yaml_path"])
        runtime_rel = str(manifest["outputs"]["scribe_runtime_json_path"])
    except Exception as e:
        raise ValueError("Manifest missing required scenario/output paths for AAR generation.") from e

    scenario_path = (case_dir / scenario_rel).resolve()
    runtime_path = (case_dir / runtime_rel).resolve()

    out_dir = (case_dir / "30_outputs").resolve()
    outputs = manifest.get("outputs", {})
    if isinstance(outputs, dict):
        aar_rel = str(outputs.get("aar_draft_path", "")).strip()
        if aar_rel:
            out_dir = (case_dir / aar_rel).resolve().parent

    return scenario_path, runtime_path, out_dir, manifest


def load_trace_map_if_present(case_dir: Optional[Path], scenario_path: Path) -> Tuple[Optional[Dict[str, Dict[str, List[str]]]], Dict[str, int]]:
    candidate_paths: List[Path] = []
    if case_dir is not None:
        candidate_paths.append((case_dir / "20_delivery" / "scenario_trace_map.json").resolve())
    if scenario_path.parent.name == "20_delivery":
        candidate_paths.append((scenario_path.parent / "scenario_trace_map.json").resolve())

    trace_path: Optional[Path] = None
    for path in candidate_paths:
        if path.exists():
            trace_path = path
            break

    if trace_path is None:
        return None, {}

    trace_obj = load_json(trace_path)
    injects_raw = trace_obj.get("injects", [])
    if not isinstance(injects_raw, list):
        return {}, {}

    trace_by_inject: Dict[str, Dict[str, List[str]]] = {}
    capability_counts: Dict[str, int] = {}
    for item in injects_raw:
        if not isinstance(item, dict):
            continue
        inject_id = safe(item.get("scenario_inject_id"))
        tests = item.get("tests", {})
        if not isinstance(tests, dict):
            tests = {}
        capabilities = tests.get("ir_plan_capabilities", [])
        crown_jewels = tests.get("crown_jewel_ids", [])
        if not isinstance(capabilities, list):
            capabilities = []
        if not isinstance(crown_jewels, list):
            crown_jewels = []

        clean_capabilities: List[str] = []
        for cap in capabilities:
            cap_id = safe(cap)
            if not cap_id:
                continue
            clean_capabilities.append(cap_id)
            capability_counts[cap_id] = capability_counts.get(cap_id, 0) + 1

        clean_crown_jewels = [safe(cj) for cj in crown_jewels if safe(cj)]
        trace_by_inject[inject_id] = {
            "ir_plan_capabilities": sorted(set(clean_capabilities)),
            "crown_jewel_ids": sorted(set(clean_crown_jewels)),
        }

    return trace_by_inject, capability_counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a deterministic AAR draft from TTX runtime exports.")
    parser.add_argument("--case-dir", help="Case folder containing case_manifest.json (preferred mode).")
    parser.add_argument("--scenario-yaml", help="Path to scenario YAML.")
    parser.add_argument("--runtime-json", help="Path to scribe_runtime.json exported by TTX Studio.")
    parser.add_argument("--out-dir", help="Output directory for the AAR draft.")
    parser.add_argument("--allow-in-repo", action="store_true", help="Allow writing outputs inside the repo (synthetic only).")
    args = parser.parse_args()

    repo_root = repo_root_from_here()

    case_dir_path: Optional[Path] = None
    manifest_obj: Dict[str, Any] = {}
    intake_structured_obj: Dict[str, Any] = {}
    if args.case_dir:
        try:
            scenario_path, runtime_path, out_dir, manifest_obj = resolve_case_mode_paths(args.case_dir)
            case_dir_path = Path(args.case_dir).expanduser().resolve()
            intake_structured_path = case_dir_path / "10_inputs" / "intake_structured.json"
            if intake_structured_path.exists():
                intake_structured_obj = load_json(intake_structured_path)
        except FileNotFoundError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 2
        except ValueError as e:
            print(f"ERROR: {e}", file=sys.stderr)
            return 2
    else:
        if not (args.scenario_yaml and args.runtime_json and args.out_dir):
            print(
                "ERROR: either --case-dir OR all of --scenario-yaml, --runtime-json, --out-dir must be provided.",
                file=sys.stderr,
            )
            return 2
        scenario_path = Path(args.scenario_yaml).expanduser().resolve()
        runtime_path = Path(args.runtime_json).expanduser().resolve()
        out_dir = Path(args.out_dir).expanduser().resolve()

    if not scenario_path.exists():
        print(f"ERROR: scenario-yaml not found: {scenario_path}", file=sys.stderr)
        return 2
    if not runtime_path.exists():
        print(f"ERROR: runtime-json not found: {runtime_path}", file=sys.stderr)
        return 2

    if not args.allow_in_repo and is_within(out_dir, repo_root):
        print(
            "ERROR: Refusing to write outputs inside the git repo directory.\n"
            f"- Repo root: {repo_root}\n"
            f"- Output dir: {out_dir}\n\n"
            "Write outputs to secure project storage outside git, or use --allow-in-repo ONLY for synthetic examples.",
            file=sys.stderr,
        )
        return 2

    scenario_obj = load_yaml(scenario_path)
    runtime_obj = load_json(runtime_path)
    trace_by_inject, capability_counts = load_trace_map_if_present(case_dir_path, scenario_path)

    scenario = scenario_obj.get("scenario", {})
    injects = scenario_obj.get("injects", [])
    if not isinstance(injects, list):
        injects = []

    decision_log = runtime_obj.get("decision_log", [])
    action_items = runtime_obj.get("action_items", [])
    comms_log = runtime_obj.get("comms_log", [])
    notes_by_inject = runtime_obj.get("notes_by_inject", {})
    if not isinstance(notes_by_inject, dict):
        notes_by_inject = {}
    has_notes_by_inject = bool(notes_by_inject)

    opening_script = safe(runtime_obj.get("opening_script"))
    session_notes = safe(runtime_obj.get("session_notes"))
    parking_lot = safe(runtime_obj.get("parking_lot"))
    hotwash_structured = runtime_obj.get("hotwash_structured")
    notes_hotwash = safe(runtime_obj.get("notes_hotwash"))
    hotwash_notes = safe(runtime_obj.get("hotwash_notes"))
    notes_global = safe(runtime_obj.get("notes_global"))
    inject_runtime = runtime_obj.get("inject_runtime", [])
    scoring = runtime_obj.get("scoring", {})
    if not isinstance(scoring, dict):
        scoring = {}

    decision_items: List[str] = []
    plan_items: List[str] = []
    injects_with_notes = 0
    for inj in injects:
        iid = safe(inj.get("id"))
        note = notes_by_inject.get(iid, {})
        if not isinstance(note, dict):
            continue
        has_any_note = False
        for d in split_bullet_lines(note.get("decisions")):
            decision_items.append(f"{d} (Inject {iid})")
            has_any_note = True
        for a in split_bullet_lines(note.get("actions")):
            plan_items.append(a)
            has_any_note = True
        for key in ("discussion", "questions", "evidence"):
            if safe(note.get(key)):
                has_any_note = True
        if has_any_note:
            injects_with_notes += 1

    hotwash_strengths: List[str] = []
    hotwash_gaps: List[str] = []
    hotwash_improvements: List[Tuple[str, str]] = []
    used_structured_hotwash = False
    if isinstance(hotwash_structured, dict):
        structured_strengths = parse_text_items(hotwash_structured.get("went_well"))
        structured_gaps = parse_text_items(hotwash_structured.get("gaps"))
        if structured_strengths or structured_gaps:
            hotwash_strengths = structured_strengths
            hotwash_gaps = structured_gaps
            used_structured_hotwash = True
        for item in parse_text_items(hotwash_structured.get("improvements")):
            timeframe, action_text = timeframe_and_action_from_hotwash(item)
            if action_text:
                hotwash_improvements.append((timeframe, action_text))
    if not used_structured_hotwash:
        hotwash_strengths, hotwash_gaps = parse_hotwash_lists(notes_hotwash)

    observed_decision_count = len(decision_items)
    observed_action_count = len(plan_items)
    if not has_notes_by_inject:
        if isinstance(decision_log, list):
            observed_decision_count = len([d for d in decision_log if isinstance(d, dict)])
        if isinstance(action_items, list):
            observed_action_count = len([a for a in action_items if isinstance(a, dict)])
        if isinstance(inject_runtime, list):
            injects_with_notes = len([r for r in inject_runtime if isinstance(r, dict)])

    case_id = safe(manifest_obj.get("case_id"))
    client_name = (
        safe(manifest_obj.get("client_name"))
        or safe(intake_structured_obj.get("client_organization"))
        or safe(intake_structured_obj.get("client_alias"))
        or "(not provided)"
    )
    handling_label = safe(manifest_obj.get("handling_label"))

    lines: List[str] = []
    lines.append("# After-Action Report (AAR) — Draft\n\n")
    lines.append("## Document control\n\n")
    lines.append(f"- Engagement / Case ID: {case_id}\n")
    lines.append(f"- Client / Organization: {client_name}\n")
    lines.append(f"- Exported at (UTC): {now_iso()}\n")
    lines.append(f"- Scenario ID: {safe(scenario.get('id'))}\n")
    lines.append(f"- Scenario title: {safe(scenario.get('title'))}\n")
    lines.append(f"- Scenario category: {safe(scenario.get('category'))}\n")
    lines.append(f"- Exercise duration (minutes): {safe(scenario.get('duration_minutes'))}\n")
    lines.append("- Prepared by (role): \n")
    lines.append(f"- Distribution: {handling_label}\n\n")

    lines.append("## Executive summary (client-facing)\n\n")
    lines.append("This AAR documents observed discussion and stated actions. It is not an audit and does not prove technical control effectiveness.\n\n")
    lines.append("**Overall readiness statement (facilitator to finalize):**\n\n")
    lines.append("- \n\n")
    lines.append("**Top strengths (from notes / logs):**\n\n")
    if hotwash_strengths:
        for item in hotwash_strengths:
            lines.append(f"- {item}\n")
        lines.append("\n")
    else:
        lines.append("- (not captured)\n\n")
    lines.append("**Top gaps/risks (from notes / logs):**\n\n")
    if hotwash_gaps:
        for item in hotwash_gaps:
            lines.append(f"- {item}\n")
        lines.append("\n")
    else:
        lines.append("- (not captured)\n\n")
    lines.append(f"Observed: {observed_decision_count} decisions, {observed_action_count} action items, {injects_with_notes} injects with notes captured.\n\n")

    lines.append("## Exercise scope and approach\n\n")
    lines.append("This tabletop exercise was discussion-based. No systems were accessed or tested. Findings are derived from observed discussion and stated actions.\n\n")
    lines.append("### Objectives (from scenario)\n\n")
    lines.append(bullets(scenario.get("objectives", [])))
    lines.append("\n### Assumptions (from scenario)\n\n")
    lines.append(bullets(scenario.get("assumptions", [])))
    lines.append("\n### Constraints / redlines (from scenario)\n\n")
    lines.append(bullets(scenario.get("constraints", [])))
    lines.append("\n")

    lines.append("## Scenario summary (client-facing)\n\n")
    lines.append(f"{safe(scenario.get('summary'))}\n\n")
    tc = safe(scenario.get("threat_context"))
    bc = safe(scenario.get("business_context"))
    if tc:
        lines.append("### Threat context\n\n")
        lines.append(f"{tc}\n\n")
    if bc:
        lines.append("### Business context\n\n")
        lines.append(f"{bc}\n\n")

    lines.append("## Key decisions observed (high level)\n\n")
    if decision_items:
        for d in decision_items:
            lines.append(f"- {d}\n")
    elif isinstance(decision_log, list) and decision_log:
        for d in decision_log:
            if not isinstance(d, dict):
                continue
            lines.append(f"- [{safe(d.get('time_utc'))}] {safe(d.get('decision'))} (Owner: {safe(d.get('owner_role'))})\n")
    else:
        lines.append("- (no decisions captured)\n")
    lines.append("\n")

    lines.append("## Scoring summary (internal by default)\n\n")
    scoring_dimensions = scoring.get("dimensions", []) if isinstance(scoring, dict) else []
    if isinstance(scoring_dimensions, list) and scoring_dimensions:
        lines.append("| Dimension | Score (1–5) | Evidence (2–4 examples) |\n")
        lines.append("|---|---:|---|\n")
        dim_label_by_id: Dict[str, str] = {}
        for dim in scoring_dimensions:
            if not isinstance(dim, dict):
                continue
            dim_id = safe(dim.get("id"))
            dim_label = safe(dim.get("label")) or dim_id
            if dim_id:
                dim_label_by_id[dim_id] = dim_label
            evidence = dim.get("evidence")
            evidence_text = markdown_text(evidence).replace("\n", "<br>")
            lines.append(f"| {dim_label.replace('|', '/')} | {safe(dim.get('score'))} | {evidence_text.replace('|', '/')} |\n")
        overall_avg = scoring.get("overall_avg")
        if overall_avg is not None and safe(overall_avg):
            lines.append(f"\nOverall readiness score: {safe(overall_avg)}\n")
        priority_gaps = scoring.get("priority_gaps")
        if isinstance(priority_gaps, list) and priority_gaps:
            lines.append("\nPriority gaps:\n")
            for gap in priority_gaps:
                gap_id = safe(gap)
                lines.append(f"- {dim_label_by_id.get(gap_id, gap_id)}\n")
        lines.append("\n")
    else:
        lines.append("If numeric scoring is required, apply dfir_backend/ttx/scoring_model.md and fill below.\n\n")
        lines.append("| Dimension | Score (1–5) | Evidence (2–4 examples) |\n")
        lines.append("|---|---:|---|\n")
        lines.append("| Detection & Awareness |  |  |\n")
        lines.append("| Decision-Making |  |  |\n")
        lines.append("| Communication |  |  |\n")
        lines.append("| Escalation & Authority |  |  |\n")
        lines.append("| Legal & Regulatory Awareness |  |  |\n")
        lines.append("| Documentation & Tracking |  |  |\n\n")

    lines.append("## Observations (strengths and gaps)\n\n")
    lines.append("### Strengths (facilitator to finalize)\n\n- \n\n")
    lines.append("### Gaps (facilitator to finalize)\n\n- \n\n")
    lines.append("### Impact (facilitator to finalize)\n\n- \n\n")
    lines.append("### Recommendations (facilitator to finalize)\n\n- \n\n")
    if capability_counts:
        lines.append("### Major recommendations (trace-mapped)\n\n")
        ranked_capabilities = sorted(capability_counts.items(), key=lambda kv: (-kv[1], kv[0]))
        for capability_id, _count in ranked_capabilities:
            lines.append(f"- Validate and strengthen IR plan capability **{capability_id}** across relevant runbooks and teams.\n")
            lines.append(f"  - Maps to: {capability_id}\n")
        lines.append("\n")

    lines.append(
        build_timeline_section(
            injects,
            notes_by_inject,
            inject_runtime if isinstance(inject_runtime, list) else [],
            trace_by_inject,
        )
    )

    lines.append("## Improvement plan (0 / 30 / 90 days)\n\n")
    lines.append("| Priority | Timeframe (0/30/90) | Recommendation / Action item | Owner (role) | Status | Notes |\n")
    lines.append("|---:|---|---|---|---|---|\n")
    combined_plan_items = [(timeframe_from_action(action), action) for action in plan_items]
    combined_plan_items.extend(hotwash_improvements)
    if combined_plan_items:
        for i, (timeframe, action) in enumerate(combined_plan_items, start=1):
            lines.append(f"| {i} | {timeframe} | {action.replace('|', '/')} |  |  |  |\n")
    elif isinstance(action_items, list) and action_items:
        for i, a in enumerate(action_items, start=1):
            if not isinstance(a, dict):
                continue
            lines.append(
                f"| {i} | {safe(a.get('timeframe_0_30_90'))} | {safe(a.get('action_item'))} | "
                f"{safe(a.get('owner_role'))} | {safe(a.get('status'))} | {safe(a.get('notes')).replace('|','/')} |\n"
            )
    else:
        lines.append("| 1 |  |  |  |  |  |\n")
    lines.append("\n")

    lines.append("## Optional: Recommended follow-on exercises / validation\n\n")
    lines.append("- Targeted tabletop for a specific audience (Exec-only / IT+Security / Legal+PR)\n")
    lines.append("- Compromise assessment recommendation based on visibility gaps observed\n")
    lines.append("- IR plan updates (escalation triggers, comms approvals, severity model)\n\n")

    lines.append("## Appendices (optional)\n\n")
    if opening_script:
        lines.append("### Opening script used\n\n")
        lines.append(opening_script + "\n\n")
    if notes_global:
        lines.append("### Global notes\n\n")
        lines.append(notes_global + "\n\n")
    if session_notes:
        lines.append("### Session notes\n\n")
        lines.append(session_notes + "\n\n")
    if parking_lot:
        lines.append("### Parking lot\n\n")
        lines.append(parking_lot + "\n\n")
    if isinstance(comms_log, list) and comms_log:
        lines.append("### Communications log (optional)\n\n")
        for c in comms_log:
            if not isinstance(c, dict):
                continue
            lines.append(f"- [{safe(c.get('time_utc'))}] {safe(c.get('audience'))}: {safe(c.get('purpose'))}\n")
        lines.append("\n")
    if hotwash_structured is not None:
        lines.append("### Hotwash (structured)\n\n")
        lines.append(markdown_text(hotwash_structured) + "\n\n")
    if notes_hotwash:
        lines.append("### Hotwash notes\n\n")
        lines.append(notes_hotwash + "\n\n")
    if hotwash_notes:
        lines.append("### Hotwash notes\n\n")
        lines.append(hotwash_notes + "\n\n")

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "after_action_report_draft.md"
    out_path.write_text("".join(lines), encoding="utf-8")

    print(f"Wrote AAR draft: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
