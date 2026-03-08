#!/usr/bin/env python3
"""
Validate a single TTX scenario YAML file against:
- JSON schema: dfir_backend/ttx/schemas/ttx_scenario.schema.json
- Taxonomy: dfir_backend/ttx/scenario_taxonomy.md
- Basic policy checks (inject ids, ordering, t_plus_min within duration)

Designed to work from any working directory. Default paths are repo-relative.

Exit codes:
- 0: pass
- 1: validation failed
- 2: usage/config error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
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


INJECT_ID_RE = re.compile(r"^i\d{2}$")


def repo_root_from_here() -> Path:
    # .../dfir_backend/ttx/scripts/validate_ttx_scenario_file.py -> repo root is parents[3]
    return Path(__file__).resolve().parents[3]


def resolve_repo_relative_path(value: str, repo_root: Path) -> Path:
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = repo_root / p
    return p.resolve()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def read_taxonomy_categories(taxonomy_path: Path) -> List[str]:
    cats: List[str] = []
    for line in taxonomy_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("## Category naming rules"):
            continue
        if line.startswith("## "):
            c = line.replace("## ", "", 1).strip()
            if c:
                cats.append(c)
    return cats


def schema_validate(validator: Draft202012Validator, obj: Any) -> List[str]:
    issues: List[str] = []
    for err in sorted(validator.iter_errors(obj), key=lambda e: list(e.path)):
        where = "$"
        if err.path:
            where = "$." + ".".join(str(p) for p in err.path)
        issues.append(f"Schema error at {where}: {err.message}")
    return issues


def policy_checks(obj: Dict[str, Any], allowed_categories: Optional[List[str]]) -> List[str]:
    issues: List[str] = []
    scenario = obj.get("scenario", {})
    injects = obj.get("injects", [])

    category = scenario.get("category")
    if allowed_categories is not None and category not in allowed_categories:
        issues.append(f"Policy error: scenario.category '{category}' is not a canonical category from scenario_taxonomy.md")

    if isinstance(injects, list):
        for inj in injects:
            if not isinstance(inj, dict):
                continue
            inj_id = inj.get("id")
            if not isinstance(inj_id, str) or not INJECT_ID_RE.match(inj_id):
                issues.append(f"Policy error: inject.id '{inj_id}' should match pattern iNN (e.g., i01, i02)")

    duration = scenario.get("duration_minutes")
    if isinstance(duration, int) and duration >= 0 and isinstance(injects, list):
        last_t: Optional[int] = None
        for inj in injects:
            if not isinstance(inj, dict):
                continue
            t = inj.get("t_plus_min")
            if not isinstance(t, int):
                continue
            if last_t is not None and t < last_t:
                issues.append(f"Policy error: injects out of order (t_plus_min {t} < previous {last_t}). Sort injects by time.")
            last_t = t
            if t > duration:
                issues.append(f"Policy error: inject t_plus_min {t} exceeds scenario.duration_minutes {duration}.")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a single TTX scenario YAML file.")
    parser.add_argument("--input", required=True, help="Path to scenario YAML file.")
    parser.add_argument("--schema", default="dfir_backend/ttx/schemas/ttx_scenario.schema.json", help="Repo-relative by default.")
    parser.add_argument("--taxonomy", default="dfir_backend/ttx/scenario_taxonomy.md", help="Repo-relative by default.")
    args = parser.parse_args()

    repo_root = repo_root_from_here()

    input_path = Path(args.input).expanduser().resolve()
    if not input_path.exists():
        print(f"ERROR: input YAML not found: {input_path}", file=sys.stderr)
        return 2

    schema_path = resolve_repo_relative_path(args.schema, repo_root)
    taxonomy_path = resolve_repo_relative_path(args.taxonomy, repo_root)

    if not schema_path.exists():
        print(f"ERROR: schema not found: {schema_path}", file=sys.stderr)
        return 2
    if not taxonomy_path.exists():
        print(f"ERROR: taxonomy not found: {taxonomy_path}", file=sys.stderr)
        return 2

    schema = load_json(schema_path)
    validator = Draft202012Validator(schema)

    allowed_categories = read_taxonomy_categories(taxonomy_path)
    if not allowed_categories:
        print("ERROR: No categories found in taxonomy (expected headings starting with '## ')", file=sys.stderr)
        return 2

    try:
        obj = load_yaml(input_path)
    except Exception as e:
        print(f"Validation FAILED: YAML parse error: {e}", file=sys.stderr)
        return 1

    if not isinstance(obj, dict):
        print("Validation FAILED: YAML root must be an object/mapping.", file=sys.stderr)
        return 1

    issues: List[str] = []
    issues.extend(schema_validate(validator, obj))
    issues.extend(policy_checks(obj, allowed_categories))

    if issues:
        print("Validation FAILED.", file=sys.stderr)
        for i in issues:
            print(f"- {i}", file=sys.stderr)
        return 1

    print("Validation PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
