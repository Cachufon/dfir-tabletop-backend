#!/usr/bin/env python3
"""
Validate TTX scenario library assets:
- reference catalog
- inject bank YAML files
- module map YAML files
- cross-link checks between references, inject ids, and module slots
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import yaml  # type: ignore
from jsonschema import Draft202012Validator  # type: ignore


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[3]


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def schema_issues(validator: Draft202012Validator, obj: Any, label: str) -> List[str]:
    issues: List[str] = []
    for err in sorted(validator.iter_errors(obj), key=lambda e: list(e.path)):
        where = "$"
        if err.path:
            where = "$." + ".".join(str(p) for p in err.path)
        issues.append(f"{label}: schema error at {where}: {err.message}")
    return issues


def gather_reference_ids(catalog_obj: Dict[str, Any]) -> Tuple[Set[str], List[str]]:
    issues: List[str] = []
    refs = catalog_obj.get("references")
    ref_ids: Set[str] = set()
    if not isinstance(refs, list):
        issues.append("reference_catalog.yaml: 'references' must be a list")
        return ref_ids, issues
    for idx, entry in enumerate(refs):
        label = f"reference_catalog.yaml references[{idx}]"
        if not isinstance(entry, dict):
            issues.append(f"{label}: entry must be an object")
            continue
        for field in ("id", "title", "url", "publisher", "why_it_matters"):
            if field not in entry:
                issues.append(f"{label}: missing required field '{field}'")
        ref_id = entry.get("id")
        if isinstance(ref_id, str):
            if ref_id in ref_ids:
                issues.append(f"{label}: duplicate reference id '{ref_id}'")
            ref_ids.add(ref_id)
    return ref_ids, issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate TTX scenario library")
    parser.add_argument("--repo-root", default=None, help="Repo root path (defaults from script location)")
    parser.add_argument("--verbose", action="store_true", help="Print additional progress")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve() if args.repo_root else repo_root_from_here()

    library_dir = repo_root / "dfir_backend" / "ttx" / "library"
    schemas_dir = repo_root / "dfir_backend" / "ttx" / "schemas"

    reference_catalog_path = library_dir / "reference_catalog.yaml"
    inject_bank_schema_path = schemas_dir / "ttx_inject_bank.schema.json"
    module_map_schema_path = schemas_dir / "ttx_module_map.schema.json"
    inject_bank_dir = library_dir / "inject_bank"
    module_maps_dir = library_dir / "module_maps"

    issues: List[str] = []

    required_paths = [
        reference_catalog_path,
        inject_bank_schema_path,
        module_map_schema_path,
        inject_bank_dir,
        module_maps_dir,
    ]
    for p in required_paths:
        if not p.exists():
            issues.append(f"Missing required path: {p}")
    if issues:
        for i in issues:
            print(f"ERROR: {i}", file=sys.stderr)
        return 1

    try:
        catalog_obj = load_yaml(reference_catalog_path)
    except Exception as exc:
        print(f"ERROR: failed to load {reference_catalog_path}: {exc}", file=sys.stderr)
        return 1

    if not isinstance(catalog_obj, dict):
        print("ERROR: reference_catalog.yaml root must be an object", file=sys.stderr)
        return 1

    catalog_ref_ids, catalog_issues = gather_reference_ids(catalog_obj)
    issues.extend(catalog_issues)

    inject_bank_schema = load_json(inject_bank_schema_path)
    module_map_schema = load_json(module_map_schema_path)
    inject_validator = Draft202012Validator(inject_bank_schema)
    module_validator = Draft202012Validator(module_map_schema)

    inject_bank_paths = sorted(p for p in inject_bank_dir.glob("*.yaml") if p.is_file())
    module_map_paths = sorted(p for p in module_maps_dir.glob("*.yaml") if p.is_file())

    inject_registry: Dict[str, Path] = {}

    for inject_path in inject_bank_paths:
        if args.verbose:
            print(f"Checking inject bank: {inject_path}")
        try:
            obj = load_yaml(inject_path)
        except Exception as exc:
            issues.append(f"{inject_path}: YAML parse error: {exc}")
            continue
        issues.extend(schema_issues(inject_validator, obj, str(inject_path)))
        if not isinstance(obj, dict):
            continue
        injects = obj.get("injects", [])
        if not isinstance(injects, list):
            continue
        for idx, item in enumerate(injects):
            if not isinstance(item, dict):
                continue
            inject_id = item.get("id")
            if isinstance(inject_id, str):
                if inject_id in inject_registry:
                    issues.append(
                        f"{inject_path}: duplicate inject id '{inject_id}' already defined in {inject_registry[inject_id]}"
                    )
                else:
                    inject_registry[inject_id] = inject_path

            inject_obj = item.get("inject", {})
            if isinstance(inject_obj, dict):
                for ref in inject_obj.get("evidence_refs", []) if isinstance(inject_obj.get("evidence_refs", []), list) else []:
                    if not isinstance(ref, str):
                        continue
                    if ref.startswith("REF_") and ref not in catalog_ref_ids:
                        issues.append(
                            f"{inject_path} injects[{idx}] id={inject_id}: evidence_refs entry '{ref}' not found in reference_catalog.yaml"
                        )

    for module_map_path in module_map_paths:
        if args.verbose:
            print(f"Checking module map: {module_map_path}")
        try:
            obj = load_yaml(module_map_path)
        except Exception as exc:
            issues.append(f"{module_map_path}: YAML parse error: {exc}")
            continue
        issues.extend(schema_issues(module_validator, obj, str(module_map_path)))
        if not isinstance(obj, dict):
            continue
        profiles = obj.get("profiles", {})
        if not isinstance(profiles, dict):
            continue
        for profile_name, profile_obj in profiles.items():
            if not isinstance(profile_obj, dict):
                continue
            modules = profile_obj.get("modules", [])
            if not isinstance(modules, list):
                continue
            ordered_t_plus: List[int] = []
            for module_idx, module in enumerate(modules):
                if not isinstance(module, dict):
                    continue
                refs = module.get("references", [])
                if isinstance(refs, list):
                    for ref in refs:
                        if isinstance(ref, str) and ref.startswith("REF_") and ref not in catalog_ref_ids:
                            issues.append(
                                f"{module_map_path} profiles.{profile_name}.modules[{module_idx}]: reference '{ref}' not found in reference_catalog.yaml"
                            )

                slots = module.get("inject_slots", [])
                if not isinstance(slots, list):
                    continue
                for slot_idx, slot in enumerate(slots):
                    if not isinstance(slot, dict):
                        continue
                    inject_id = slot.get("inject_id")
                    if isinstance(inject_id, str) and inject_id not in inject_registry:
                        issues.append(
                            f"{module_map_path} profiles.{profile_name}.modules[{module_idx}].inject_slots[{slot_idx}]: inject_id '{inject_id}' not found in loaded inject banks"
                        )
                    t_plus = slot.get("t_plus_min")
                    if isinstance(t_plus, int):
                        ordered_t_plus.append(t_plus)

            for i in range(1, len(ordered_t_plus)):
                if ordered_t_plus[i] <= ordered_t_plus[i - 1]:
                    issues.append(
                        f"{module_map_path} profiles.{profile_name}: inject_slots t_plus_min must be strictly increasing; got {ordered_t_plus[i - 1]} then {ordered_t_plus[i]}"
                    )

    if issues:
        print("TTX library validation FAILED.", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    print("TTX library validation PASSED.")
    if args.verbose:
        print(f"Catalog references: {len(catalog_ref_ids)}")
        print(f"Inject bank files: {len(inject_bank_paths)}")
        print(f"Module map files: {len(module_map_paths)}")
        print(f"Inject IDs loaded: {len(inject_registry)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
