#!/usr/bin/env python3
"""
Create a paste-ready AI bundle for generating a bespoke scenario YAML for a specific case.

This script DOES NOT call any AI.
It packages:
- the scenario-generation prompt template
- the canonical taxonomy (categories)
- the canonical JSON schema
- case manifest context (duration, audience, constraints)
- optional intake notes
- optional IR plan text

SAFETY:
- Refuses to write outputs inside the git repo directory by default.
- Use --allow-in-repo ONLY for synthetic examples.

Outputs (under 10_inputs/ttx_scenario_generation by default):
- scenario_generation_inputs.json
- ttx_scenario_ai_bundle.txt
- scenario_generated.yaml (placeholder to paste YAML output)
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
    # .../dfir_backend/ttx/scripts/build_ttx_scenario_ai_bundle_from_case.py -> repo root is parents[3]
    return Path(__file__).resolve().parents[3]


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def taxonomy_categories(taxonomy_md: str) -> List[str]:
    cats: List[str] = []
    for line in taxonomy_md.splitlines():
        line = line.strip()
        if line.startswith("## "):
            c = line.replace("## ", "", 1).strip()
            if c:
                cats.append(c)
    return cats


def load_manifest(case_dir: Path) -> Dict[str, Any]:
    manifest_path = case_dir / "case_manifest.json"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def validate_manifest(schema_path: Path, manifest: Dict[str, Any]) -> None:
    schema = read_json(schema_path)
    validator = Draft202012Validator(schema)
    errs = sorted(validator.iter_errors(manifest), key=lambda e: list(e.path))
    if errs:
        msgs = []
        for e in errs:
            where = "$"
            if e.path:
                where = "$." + ".".join(str(p) for p in e.path)
            msgs.append(f"{where}: {e.message}")
        raise ValueError("Manifest schema validation failed:\n" + "\n".join(msgs))


def handling_label_from_manifest(manifest: Dict[str, Any]) -> str:
    hl = str(manifest.get("handling_label", "")).strip()
    if hl:
        return hl

    # Backward compat: map deprecated TLP if present
    tlp = str(manifest.get("tlp", "")).strip()
    mapping = {
        "TLP:CLEAR": "PUBLIC",
        "TLP:GREEN": "INTERNAL",
        "TLP:AMBER": "CONFIDENTIAL",
        "TLP:AMBER+STRICT": "CLIENT_CONFIDENTIAL",
        "TLP:RED": "CLIENT_CONFIDENTIAL",
    }
    return mapping.get(tlp, "CLIENT_CONFIDENTIAL" if tlp else "CLIENT_CONFIDENTIAL")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an AI scenario YAML generation bundle from a case folder.")
    parser.add_argument("--case-dir", required=True, help="Case folder containing case_manifest.json")
    parser.add_argument("--out-dir", default="", help="Override output directory (default: 10_inputs/ttx_scenario_generation)")
    parser.add_argument("--allow-in-repo", action="store_true", help="Allow writing outputs inside the repo (synthetic only).")
    args = parser.parse_args()

    repo_root = repo_root_from_here()
    case_dir = Path(args.case_dir).expanduser().resolve()

    if not case_dir.is_dir():
        print(f"ERROR: case-dir is not a directory: {case_dir}", file=sys.stderr)
        return 2

    if not args.allow_in_repo and is_within(case_dir, repo_root):
        print(
            "ERROR: Refusing to operate on a case folder inside the git repo.\n"
            "Store case data in secure storage outside git.\n"
            f"- Repo root: {repo_root}\n"
            f"- Case dir: {case_dir}",
            file=sys.stderr,
        )
        return 2

    manifest_schema = repo_root / "dfir_backend" / "ttx" / "schemas" / "ttx_case_manifest.schema.json"
    taxonomy_path = repo_root / "dfir_backend" / "ttx" / "scenario_taxonomy.md"
    scenario_schema_path = repo_root / "dfir_backend" / "ttx" / "schemas" / "ttx_scenario.schema.json"
    prompt_path = repo_root / "dfir_backend" / "ai_assist" / "prompts" / "ttx_scenario_yaml_from_ir_plan.md"

    for p in (manifest_schema, taxonomy_path, scenario_schema_path, prompt_path):
        if not p.exists():
            print(f"ERROR: Required repo file not found: {p}", file=sys.stderr)
            return 2

    manifest = load_manifest(case_dir)
    validate_manifest(manifest_schema, manifest)

    category = str(manifest["scenario"].get("category", "")).strip()
    if not category:
        print("ERROR: case_manifest.json missing scenario.category. Set it in the case workflow runner first.", file=sys.stderr)
        return 2

    taxonomy_md = read_text(taxonomy_path)
    cats = taxonomy_categories(taxonomy_md)
    if category not in cats:
        print(f"ERROR: scenario.category '{category}' is not a canonical taxonomy category.", file=sys.stderr)
        print("Allowed categories:", file=sys.stderr)
        for c in cats:
            print(f"- {c}", file=sys.stderr)
        return 2

    # Locate case input files (relative paths in manifest)
    def resolve_case_path(rel: str) -> Path:
        return (case_dir / rel).resolve()

    intake_path = resolve_case_path(manifest["inputs"]["intake_notes_path"])
    ir_plan_path = resolve_case_path(manifest["inputs"]["ir_plan_path"])
    threat_path = resolve_case_path(manifest["inputs"]["threat_brief_path"])

    intake_text = read_text(intake_path) if intake_path.exists() else ""
    ir_text = read_text(ir_plan_path) if ir_plan_path.exists() else ""
    threat_text = read_text(threat_path) if threat_path.exists() else ""

    out_dir = Path(args.out_dir).expanduser().resolve() if args.out_dir.strip() else resolve_case_path(manifest["inputs"]["scenario_generation_dir"])
    if not args.allow_in_repo and is_within(out_dir, repo_root):
        print("ERROR: Refusing to write outputs inside git repo. Choose a case out-dir outside git.", file=sys.stderr)
        return 2

    out_dir.mkdir(parents=True, exist_ok=True)

    inputs_obj: Dict[str, Any] = {
        "generated_at_utc": now_iso(),
        "case_id": manifest.get("case_id", ""),
        "bundle_type": manifest.get("bundle_type", ""),
        "duration_minutes": manifest.get("duration_minutes", ""),
        "timezone": manifest.get("timezone", ""),
        "handling_label": handling_label_from_manifest(manifest),
        "industry": manifest.get("industry", ""),
        "region": manifest.get("region", ""),
        "audience_roles": manifest.get("audience_roles", []),
        "scenario_category": category,
        "scenario_title_hint": manifest["scenario"].get("title_hint", ""),
        "constraints": [],
    }

    write_text(out_dir / "scenario_generation_inputs.json", json.dumps(inputs_obj, indent=2) + "\n")

    scenario_schema = json.dumps(read_json(scenario_schema_path), indent=2)

    bundle: List[str] = []
    bundle.append("INSTRUCTIONS (STRICT):\n")
    bundle.append("1) Output MUST be YAML ONLY (no markdown fences).\n")
    bundle.append("2) YAML MUST validate against the included JSON schema.\n")
    bundle.append(f"3) scenario.category MUST EXACTLY be: {category}\n")
    bundle.append("4) Do NOT invent client environment details; list assumptions explicitly.\n")
    bundle.append("5) Prefer roles over names; avoid PII; do not include secrets.\n\n")

    bundle.append("========== PROMPT TEMPLATE ==========\n\n")
    bundle.append(read_text(prompt_path))
    bundle.append("\n\n")

    bundle.append("========== CANONICAL TAXONOMY (CATEGORIES) ==========\n\n")
    for c in cats:
        bundle.append(f"- {c}\n")
    bundle.append("\n")

    bundle.append("========== JSON SCHEMA (MUST COMPLY) ==========\n\n")
    bundle.append(scenario_schema)
    bundle.append("\n\n")

    bundle.append("========== CASE CONTEXT (JSON) ==========\n\n")
    bundle.append(json.dumps(inputs_obj, indent=2))
    bundle.append("\n\n")

    if threat_text.strip():
        bundle.append("========== THREAT BRIEF (OPTIONAL; HIGH-LEVEL) ==========\n\n")
        bundle.append(threat_text)
        bundle.append("\n\n")

    if intake_text.strip():
        bundle.append("========== INTAKE NOTES ==========\n\n")
        bundle.append(intake_text)
        bundle.append("\n\n")

    if ir_text.strip():
        bundle.append("========== IR PLAN EXCERPTS (TEXT) ==========\n\n")
        bundle.append(ir_text)
        bundle.append("\n\n")

    write_text(out_dir / "ttx_scenario_ai_bundle.txt", "".join(bundle))

    placeholder = []
    placeholder.append("# Paste the AI-generated, schema-valid TTX scenario YAML here.\n")
    placeholder.append("# REQUIRE YAML ONLY (no markdown).\n")
    placeholder.append("#\n")
    placeholder.append("# After pasting, copy or move this file to:\n")
    placeholder.append("#   20_delivery/scenario.yaml\n")
    placeholder.append("# Then validate/build via the case workflow runner.\n\n")
    write_text(out_dir / "scenario_generated.yaml", "".join(placeholder))

    print("Wrote scenario AI bundle artifacts:")
    print(f"- {out_dir / 'scenario_generation_inputs.json'}")
    print(f"- {out_dir / 'ttx_scenario_ai_bundle.txt'}")
    print(f"- {out_dir / 'scenario_generated.yaml'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
