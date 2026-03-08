#!/usr/bin/env python3
"""
Validate Gruve DFIR TTX scenario YAML files against the canonical JSON schema and basic policy checks.

This script is designed to work no matter what your current working directory is.
All default paths are resolved relative to the repository root (derived from this file’s location).

Dependencies (install if missing):
- PyYAML
- jsonschema

Examples:
  # From repo root (recommended)
  python3 dfir_backend/ttx/scripts/validate_ttx_scenarios.py

  # From any directory (works the same)
  python3 /path/to/repo/dfir_backend/ttx/scripts/validate_ttx_scenarios.py

Optional arguments (repo-relative by default):
  --schema dfir_backend/ttx/schemas/ttx_scenario.schema.json
  --scenarios-dir dfir_backend/ttx/scenarios
  --taxonomy dfir_backend/ttx/scenario_taxonomy.md
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    print("ERROR: Missing dependency PyYAML. Install with: pip install pyyaml", file=sys.stderr)
    raise

try:
    from jsonschema import Draft202012Validator  # type: ignore
except Exception:  # pragma: no cover
    print("ERROR: Missing dependency jsonschema. Install with: pip install jsonschema", file=sys.stderr)
    raise


INJECT_ID_RE = re.compile(r"^i\d{2}$")  # i01, i02, ...


@dataclass
class ValidationIssue:
    file_path: str
    message: str


def repo_root_from_here() -> Path:
    # .../dfir_backend/ttx/scripts/validate_ttx_scenarios.py -> repo root is parents[3]
    return Path(__file__).resolve().parents[3]


def resolve_repo_relative_path(value: str, repo_root: Path) -> Path:
    """
    If value is an absolute path, return it.
    If value is relative, treat it as relative to the repo root (NOT the current working directory).
    """
    p = Path(value).expanduser()
    if not p.is_absolute():
        p = repo_root / p
    return p.resolve()


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


def iter_scenario_files(scenarios_dir: Path) -> List[Path]:
    paths = [
        p
        for p in scenarios_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in (".yaml", ".yml")
    ]
    return sorted(paths)


def schema_validate(
    validator: Draft202012Validator,
    scenario_obj: Any,
    file_path: str,
) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    for err in sorted(validator.iter_errors(scenario_obj), key=lambda e: list(e.path)):
        where = "$"
        if err.path:
            where = "$." + ".".join(str(p) for p in err.path)
        issues.append(ValidationIssue(file_path, f"Schema error at {where}: {err.message}"))
    return issues


def policy_checks(
    scenario_obj: Dict[str, Any],
    file_path: str,
    allowed_categories: Optional[List[str]] = None,
) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []

    scenario = scenario_obj.get("scenario", {})
    injects = scenario_obj.get("injects", [])

    # 1) Category must match taxonomy (if provided).
    category = scenario.get("category")
    if allowed_categories is not None:
        if category not in allowed_categories:
            issues.append(
                ValidationIssue(
                    file_path,
                    f"Policy error: scenario.category '{category}' is not a canonical category from scenario_taxonomy.md",
                )
            )

    # 2) Inject IDs should be iNN (i01, i02, ...).
    for inj in injects:
        inj_id = inj.get("id")
        if not isinstance(inj_id, str) or not INJECT_ID_RE.match(inj_id):
            issues.append(
                ValidationIssue(
                    file_path,
                    f"Policy error: inject.id '{inj_id}' should match pattern iNN (e.g., i01, i02)",
                )
            )

    # 3) Inject times should be non-decreasing and within scenario.duration_minutes.
    duration = scenario.get("duration_minutes")
    if isinstance(duration, int) and duration >= 0:
        last_t: Optional[int] = None
        for inj in injects:
            t = inj.get("t_plus_min")
            if not isinstance(t, int):
                continue
            if last_t is not None and t < last_t:
                issues.append(
                    ValidationIssue(
                        file_path,
                        f"Policy error: injects are out of order (t_plus_min {t} < previous {last_t}). Sort injects by time.",
                    )
                )
            last_t = t
            if t > duration:
                issues.append(
                    ValidationIssue(
                        file_path,
                        f"Policy error: inject t_plus_min {t} exceeds scenario.duration_minutes {duration}.",
                    )
                )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate TTX scenario YAML files.")
    parser.add_argument(
        "--schema",
        default="dfir_backend/ttx/schemas/ttx_scenario.schema.json",
        help="Path to JSON schema for TTX scenarios (repo-relative by default).",
    )
    parser.add_argument(
        "--scenarios-dir",
        default="dfir_backend/ttx/scenarios",
        help="Directory containing scenario YAML files (repo-relative by default).",
    )
    parser.add_argument(
        "--taxonomy",
        default="dfir_backend/ttx/scenario_taxonomy.md",
        help="Path to scenario taxonomy markdown (repo-relative by default).",
    )
    args = parser.parse_args()

    repo_root = repo_root_from_here()

    schema_path = resolve_repo_relative_path(args.schema, repo_root)
    scenarios_dir = resolve_repo_relative_path(args.scenarios_dir, repo_root)
    taxonomy_path = resolve_repo_relative_path(args.taxonomy, repo_root)

    if not schema_path.exists():
        print(f"ERROR: Schema not found: {schema_path}", file=sys.stderr)
        return 2
    if not scenarios_dir.is_dir():
        print(f"ERROR: Scenarios directory not found: {scenarios_dir}", file=sys.stderr)
        return 2
    if not taxonomy_path.exists():
        print(f"ERROR: Taxonomy not found: {taxonomy_path}", file=sys.stderr)
        return 2

    schema = load_json(schema_path)
    validator = Draft202012Validator(schema)

    allowed_categories = read_taxonomy_categories(taxonomy_path)
    if not allowed_categories:
        print("ERROR: No categories found in taxonomy. Expected Markdown headings starting with '## '", file=sys.stderr)
        return 2

    scenario_files = iter_scenario_files(scenarios_dir)
    if not scenario_files:
        print(f"ERROR: No scenario YAML files found under: {scenarios_dir}", file=sys.stderr)
        return 2

    all_issues: List[ValidationIssue] = []
    for path in scenario_files:
        try:
            obj = load_yaml(path)
        except Exception as e:
            all_issues.append(ValidationIssue(str(path), f"YAML parse error: {e}"))
            continue

        if not isinstance(obj, dict):
            all_issues.append(ValidationIssue(str(path), "YAML root must be a mapping/object."))
            continue

        all_issues.extend(schema_validate(validator, obj, str(path)))
        all_issues.extend(policy_checks(obj, str(path), allowed_categories=allowed_categories))

    if all_issues:
        print("TTX validation FAILED.\n", file=sys.stderr)
        for issue in all_issues:
            print(f"- {issue.file_path}: {issue.message}", file=sys.stderr)
        print("\nFix issues above and re-run validation.", file=sys.stderr)
        return 1

    print(f"TTX validation PASSED ({len(scenario_files)} scenario file(s) checked).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
