#!/usr/bin/env python3
"""
Optionally generate a TTX AAR markdown file using OpenAI Responses API.

Safety defaults:
- Requires explicit --confirm-send I_HAVE_CLIENT_PERMISSION to call network.
- Reads API key from --api-key or OPENAI_API_KEY.
- Supports --dry-run to write assembled prompt bundle only.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, List


def repo_root_from_here() -> Path:
    # .../dfir_backend/ttx/scripts/generate_aar_with_openai.py -> repo root is parents[3]
    return Path(__file__).resolve().parents[3]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_input_bundle(
    prompt_template: str,
    scenario_yaml: str,
    runtime_json: str,
    intake_notes: str,
    ir_plan: str,
) -> str:
    sections: List[str] = []
    sections.append("========== PROMPT TEMPLATE ==========\n\n")
    sections.append(prompt_template)
    sections.append("\n\n")

    sections.append("========== SCENARIO YAML ==========\n\n")
    sections.append(scenario_yaml)
    sections.append("\n\n")

    sections.append("========== SCRIBE RUNTIME JSON ==========\n\n")
    sections.append(runtime_json)
    sections.append("\n\n")

    sections.append("========== INTAKE NOTES (OPTIONAL) ==========\n\n")
    sections.append(intake_notes)
    sections.append("\n\n")

    sections.append("========== IR PLAN TEXT (OPTIONAL) ==========\n\n")
    sections.append(ir_plan)
    sections.append("\n\n")

    sections.append("========== OUTPUT REQUIREMENTS ==========\n\n")
    sections.append("- Markdown only\n")
    sections.append("- no code fences\n")
    return "".join(sections)


def extract_output_text(response_obj: Any) -> str:
    output = response_obj.get("output")
    if not isinstance(output, list):
        return ""

    chunks: List[str] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict):
                continue
            if part.get("type") == "output_text":
                text = part.get("text")
                if isinstance(text, str):
                    chunks.append(text)
    return "".join(chunks).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Optionally generate TTX AAR markdown via OpenAI Responses API.")
    parser.add_argument("--scenario-yaml", required=True)
    parser.add_argument("--runtime-json", required=True)
    parser.add_argument("--out-path", required=True)
    parser.add_argument("--ir-plan", default="")
    parser.add_argument("--intake-notes", default="")
    parser.add_argument("--model", default="gpt-5-mini")
    parser.add_argument("--max-output-tokens", type=int, default=2200)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--api-key", default="")
    parser.add_argument("--confirm-send", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    scenario_path = Path(args.scenario_yaml).expanduser().resolve()
    runtime_path = Path(args.runtime_json).expanduser().resolve()
    out_path = Path(args.out_path).expanduser().resolve()

    if not scenario_path.exists():
        print(f"ERROR: scenario-yaml not found: {scenario_path}", file=sys.stderr)
        return 2
    if not runtime_path.exists():
        print(f"ERROR: runtime-json not found: {runtime_path}", file=sys.stderr)
        return 2

    intake_notes_text = ""
    if args.intake_notes.strip():
        intake_path = Path(args.intake_notes).expanduser().resolve()
        if not intake_path.exists():
            print(f"ERROR: intake-notes file not found: {intake_path}", file=sys.stderr)
            return 2
        intake_notes_text = read_text(intake_path)

    ir_plan_text = ""
    if args.ir_plan.strip():
        ir_plan_path = Path(args.ir_plan).expanduser().resolve()
        if not ir_plan_path.exists():
            print(f"ERROR: ir-plan file not found: {ir_plan_path}", file=sys.stderr)
            return 2
        ir_plan_text = read_text(ir_plan_path)

    prompt_template_path = repo_root_from_here() / "dfir_backend" / "ai_assist" / "prompts" / "ttx_aar_from_scribe_notes.md"
    if not prompt_template_path.exists():
        print(f"ERROR: Prompt template not found: {prompt_template_path}", file=sys.stderr)
        return 2

    input_bundle = build_input_bundle(
        prompt_template=read_text(prompt_template_path),
        scenario_yaml=read_text(scenario_path),
        runtime_json=read_text(runtime_path),
        intake_notes=intake_notes_text,
        ir_plan=ir_plan_text,
    )

    if args.dry_run:
        prompt_out = Path(str(out_path) + ".prompt.txt")
        prompt_out.parent.mkdir(parents=True, exist_ok=True)
        prompt_out.write_text(input_bundle, encoding="utf-8")
        print(f"Wrote prompt bundle (dry-run): {prompt_out}")
        return 0

    if args.confirm_send != "I_HAVE_CLIENT_PERMISSION":
        print(
            "ERROR: Network call blocked. To run this script, set --confirm-send exactly to I_HAVE_CLIENT_PERMISSION.",
            file=sys.stderr,
        )
        return 2

    api_key = args.api_key.strip() or os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        print("ERROR: Missing API key. Provide --api-key or set OPENAI_API_KEY.", file=sys.stderr)
        return 2

    request_body = {
        "model": args.model,
        "input": input_bundle,
        "text": {"format": {"type": "text"}},
        "max_output_tokens": args.max_output_tokens,
        "temperature": args.temperature,
        "store": False,
    }

    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(request_body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"ERROR: API request failed ({exc.code}).\n{body}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"ERROR: API request failed: {exc}", file=sys.stderr)
        return 1

    try:
        response_obj = json.loads(raw)
    except json.JSONDecodeError:
        print("ERROR: API response was not valid JSON.", file=sys.stderr)
        return 1

    err = response_obj.get("error")
    if err:
        print(f"ERROR: API returned error: {json.dumps(err, ensure_ascii=False)}", file=sys.stderr)
        return 1

    output_text = extract_output_text(response_obj)
    if not output_text:
        print("ERROR: Could not parse output_text from API response.", file=sys.stderr)
        return 1

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(output_text + "\n", encoding="utf-8")
    print(f"Wrote AI-generated AAR markdown: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
