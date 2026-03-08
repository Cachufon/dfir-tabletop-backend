#!/usr/bin/env python3
"""
Build a Tabletop Exercise (TTX) package from a scenario YAML.

This script generates human-usable artifacts for delivery:
- scenario.yaml (copy of input)
- sitman.md (participant-facing Situation Manual)
- facilitator_packet.md (facilitator run-sheet + inject details)
- participant_guide.md (short participant pre-read)
- scribe_logs.md (tables for inject/decision/action logging)
- package_manifest.md (what was generated + handling rules)

IMPORTANT DATA HANDLING RULE:
- Client-tailored outputs should be written to secure project storage OUTSIDE git.
- By default, this script BLOCKS writing outputs inside the repo directory.
- Use --allow-in-repo ONLY for synthetic examples.

Dependencies:
- PyYAML
- jsonschema

Install:
  pip install pyyaml jsonschema

Example:
  python3 dfir_backend/ttx/scripts/build_ttx_package_from_yaml.py \
    --input /secure_storage/ttx/TTX-20260210-CLIENT-IDENTITY/scenario.yaml \
    --out-dir /secure_storage/ttx/TTX-20260210-CLIENT-IDENTITY/20_delivery/ttx_package
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

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


@dataclass
class ValidationIssue:
    message: str


def repo_root_from_here() -> Path:
    # .../dfir_backend/ttx/scripts/build_ttx_package_from_yaml.py -> repo root is parents[3]
    return Path(__file__).resolve().parents[3]


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def read_taxonomy_categories(taxonomy_path: Path) -> List[str]:
    """
    Extract canonical categories from dfir_backend/ttx/scenario_taxonomy.md.

    Convention:
    - Categories are Markdown H2 headings: lines starting with "## "
    """
    categories: List[str] = []
    for line in taxonomy_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("## Category naming rules"):
            continue
        if line.startswith("## "):
            cat = line.replace("## ", "", 1).strip()
            if cat:
                categories.append(cat)
    return categories


def schema_validate(obj: Any, schema_path: Path) -> List[ValidationIssue]:
    schema = load_json(schema_path)
    validator = Draft202012Validator(schema)
    issues: List[ValidationIssue] = []
    for err in sorted(validator.iter_errors(obj), key=lambda e: e.path):
        where = "$"
        if err.path:
            where = "$." + ".".join(str(p) for p in err.path)
        issues.append(ValidationIssue(f"Schema error at {where}: {err.message}"))
    return issues


def policy_validate(obj: Dict[str, Any], allowed_categories: List[str]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    scenario = obj.get("scenario", {})
    injects = obj.get("injects", [])

    category = scenario.get("category")
    if category not in allowed_categories:
        issues.append(
            ValidationIssue(
                f"Policy error: scenario.category '{category}' is not a canonical category from scenario_taxonomy.md"
            )
        )

    # Basic inject ordering and ID checks (expect i01, i02, ...)
    last_t: Optional[int] = None
    duration = scenario.get("duration_minutes")
    for inj in injects:
        inj_id = inj.get("id")
        if not isinstance(inj_id, str) or len(inj_id) != 3 or not inj_id.startswith("i") or not inj_id[1:].isdigit():
            issues.append(ValidationIssue(f"Policy error: inject.id '{inj_id}' should be like i01, i02, i03"))
        t = inj.get("t_plus_min")
        if isinstance(t, int):
            if last_t is not None and t < last_t:
                issues.append(ValidationIssue(f"Policy error: injects out of order: {t} < previous {last_t}"))
            last_t = t
            if isinstance(duration, int) and t > duration:
                issues.append(ValidationIssue(f"Policy error: inject t_plus_min {t} exceeds duration_minutes {duration}"))
        else:
            issues.append(ValidationIssue(f"Policy error: inject.t_plus_min must be an integer (inject {inj_id})"))

    return issues


def md_bullets(items: List[str]) -> str:
    if not items:
        return "- (none observed)\n"
    return "".join([f"- {x}\n" for x in items])


def first_non_empty(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if value is not None:
            txt = str(value).strip()
            if txt:
                return txt
    return ""


def coerce_roles(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def format_audience_labels(audience_list: List[str]) -> str:
    audience_map = {
        "command_team": "Command team",
        "executive_and_ir_leads": "Executive and IR leads",
        "incident_response_and_soc": "Incident response and SOC",
        "communications_and_legal": "Communications and Legal",
    }

    labels: List[str] = []
    for audience in audience_list:
        if audience in audience_map:
            labels.append(audience_map[audience])
            continue
        if "_" in audience:
            labels.append(audience.replace("_", " ").title())
            continue
        labels.append(audience)

    return ", ".join(labels)


def build_doc_context(
    scenario: Dict[str, Any],
    case_manifest: Optional[Dict[str, Any]],
    intake_structured: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    manifest = case_manifest or {}
    intake = intake_structured or {}

    duration = manifest.get("duration_minutes")
    if duration in (None, ""):
        duration = scenario.get("duration_minutes")

    audiences = coerce_roles(manifest.get("audience_roles"))
    if not audiences:
        audiences = coerce_roles(scenario.get("audiences"))

    return {
        "case_id": first_non_empty(manifest.get("case_id")),
        "client_organization": first_non_empty(manifest.get("client_name"), intake.get("client_organization")),
        "timezone": first_non_empty(manifest.get("timezone"), intake.get("timezone")),
        "duration_minutes": duration,
        "audiences": audiences,
        "handling_label": first_non_empty(manifest.get("handling_label")),
    }


def render_sitman(obj: Dict[str, Any], context: Dict[str, Any]) -> str:
    s = obj["scenario"]
    injects = obj["injects"]

    lines: List[str] = []
    lines.append("# TTX Situation Manual (SitMan)\n")
    lines.append("**Handling note:** Store securely and distribute only to authorized exercise participants.\n")
    lines.append("\n## 1) Document control\n")
    lines.append(f"- Engagement / Case ID: {context.get('case_id', '')}\n")
    lines.append(f"- Client / Organization: {context.get('client_organization', '')}\n")
    lines.append("- Exercise date: \n")
    lines.append(f"- Timezone: {context.get('timezone', '')}\n")
    lines.append(f"- Duration (minutes): {context.get('duration_minutes')}\n")
    lines.append("- Format: (Virtual / In-person)\n")
    lines.append(f"- Scenario ID: {s.get('id')}\n")
    lines.append(f"- Scenario title: {s.get('title')}\n")
    lines.append(f"- Scenario category: {s.get('category')}\n")
    lines.append("- Prepared by (role): \n")
    lines.append(f"- Distribution: {context.get('handling_label', '')}\n")

    lines.append("\n## 2) Purpose\n")
    lines.append(
        "This tabletop exercise is a **discussion-based simulation** intended to improve incident readiness by testing:\n"
        "- decision-making under time pressure,\n"
        "- escalation and authority clarity,\n"
        "- communications governance (internal and external),\n"
        "- legal/regulatory awareness (as applicable),\n"
        "- and identification of actionable improvements.\n\n"
        "**This is a no-fault learning exercise.** It is not an audit and does not prove technical control effectiveness.\n"
    )

    lines.append("\n## 3) Rules of engagement\n")
    lines.append("1. Discussion-based: No systems are touched; no live technical testing occurs.\n")
    lines.append("2. State assumptions: If information is missing, state assumptions and what you would request.\n")
    lines.append("3. Time-boxed decisions: The facilitator may force decisions to keep the exercise moving.\n")
    lines.append("4. One conversation at a time: Use a “parking lot” for side topics.\n")
    lines.append("5. Confidentiality: Treat exercise discussion and outputs as sensitive unless agreed otherwise.\n")

    lines.append("\n## 4) Objectives\n")
    lines.append(md_bullets(s.get("objectives", [])))

    lines.append("\n## 5) Assumptions and constraints\n")
    lines.append("\n### Assumptions\n")
    lines.append(md_bullets(s.get("assumptions", [])))
    lines.append("\n### Constraints / redlines\n")
    lines.append(md_bullets(s.get("constraints", [])))
    lines.append("\n### Out of scope\n")
    lines.append(md_bullets(s.get("out_of_scope", [])))

    lines.append("\n## 6) Scenario overview\n")
    lines.append("\n### Summary\n")
    lines.append(f"{s.get('summary','').strip()}\n")
    lines.append("\n### Threat context\n")
    lines.append(f"{s.get('threat_context','').strip()}\n")
    lines.append("\n### Business context\n")
    lines.append(f"{s.get('business_context','').strip()}\n")

    lines.append("\n## 7) Participants (roles only)\n")
    lines.append("- Executive:\n- IT:\n- Security:\n- Legal / Privacy:\n- PR / Comms:\n- HR:\n- Finance:\n- Product / Engineering:\n- Vendor / MSSP (optional):\n")

    lines.append("\n## 8) Scenario timeline (participant-facing injects)\n")
    lines.append("| Inject ID | T+ (min) | Audience (roles) | Prompt (participant-facing) |\n")
    lines.append("|---|---:|---|---|\n")
    for inj in injects:
        iid = inj.get("id", "")
        t = inj.get("t_plus_min", "")
        aud = format_audience_labels(inj.get("audience", []))
        prompt = " ".join(str(inj.get("participant_prompt", "")).split())
        lines.append(f"| {iid} | {t} | {aud} | {prompt} |\n")

    lines.append("\n## 9) Hotwash (debrief)\n")
    lines.append("- What worked well?\n")
    lines.append("- What slowed down decision-making?\n")
    lines.append("- Where were decision rights unclear?\n")
    lines.append("- What information/tools were missing?\n")
    lines.append("- What are the top 3 improvements in the next 30–90 days?\n")

    return "".join(lines)


def render_participant_guide(obj: Dict[str, Any], context: Dict[str, Any]) -> str:
    s = obj["scenario"]
    lines: List[str] = []
    lines.append("# TTX Participant Guide (Pre-read)\n")
    lines.append("**Handling note:** Store securely and distribute only to authorized exercise participants.\n")
    lines.append("\n## 1) Exercise overview\n")
    lines.append(
        "You are participating in a **discussion-based cybersecurity tabletop exercise (TTX)**.\n"
        "The purpose is to improve readiness by testing decision-making, escalation authority, and communications.\n\n"
        "**This is a no-fault learning exercise.** It is not an audit and does not prove technical control effectiveness.\n"
        "No systems will be accessed or tested during the session.\n"
    )

    lines.append("\n## 2) Logistics\n")
    lines.append(f"- Engagement / Case ID: {context.get('case_id', '')}\n")
    lines.append(f"- Client / Organization: {context.get('client_organization', '')}\n")
    lines.append(f"- Date:\n- Time:\n- Timezone: {context.get('timezone', '')}\n")
    lines.append(f"- Duration (minutes): {context.get('duration_minutes')}\n")
    lines.append(f"- Audiences (roles): {', '.join(context.get('audiences', []))}\n")
    lines.append(f"- Handling / Distribution: {context.get('handling_label', '')}\n")
    lines.append("- Format: (Virtual / In-person)\n- Location / Link:\n- Facilitator (role):\n- Scribe (role):\n- Observers (roles, optional):\n- Recording policy: (Yes/No)\n")

    lines.append("\n## 3) Objectives\n")
    lines.append(md_bullets(s.get("objectives", [])))

    lines.append("\n## 4) Rules of engagement\n")
    lines.append("1. No-fault learning environment: the goal is improvement, not grading individuals.\n")
    lines.append("2. Discussion-based: no systems are touched; we focus on decisions, communications, and process.\n")
    lines.append("3. State assumptions: if information is missing, state what you assume and what you would request.\n")
    lines.append("4. Time-boxed decisions: the facilitator may force a decision to keep the exercise moving.\n")
    lines.append("5. Confidentiality: treat discussion and outputs as sensitive unless agreed otherwise.\n")

    lines.append("\n## 5) Scenario summary\n")
    lines.append(f"- Scenario title: {s.get('title')}\n")
    lines.append(f"- Scenario category: {s.get('category')}\n")
    lines.append("\nSummary:\n")
    lines.append(f"{s.get('summary','').strip()}\n")

    return "".join(lines)


def render_scribe_logs(obj: Dict[str, Any]) -> str:
    s = obj["scenario"]
    injects = obj["injects"]

    lines: List[str] = []
    lines.append("# TTX Scribe Logs\n")
    lines.append("Use this document during facilitation to capture inject timing, decisions, communications, and action items.\n")
    lines.append("Store in secure project storage (outside git).\n")
    lines.append("\n## Scenario reference\n")
    lines.append(f"- Scenario ID: {s.get('id')}\n")
    lines.append(f"- Scenario title: {s.get('title')}\n")
    lines.append(f"- Scenario category: {s.get('category')}\n")
    lines.append(f"- Planned duration (minutes): {s.get('duration_minutes')}\n")

    lines.append("\n## 1) Inject execution log\n")
    lines.append("| Inject ID | Planned T+ (min) | Actual T+ (min) | Audience | Delivery method | 1–2 sentence summary of discussion | Notes / deviations |\n")
    lines.append("|---|---:|---:|---|---|---|---|\n")
    for inj in injects:
        iid = inj.get("id", "")
        t = inj.get("t_plus_min", "")
        aud = format_audience_labels(inj.get("audience", []))
        dm = inj.get("delivery_method", "")
        lines.append(f"| {iid} | {t} |  | {aud} | {dm} |  |  |\n")

    lines.append("\n## 2) Decision log\n")
    lines.append("| Time | Decision | Decision owner (role) | Rationale / tradeoffs | Info needed / requested | Follow-up action (owner + due) |\n")
    lines.append("|---|---|---|---|---|---|\n")
    lines.append("|  |  |  |  |  |  |\n")

    lines.append("\n## 3) Communications log (optional)\n")
    lines.append("| Time | Audience (internal/external) | Message purpose | Who approves | Channel | Notes |\n")
    lines.append("|---|---|---|---|---|---|\n")
    lines.append("|  |  |  |  |  |  |\n")

    lines.append("\n## 4) Action items\n")
    lines.append("| Action item | Owner (role) | Target timeframe (0/30/90) | Status | Notes |\n")
    lines.append("|---|---|---|---|---|\n")
    lines.append("|  |  |  |  |  |\n")

    return "".join(lines)


def render_facilitator_packet(obj: Dict[str, Any], context: Dict[str, Any]) -> str:
    s = obj["scenario"]
    injects = obj["injects"]

    lines: List[str] = []
    lines.append("# TTX Facilitator Packet\n")
    lines.append("**NOTE (internal):** Store this document in secure project storage and share only with authorized facilitation staff.\n")

    lines.append("\n## 1) Exercise metadata\n")
    lines.append(
        f"- Engagement / Case ID: {context.get('case_id', '')}\n"
        f"- Client / Organization: {context.get('client_organization', '')}\n"
        "- Date:\n"
        f"- Timezone: {context.get('timezone', '')}\n"
        "- Facilitator (role):\n"
        "- Scribe (role):\n"
        "- Observers (roles, optional):\n"
        "- Recording policy (Yes/No) + storage location (if Yes):\n"
    )
    lines.append(f"- Scenario ID: {s.get('id')}\n")
    lines.append(f"- Scenario title: {s.get('title')}\n")
    lines.append(f"- Scenario category: {s.get('category')}\n")
    lines.append(f"- Planned duration (minutes): {context.get('duration_minutes')}\n")
    lines.append(f"- Audiences (roles): {', '.join(context.get('audiences', []))}\n")
    lines.append(f"- Handling / Distribution: {context.get('handling_label', '')}\n")

    lines.append("\n## 2) Objectives\n")
    lines.append(md_bullets(s.get("objectives", [])))

    lines.append("\n## 3) Assumptions\n")
    lines.append(md_bullets(s.get("assumptions", [])))

    lines.append("\n## 4) Constraints / redlines\n")
    lines.append(md_bullets(s.get("constraints", [])))

    lines.append("\n## 5) Success criteria\n")
    lines.append(md_bullets(s.get("success_criteria", [])))

    lines.append("\n## 6) Facilitator notes (scenario-level)\n")
    lines.append(f"{str(s.get('facilitator_notes','')).strip()}\n")

    lines.append("\n## 7) Inject-by-inject facilitation details\n")
    for inj in injects:
        iid = inj.get("id", "")
        t = inj.get("t_plus_min", "")
        dm = inj.get("delivery_method", "")
        aud = format_audience_labels(inj.get("audience", []))
        prompt = str(inj.get("participant_prompt", "")).strip()

        lines.append(f"\n### {iid} (T+{t} min) — {dm} — Audience: {aud}\n")
        lines.append("\n**Participant prompt (read verbatim):**\n")
        lines.append(f"{prompt}\n")

        ed = inj.get("expected_discussion", [])
        if isinstance(ed, list) and ed:
            lines.append("\n**Expected discussion prompts:**\n")
            lines.append(md_bullets([str(x) for x in ed]))

        dec = inj.get("expected_decisions", [])
        if isinstance(dec, list) and dec:
            lines.append("\n**Expected decisions:**\n")
            lines.append(md_bullets([str(x) for x in dec]))

        ev = inj.get("evaluation_criteria", [])
        if isinstance(ev, list) and ev:
            lines.append("\n**Evaluation criteria (what “good” looks like):**\n")
            lines.append(md_bullets([str(x) for x in ev]))

        bg = str(inj.get("branching_guidance", "")).strip()
        if bg:
            lines.append("\n**Branching guidance:**\n")
            lines.append(f"{bg}\n")

        fn = str(inj.get("facilitator_notes", "")).strip()
        if fn:
            lines.append("\n**Facilitator notes (NOT shown to participants):**\n")
            lines.append(f"{fn}\n")

        refs = inj.get("evidence_refs", [])
        if isinstance(refs, list) and refs:
            lines.append("\n**Synthetic evidence references (optional):**\n")
            lines.append(md_bullets([str(x) for x in refs]))

    lines.append("\n## 8) Decision-forcing questions (use repeatedly)\n")
    lines.append("- What decision do you need to make right now?\n")
    lines.append("- Who owns that decision?\n")
    lines.append("- What is the immediate priority in the next 30 minutes?\n")
    lines.append("- What information do you need, and who will request it?\n")
    lines.append("- What is the business impact of containment vs continued operation?\n")
    lines.append("- What are you communicating internally and externally, and who approves it?\n")

    lines.append("\n## 9) Scribe logs (copy/paste or keep separate)\n")
    lines.append("\n### Inject execution log\n")
    lines.append("| Inject ID | Planned T+ (min) | Actual T+ (min) | Audience | Delivery method | 1–2 sentence summary of discussion | Notes / deviations |\n")
    lines.append("|---|---:|---:|---|---|---|---|\n")
    for inj in injects:
        iid = inj.get("id", "")
        t = inj.get("t_plus_min", "")
        aud = format_audience_labels(inj.get("audience", []))
        dm = inj.get("delivery_method", "")
        lines.append(f"| {iid} | {t} |  | {aud} | {dm} |  |  |\n")

    lines.append("\n### Decision log\n")
    lines.append("| Time | Decision | Decision owner (role) | Rationale / tradeoffs | Info needed / requested | Follow-up action (owner + due) |\n")
    lines.append("|---|---|---|---|---|---|\n")
    lines.append("|  |  |  |  |  |  |\n")

    lines.append("\n### Communications log (optional)\n")
    lines.append("| Time | Audience (internal/external) | Message purpose | Who approves | Channel | Notes |\n")
    lines.append("|---|---|---|---|---|---|\n")
    lines.append("|  |  |  |  |  |  |\n")

    lines.append("\n### Action items\n")
    lines.append("| Action item | Owner (role) | Target timeframe (0/30/90) | Status | Notes |\n")
    lines.append("|---|---|---|---|---|\n")
    lines.append("|  |  |  |  |  |\n")

    return "".join(lines)


def render_manifest(input_path: Path, out_dir: Path, obj: Dict[str, Any]) -> str:
    s = obj["scenario"]
    files = [
        "scenario.yaml",
        "sitman.md",
        "facilitator_packet.md",
        "participant_guide.md",
        "scribe_logs.md",
        "package_manifest.md",
    ]
    lines: List[str] = []
    lines.append("# TTX Package Manifest\n")
    lines.append("\n## Scenario reference\n")
    lines.append(f"- Scenario ID: {s.get('id')}\n")
    lines.append(f"- Scenario title: {s.get('title')}\n")
    lines.append(f"- Scenario category: {s.get('category')}\n")
    lines.append(f"- Duration (minutes): {s.get('duration_minutes')}\n")
    lines.append(f"- Source scenario YAML: {str(input_path)}\n")

    lines.append("\n## Generated artifacts\n")
    for f in files:
        lines.append(f"- {f}\n")

    lines.append("\n## Handling rules (critical)\n")
    lines.append("- Store client-tailored artifacts in secure project storage (outside git).\n")
    lines.append("- Do NOT commit client-tailored scenario YAML, SitMan, facilitator packet, scribe logs, or AARs to git.\n")
    lines.append("- Prefer roles over names; avoid unnecessary client identifiers.\n")

    lines.append("\n## Next steps\n")
    lines.append("- Use facilitator_packet.md to run the session.\n")
    lines.append("- Use scribe_logs.md during facilitation.\n")
    lines.append("- Draft the After-Action Report using dfir_backend/ttx/after_action_report_template.md (outside git).\n")

    return "".join(lines)


def write_file(path: Path, content: str, force: bool) -> None:
    if path.exists() and not force:
        raise FileExistsError(f"Refusing to overwrite existing file: {path} (use --force to overwrite)")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a TTX package from a scenario YAML.")
    parser.add_argument("--input", required=True, help="Path to scenario YAML file.")
    parser.add_argument("--out-dir", required=True, help="Output directory for generated artifacts.")
    parser.add_argument(
        "--schema",
        default="dfir_backend/ttx/schemas/ttx_scenario.schema.json",
        help="Path to JSON schema (relative to repo root by default).",
    )
    parser.add_argument(
        "--taxonomy",
        default="dfir_backend/ttx/scenario_taxonomy.md",
        help="Path to taxonomy markdown (relative to repo root by default).",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite output files if they already exist.")
    parser.add_argument(
        "--allow-in-repo",
        action="store_true",
        help="Allow writing output inside the git repo directory (ONLY for synthetic examples).",
    )
    parser.add_argument("--case-dir", help="Case directory. If provided, load <case-dir>/case_manifest.json.")
    parser.add_argument(
        "--intake-structured",
        help="Optional path to intake_structured.json. Defaults to <case-dir>/10_inputs/intake_structured.json when --case-dir is set.",
    )
    args = parser.parse_args()

    repo_root = repo_root_from_here()
    input_path = Path(args.input).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()
    schema_path = (repo_root / args.schema).resolve() if not Path(args.schema).is_absolute() else Path(args.schema).resolve()
    taxonomy_path = (repo_root / args.taxonomy).resolve() if not Path(args.taxonomy).is_absolute() else Path(args.taxonomy).resolve()

    if not input_path.exists():
        print(f"ERROR: Input scenario YAML not found: {input_path}", file=sys.stderr)
        return 2
    if not schema_path.exists():
        print(f"ERROR: Schema not found: {schema_path}", file=sys.stderr)
        return 2
    if not taxonomy_path.exists():
        print(f"ERROR: Taxonomy not found: {taxonomy_path}", file=sys.stderr)
        return 2

    case_manifest: Optional[Dict[str, Any]] = None
    intake_structured: Optional[Dict[str, Any]] = None
    if args.case_dir:
        case_dir = Path(args.case_dir).expanduser().resolve()
        case_manifest_path = case_dir / "case_manifest.json"
        if case_manifest_path.exists():
            case_manifest = load_json(case_manifest_path)
        else:
            print(f"WARN: case_manifest.json not found at {case_manifest_path}; using scenario/intake fallbacks.", file=sys.stderr)

        intake_path = Path(args.intake_structured).expanduser().resolve() if args.intake_structured else (case_dir / "10_inputs" / "intake_structured.json")
        if intake_path.exists():
            intake_structured = load_json(intake_path)
        elif args.intake_structured:
            print(f"WARN: intake_structured.json not found at {intake_path}; continuing without it.", file=sys.stderr)
    elif args.intake_structured:
        intake_path = Path(args.intake_structured).expanduser().resolve()
        if intake_path.exists():
            intake_structured = load_json(intake_path)
        else:
            print(f"WARN: intake_structured.json not found at {intake_path}; continuing without it.", file=sys.stderr)

    if not args.allow_in_repo and is_within(out_dir, repo_root):
        print(
            "ERROR: Refusing to write outputs inside the git repo directory.\n"
            f"- Repo root: {repo_root}\n"
            f"- Output dir: {out_dir}\n\n"
            "Write outputs to secure project storage outside git, or use --allow-in-repo ONLY for synthetic examples.",
            file=sys.stderr,
        )
        return 2

    obj = load_yaml(input_path)
    if not isinstance(obj, dict):
        print("ERROR: YAML root must be an object/mapping.", file=sys.stderr)
        return 2

    # Validate against schema + taxonomy.
    issues: List[ValidationIssue] = []
    issues.extend(schema_validate(obj, schema_path))
    allowed_categories = read_taxonomy_categories(taxonomy_path)
    if not allowed_categories:
        issues.append(ValidationIssue("No taxonomy categories found. Expected headings starting with '## '"))
    else:
        issues.extend(policy_validate(obj, allowed_categories))

    if issues:
        print("ERROR: Scenario validation failed:\n", file=sys.stderr)
        for i in issues:
            print(f"- {i.message}", file=sys.stderr)
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    context = build_doc_context(obj.get("scenario", {}), case_manifest, intake_structured)

    # Write scenario.yaml as a copy of the input file (preserve original formatting).
    scenario_text = input_path.read_text(encoding="utf-8")
    write_file(out_dir / "scenario.yaml", scenario_text, force=args.force)

    # Render and write derived artifacts.
    write_file(out_dir / "sitman.md", render_sitman(obj, context), force=args.force)
    write_file(out_dir / "facilitator_packet.md", render_facilitator_packet(obj, context), force=args.force)
    write_file(out_dir / "participant_guide.md", render_participant_guide(obj, context), force=args.force)
    write_file(out_dir / "scribe_logs.md", render_scribe_logs(obj), force=args.force)
    write_file(out_dir / "package_manifest.md", render_manifest(input_path, out_dir, obj), force=args.force)

    print("TTX package generated:")
    for f in ["scenario.yaml", "sitman.md", "facilitator_packet.md", "participant_guide.md", "scribe_logs.md", "package_manifest.md"]:
        print(f"- {out_dir / f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
