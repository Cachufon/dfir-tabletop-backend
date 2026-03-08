#!/usr/bin/env python3
"""
Optionally generate scenario enhancement suggestions via OpenAI Responses API.

Safety defaults:
- Requires explicit --confirm-send I_HAVE_CLIENT_PERMISSION to call network.
- Reads API key from --api-key or OPENAI_API_KEY.
- Supports --dry-run to write assembled prompt bundle only.
- Writes suggestions to markdown; never modifies scenario.yaml.
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
    return Path(__file__).resolve().parents[3]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def build_input_bundle(prompt_template: str, reference_catalog: str, scenario_yaml: str) -> str:
    sections: List[str] = []
    sections.append("========== PROMPT TEMPLATE ==========\n\n")
    sections.append(prompt_template)
    sections.append("\n\n")

    sections.append("========== REFERENCE CATALOG YAML ==========\n\n")
    sections.append(reference_catalog)
    sections.append("\n\n")

    sections.append("========== SCENARIO YAML ==========\n\n")
    sections.append(scenario_yaml)
    sections.append("\n\n")

    sections.append("========== OUTPUT REQUIREMENTS ==========\n\n")
    sections.append("- Markdown only\n")
    sections.append("- Suggestions only; do not provide full replacement scenario YAML\n")

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
    parser = argparse.ArgumentParser(description="Optionally generate TTX scenario enhancement suggestions via OpenAI Responses API.")
    parser.add_argument("--scenario-yaml", required=True)
    parser.add_argument("--reference-catalog", default="dfir_backend/ttx/library/reference_catalog.yaml")
    parser.add_argument("--out-path", required=True)
    parser.add_argument("--model", default="gpt-5")
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--api-key", default="")
    parser.add_argument("--confirm-send", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    repo_root = repo_root_from_here()
    prompt_template_path = repo_root / "dfir_backend" / "ai_assist" / "prompts" / "ttx_scenario_enhance_from_yaml.md"
    scenario_yaml_path = Path(args.scenario_yaml).expanduser().resolve()
    default_reference_catalog = repo_root / "dfir_backend" / "ttx" / "library" / "reference_catalog.yaml"
    reference_catalog_arg = Path(args.reference_catalog).expanduser()
    if not reference_catalog_arg.is_absolute():
        reference_catalog_arg = repo_root / reference_catalog_arg
    reference_catalog_path = reference_catalog_arg.resolve()
    if not args.reference_catalog.strip():
        reference_catalog_path = default_reference_catalog
    out_path = Path(args.out_path).expanduser().resolve()

    if not prompt_template_path.exists():
        print(f"ERROR: prompt template not found: {prompt_template_path}", file=sys.stderr)
        return 2
    if not scenario_yaml_path.exists():
        print(f"ERROR: scenario-yaml not found: {scenario_yaml_path}", file=sys.stderr)
        return 2
    if not reference_catalog_path.exists():
        print(f"ERROR: reference-catalog not found: {reference_catalog_path}", file=sys.stderr)
        return 2

    input_bundle = build_input_bundle(
        prompt_template=read_text(prompt_template_path),
        reference_catalog=read_text(reference_catalog_path),
        scenario_yaml=read_text(scenario_yaml_path),
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
        "store": False,
        "input": input_bundle,
        "text": {"format": {"type": "text"}},
        "temperature": args.temperature,
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
    print(f"Wrote AI enhancement suggestions: {out_path}")
    if args.apply:
        print("NOTICE: --apply was provided. This script still writes suggestions only and does not modify scenario.yaml.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
