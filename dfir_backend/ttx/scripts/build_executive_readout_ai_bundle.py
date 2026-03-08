#!/usr/bin/env python3
"""
Build a single AI input bundle for drafting a TTX executive readout.

This does NOT call any AI. It creates a text file you can paste into your approved LLM workflow.

Bundle includes:
- Prompt template: dfir_backend/ai_assist/prompts/ttx_executive_readout_from_runtime.md
- Scenario YAML (full text)
- scribe_runtime.json (full text)
- Optional: intake notes text file
- Optional: IR plan text file

SAFETY:
- By default, refuses to write outputs inside the git repo directory.
- Use --allow-in-repo ONLY for synthetic examples.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[3]


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a paste-ready AI bundle for executive readout drafting.")
    parser.add_argument("--scenario-yaml", required=True, help="Path to scenario YAML.")
    parser.add_argument("--runtime-json", required=True, help="Path to scribe_runtime.json exported by TTX Studio.")
    parser.add_argument("--out-dir", required=True, help="Output directory for bundle.")
    parser.add_argument("--case-manifest", default="", help="Optional path to case_manifest.json.")
    parser.add_argument("--ir-plan", default="", help="Optional path to IR plan text file.")
    parser.add_argument("--intake-notes", default="", help="Optional path to intake notes text file.")
    parser.add_argument("--allow-in-repo", action="store_true", help="Allow writing outputs inside the repo (synthetic only).")
    args = parser.parse_args()

    repo_root = repo_root_from_here()

    scenario_path = Path(args.scenario_yaml).expanduser().resolve()
    runtime_path = Path(args.runtime_json).expanduser().resolve()
    out_dir = Path(args.out_dir).expanduser().resolve()

    if not scenario_path.exists():
        print(f"ERROR: scenario-yaml not found: {scenario_path}", file=sys.stderr)
        return 2
    if not runtime_path.exists():
        print(f"ERROR: runtime-json not found: {runtime_path}", file=sys.stderr)
        return 2

    if args.case_manifest.strip():
        p = Path(args.case_manifest).expanduser().resolve()
        if not p.exists():
            print(f"ERROR: case-manifest file not found: {p}", file=sys.stderr)
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

    prompt_path = repo_root / "dfir_backend" / "ai_assist" / "prompts" / "ttx_executive_readout_from_runtime.md"
    if not prompt_path.exists():
        print(f"ERROR: Prompt template not found: {prompt_path}", file=sys.stderr)
        return 2

    ir_plan_text = ""
    if args.ir_plan.strip():
        p = Path(args.ir_plan).expanduser().resolve()
        if not p.exists():
            print(f"ERROR: IR plan file not found: {p}", file=sys.stderr)
            return 2
        ir_plan_text = read_text(p)

    intake_text = ""
    if args.intake_notes.strip():
        p = Path(args.intake_notes).expanduser().resolve()
        if not p.exists():
            print(f"ERROR: Intake notes file not found: {p}", file=sys.stderr)
            return 2
        intake_text = read_text(p)

    bundle = []
    bundle.append("INSTRUCTIONS:\n")
    bundle.append("- Use only approved AI tooling/workflows for client data.\n")
    bundle.append("- Prefer roles over names; remove secrets/PII before submission.\n")
    bundle.append("- Paste EVERYTHING below into your AI tool.\n\n")

    bundle.append("========== PROMPT TEMPLATE ==========\n\n")
    bundle.append(read_text(prompt_path))
    bundle.append("\n\n")

    bundle.append("========== SCENARIO YAML ==========\n\n")
    bundle.append(read_text(scenario_path))
    bundle.append("\n\n")

    bundle.append("========== SCRIBE RUNTIME JSON (EXPORT) ==========\n\n")
    bundle.append(read_text(runtime_path))
    bundle.append("\n\n")

    if intake_text:
        bundle.append("========== INTAKE NOTES (OPTIONAL) ==========\n\n")
        bundle.append(intake_text)
        bundle.append("\n\n")

    if ir_plan_text:
        bundle.append("========== IR PLAN TEXT (OPTIONAL) ==========\n\n")
        bundle.append(ir_plan_text)
        bundle.append("\n\n")

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "executive_readout_ai_bundle.txt"
    out_path.write_text("".join(bundle), encoding="utf-8")

    print(f"Wrote AI bundle: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
