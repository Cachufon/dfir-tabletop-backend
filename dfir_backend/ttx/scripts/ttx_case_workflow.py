#!/usr/bin/env python3
"""
Guided CLI workflow runner for the TTX state machine.

Goals:
- Minimal, guided prompts (not a huge menu)
- Show the current state + "next recommended step"
- After each action: pause, then clear screen so you don't scroll hunting for the menu
- Launch Streamlit in *facilitator mode* only (case-aware)

Usage:
  python3 dfir_backend/ttx/scripts/ttx_case_workflow.py --case-dir /secure_storage/ttx/<case_id>

SAFETY:
- Case folders must be outside git. This runner refuses to operate on case folders inside the repo unless --allow-in-repo is set.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


class Ansi:
    enabled = not bool(os.environ.get("NO_COLOR"))
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"


def colorize(text: str, *styles: str) -> str:
    if not Ansi.enabled:
        return text
    return "".join(styles) + text + Ansi.RESET


def print_success(text: str) -> None:
    print(colorize(text, Ansi.GREEN, Ansi.BOLD))


def print_error(text: str) -> None:
    print(colorize(text, Ansi.RED, Ansi.BOLD))


def status_dot(status: str) -> str:
    dot = "●"
    if status == "OK":
        return f"{colorize(dot, Ansi.GREEN)} {status}" if Ansi.enabled else f"{dot} {status}"
    if status == "WARN":
        return f"{colorize(dot, Ansi.YELLOW)} {status}" if Ansi.enabled else f"{dot} {status}"
    return f"{colorize(dot, Ansi.RED)} {status}" if Ansi.enabled else f"{dot} {status}"


def repo_root_from_here() -> Path:
    # .../dfir_backend/ttx/scripts/ttx_case_workflow.py -> repo root is parents[3]
    return Path(__file__).resolve().parents[3]


def is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except Exception:
        return False


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, obj: Dict[str, Any]) -> None:
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def pause() -> None:
    input("\nPress Enter to continue...")


def clear_screen() -> None:
    # ANSI clear screen + home cursor
    print("\033[2J\033[H", end="")


def prompt(text: str, default: str = "") -> str:
    if default:
        val = input(f"{text} [{default}]: ").strip()
        return val if val else default
    return input(f"{text}: ").strip()


def yes_no(question: str, default_no: bool = True) -> bool:
    suffix = " [y/N]" if default_no else " [Y/n]"
    val = input(question + suffix + ": ").strip().lower()
    if not val:
        return not default_no
    return val in ("y", "yes")


def resolve_case_path(case_dir: Path, rel: str) -> Path:
    return (case_dir / rel).resolve()


def file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except Exception:
        return 0


def parse_intake_labels_and_sections(intake_path: Path) -> Tuple[bool, List[str]]:
    text = intake_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    required_labels = ["Client / Organization:", "Timezone:", "Duration:"]
    labels_complete = True
    for label in required_labels:
        label_pattern = re.compile(rf"^\s*(?:-\s*)?{re.escape(label)}\s*(.*?)\s*$")
        matched = [label_pattern.match(line) for line in lines]
        matched = [m for m in matched if m]
        if not matched:
            labels_complete = False
            continue
        if not any(m.group(1).strip() for m in matched):
            labels_complete = False

    required_headings = ["### Primary objectives", "### Crown jewels"]

    def has_non_empty_bullet(heading: str) -> bool:
        heading_prefix = heading.lower()
        heading_indices = [i for i, line in enumerate(lines) if line.strip().lower().startswith(heading_prefix)]
        if not heading_indices:
            return False
        for start_idx in heading_indices:
            for line in lines[start_idx + 1 :]:
                stripped = line.strip()
                if stripped.startswith("### ") or stripped.startswith("## ") or stripped.startswith("# "):
                    break
                if stripped.startswith("- ") and stripped[2:].strip():
                    return True
        return False

    missing_sections = [heading.replace("### ", "", 1) for heading in required_headings if not has_non_empty_bullet(heading)]
    return labels_complete, missing_sections


def compute_inputs_status(case_dir: Path, manifest: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    inputs = manifest.get("inputs", {})
    checks = [
        ("intake_notes", inputs.get("intake_notes_path", "10_inputs/intake_notes.md"), 500, True),
        ("ir_plan", inputs.get("ir_plan_path", "10_inputs/ir_plan.txt"), 200, False),
        ("ir_plan_profile", "10_inputs/ir_plan_profile.json", 100, False),
        ("threat_brief", inputs.get("threat_brief_path", "10_inputs/threat_brief.md"), 100, False),
    ]
    status: Dict[str, Dict[str, Any]] = {}
    for key, rel_path, min_bytes, required in checks:
        abs_path = resolve_case_path(case_dir, str(rel_path))
        exists = abs_path.exists()
        size_bytes = file_size(abs_path) if exists else 0
        state = "MISSING"
        reason = "Not found"
        if exists and size_bytes >= min_bytes:
            state = "OK"
            reason = f"Size {size_bytes} bytes"
        elif exists:
            state = "WARN"
            reason = f"Size {size_bytes} bytes (< {min_bytes})"
        elif not required:
            reason = "Optional input not provided"

        status[key] = {
            "required": required,
            "rel_path": str(rel_path),
            "abs_path": abs_path,
            "exists": exists,
            "size_bytes": size_bytes,
            "status": state,
            "reason": reason,
        }

    intake_path = status["intake_notes"]["abs_path"]
    if status["intake_notes"]["status"] != "MISSING":
        try:
            labels_complete, missing_sections = parse_intake_labels_and_sections(intake_path)
            intake_warnings: List[str] = []
            if not labels_complete:
                intake_warnings.append("One or more required intake labels are blank")
            if missing_sections:
                intake_warnings.append(f"Missing bullets under: {', '.join(missing_sections)}")
            if intake_warnings and status["intake_notes"]["status"] == "OK":
                status["intake_notes"]["status"] = "WARN"
            if intake_warnings:
                status["intake_notes"]["reason"] = "; ".join(intake_warnings)
        except Exception as exc:
            status["intake_notes"]["status"] = "WARN"
            status["intake_notes"]["reason"] = f"Unable to parse intake notes: {exc}"

    return status


def format_mtime(path: Path) -> str:
    if not path.exists():
        return "-"
    return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(timespec="seconds")


def update_manifest(manifest: Dict[str, Any], event: str, to_state: str, note: str) -> None:
    from_state = manifest.get("state")
    manifest["state"] = to_state
    manifest["last_updated_at_utc"] = now_iso()
    manifest.setdefault("history", [])
    manifest["history"].append(
        {
            "at_utc": now_iso(),
            "event": event,
            "from_state": from_state,
            "to_state": to_state,
            "note": note,
        }
    )


def best_effort_autoadvance(case_dir: Path, manifest: Dict[str, Any]) -> None:
    scenario_path = resolve_case_path(case_dir, manifest["scenario"]["scenario_yaml_path"])
    package_dir = resolve_case_path(case_dir, manifest["package"]["package_dir"])
    handouts_dir = resolve_case_path(case_dir, manifest["handouts"]["handouts_dir"])
    logs_path = resolve_case_path(case_dir, manifest["outputs"]["scribe_runtime_json_path"])
    aar_path = resolve_case_path(case_dir, manifest["outputs"]["aar_draft_path"])

    state = manifest.get("state", "S1_CASE_INITIALIZED")

    if scenario_path.exists() and state in ("S1_CASE_INITIALIZED", "S2_INPUTS_COLLECTED"):
        update_manifest(manifest, "autoadvance", "S3_SCENARIO_DRAFTED", "scenario.yaml exists")

    if manifest["scenario"].get("validated") and state in ("S3_SCENARIO_DRAFTED",):
        update_manifest(manifest, "autoadvance", "S4_SCENARIO_VALIDATED", "scenario validated (manifest flag)")

    if manifest["scenario"].get("approved") and state in ("S4_SCENARIO_VALIDATED", "S3_SCENARIO_DRAFTED"):
        update_manifest(manifest, "autoadvance", "S4_SCENARIO_APPROVED", "scenario approved (manifest flag)")

    if package_dir.is_dir() and (package_dir / "package_manifest.md").exists():
        if state not in ("S5_PACKAGE_BUILT", "S6_HANDOUTS_EXPORTED", "S7_FACILITATION_IN_PROGRESS", "S8_LOGS_EXPORTED", "S9_AAR_DRAFTED", "S10_CLOSED"):
            update_manifest(manifest, "autoadvance", "S5_PACKAGE_BUILT", "package_manifest.md exists")

    if handouts_dir.is_dir() and (handouts_dir / "index.html").exists():
        if state not in ("S6_HANDOUTS_EXPORTED", "S7_FACILITATION_IN_PROGRESS", "S8_LOGS_EXPORTED", "S9_AAR_DRAFTED", "S10_CLOSED"):
            update_manifest(manifest, "autoadvance", "S6_HANDOUTS_EXPORTED", "handouts index.html exists")

    if logs_path.exists():
        if state not in ("S8_LOGS_EXPORTED", "S9_AAR_DRAFTED", "S10_CLOSED"):
            update_manifest(manifest, "autoadvance", "S8_LOGS_EXPORTED", "scribe_runtime.json exists")

    if aar_path.exists():
        if state not in ("S9_AAR_DRAFTED", "S10_CLOSED"):
            update_manifest(manifest, "autoadvance", "S9_AAR_DRAFTED", "AAR draft exists")


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


def list_repo_scenarios(repo_root: Path) -> List[Path]:
    scenarios_dir = repo_root / "dfir_backend" / "ttx" / "scenarios"
    if not scenarios_dir.exists():
        return []
    files = sorted(list(scenarios_dir.rglob("*.yaml")) + list(scenarios_dir.rglob("*.yml")))
    files = [p for p in files if "_build" not in str(p)]
    return files


def choose_from_list(items: List[Path], label: str) -> Optional[Path]:
    def display_label(path: Path) -> str:
        basename = path.name
        try:
            scenario_doc = yaml.safe_load(path.read_text(encoding="utf-8"))
            if isinstance(scenario_doc, dict):
                scenario_section = scenario_doc.get("scenario")
                if isinstance(scenario_section, dict):
                    scenario_title = str(scenario_section.get("title", "")).strip()
                    if scenario_title:
                        return f"{basename} — {scenario_title}"
        except Exception:
            pass
        return basename

    if not items:
        return None
    print(f"\n{label}")
    for i, p in enumerate(items, start=1):
        print(f"{i}) {display_label(p)}")
    raw = input("Choose by number (or blank to cancel): ").strip()
    if not raw:
        return None
    if raw.isdigit():
        idx = int(raw)
        if 1 <= idx <= len(items):
            return items[idx - 1]
    print("Invalid selection.")
    return None


def read_taxonomy_categories(repo_root: Path) -> List[str]:
    taxonomy = repo_root / "dfir_backend" / "ttx" / "scenario_taxonomy.md"
    if not taxonomy.exists():
        return []
    cats: List[str] = []
    for line in taxonomy.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("## Category naming rules"):
            continue
        if line.startswith("## "):
            c = line.replace("## ", "", 1).strip()
            if c:
                cats.append(c)
    return cats


def run_cmd(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)


def run_cmd_interactive(cmd: List[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), text=True)


def recommended_step(case_dir: Path, manifest: Dict[str, Any]) -> Tuple[str, str]:
    """
    Returns (step_key, human_text).
    step_key is a stable identifier used by 'Continue'.
    """
    scenario_yaml = resolve_case_path(case_dir, manifest["scenario"]["scenario_yaml_path"])
    package_dir = resolve_case_path(case_dir, manifest["package"]["package_dir"])
    handouts_dir = resolve_case_path(case_dir, manifest["handouts"]["handouts_dir"])
    logs_path = resolve_case_path(case_dir, manifest["outputs"]["scribe_runtime_json_path"])
    aar_path = resolve_case_path(case_dir, manifest["outputs"]["aar_draft_path"])
    executive_readout = resolve_case_path(case_dir, manifest["outputs"]["executive_readout_path"])

    inputs_complete = bool(manifest["inputs"].get("inputs_complete", False))
    if not inputs_complete:
        return ("REVIEW_INPUTS", "Review inputs checklist (questionnaire/IRP paths) and mark complete")

    if not str(manifest["scenario"].get("category", "")).strip():
        return ("SET_SCENARIO_META", "Set scenario category + title hint")

    if not scenario_yaml.exists():
        return ("DRAFT_SCENARIO", "Create scenario.yaml (Option A base scenario OR Option B AI bundle OR Option C compile from library)")

    if not manifest["scenario"].get("validated", False):
        return ("VALIDATE_SCENARIO", "Validate scenario.yaml (deterministic gate)")

    if not manifest["scenario"].get("approved", False):
        return ("APPROVE_SCENARIO", "Record facilitator approval")

    if not (package_dir.is_dir() and (package_dir / "package_manifest.md").exists()):
        return ("BUILD_PACKAGE", "Build scenario package (ttx_package/)")

    if not logs_path.exists():
        return ("FACILITATE", "Launch facilitation UI (Facilitate + Scribe)")

    if logs_path.exists() and not aar_path.exists():
        return ("GENERATE_AAR", "Generate AAR draft")

    if aar_path.exists():
        return ("CLOSE_CASE", "Close case (AAR draft exists)")

    if not executive_readout.exists():
        return ("GENERATE_EXEC_READOUT", "Generate Executive Readout (draft + AI bundle + optional AI)")

    return ("CLOSE_CASE", "Close case (S10)")


def print_header(case_dir: Path, manifest: Dict[str, Any]) -> None:
    scenario_yaml = resolve_case_path(case_dir, manifest["scenario"]["scenario_yaml_path"])
    package_dir = resolve_case_path(case_dir, manifest["package"]["package_dir"])
    handouts_dir = resolve_case_path(case_dir, manifest["handouts"]["handouts_dir"])
    runtime_json = resolve_case_path(case_dir, manifest["outputs"]["scribe_runtime_json_path"])
    aar_path = resolve_case_path(case_dir, manifest["outputs"]["aar_draft_path"])
    executive_readout_path = resolve_case_path(case_dir, manifest["outputs"]["executive_readout_path"])

    step_key, step_text = recommended_step(case_dir, manifest)
    input_status = compute_inputs_status(case_dir, manifest)
    intake_state = input_status["intake_notes"]["status"]
    ir_state = input_status["ir_plan"]["status"]
    threat_state = input_status["threat_brief"]["status"]
    profile_state = input_status["ir_plan_profile"]["status"]

    print(colorize("============================================================", Ansi.CYAN, Ansi.BOLD))
    print(colorize("TTX Case Workflow", Ansi.CYAN, Ansi.BOLD))
    print(colorize("============================================================", Ansi.CYAN, Ansi.BOLD))
    print(f"Case dir : {case_dir}")
    print(f"Case ID  : {manifest.get('case_id','')}")
    print(f"State    : {manifest.get('state','')}")
    print(colorize("------------------------------------------------------------", Ansi.CYAN))
    print(f"Bundle   : {manifest.get('bundle_type','')} • {manifest.get('duration_minutes','')} min • {manifest.get('timezone','')}")
    print(f"Handling : {handling_label_from_manifest(manifest)}")
    print(f"Scenario : {manifest['scenario'].get('category','(unset)')} • validated={manifest['scenario'].get('validated')} • approved={manifest['scenario'].get('approved')}")
    print("Inputs:")
    print(f"  {status_dot(intake_state)} intake_notes")
    print(f"  {status_dot(ir_state)} ir_plan (optional)")
    print(f"  {status_dot(threat_state)} threat_brief (optional)")
    print(f"  {status_dot(profile_state)} ir_plan_profile (optional/recommended)")
    print("Locations:")
    print(f"  - intake_notes.md: {input_status['intake_notes']['abs_path']}")
    print(f"  - ir_plan.txt: {input_status['ir_plan']['abs_path']}")
    print(f"  - ir_plan_profile.json: {input_status['ir_plan_profile']['abs_path']}")
    print(f"  - threat_brief.md: {input_status['threat_brief']['abs_path']}")
    print("Outputs:")
    print(f"  {status_dot('OK' if scenario_yaml.exists() else 'MISSING')} scenario.yaml")
    print(f"  {status_dot('OK' if package_dir.is_dir() else 'MISSING')} package")
    print(f"  {status_dot('OK' if handouts_dir.is_dir() else 'MISSING')} handouts")
    print(f"  {status_dot('OK' if runtime_json.exists() else 'MISSING')} runtime")
    print(f"  {status_dot('OK' if aar_path.exists() else 'MISSING')} aar")
    print(f"  {status_dot('OK' if executive_readout_path.exists() else 'MISSING')} exec readout")
    print(colorize("------------------------------------------------------------", Ansi.CYAN))
    print(f"Next     : {step_text}")
    print(colorize("============================================================", Ansi.CYAN, Ansi.BOLD))


def action_review_inputs(case_dir: Path, manifest: Dict[str, Any]) -> None:
    print("\nInputs tracker review")
    print("------------------------------------------------------------")
    statuses = compute_inputs_status(case_dir, manifest)
    ir_plan_mapper_cmd = f"{sys.executable} dfir_backend/ttx/scripts/run_ir_plan_mapper.py --case-dir {case_dir}"
    for key, label in (("intake_notes", "intake_notes.md"), ("ir_plan", "ir_plan.txt"), ("ir_plan_profile", "ir_plan_profile.json"), ("threat_brief", "threat_brief.md")):
        item = statuses[key]
        print(f"{label}: {item['status']}")
        print(f"  relative: {item['rel_path']}")
        print(f"  absolute: {item['abs_path']}")
        print(f"  modified: {format_mtime(item['abs_path'])}")
        details = item["reason"]
        if key == "ir_plan_profile" and item["status"] == "MISSING":
            details = f"{details}; generate with: {ir_plan_mapper_cmd}"
        print(f"  details : {details}")

    if statuses["intake_notes"]["status"] == "WARN":
        if yes_no("Run quick intake wizard now?", default_no=True):
            wizard = repo_root_from_here() / "dfir_backend" / "ttx" / "scripts" / "run_quick_intake_wizard.py"
            if not wizard.exists():
                print_error(f"ERROR: quick intake wizard script not found: {wizard}")
            else:
                proc = run_cmd_interactive([sys.executable, str(wizard), "--case-dir", str(case_dir)], cwd=repo_root_from_here())
                if proc.returncode != 0:
                    print_error("ERROR: quick intake wizard failed.")
                else:
                    print_success("SUCCESS: quick intake wizard completed.")
                    statuses = compute_inputs_status(case_dir, manifest)
                    refreshed = statuses["intake_notes"]
                    print(f"Refreshed intake status: {refreshed['status']} ({refreshed['reason']})")

    if statuses["ir_plan_profile"]["status"] == "MISSING":
        if yes_no("Run IR plan mapper wizard now? (optional/recommended)", default_no=True):
            mapper = repo_root_from_here() / "dfir_backend" / "ttx" / "scripts" / "run_ir_plan_mapper.py"
            if not mapper.exists():
                print_error(f"ERROR: IR plan mapper script not found: {mapper}")
            else:
                proc = run_cmd_interactive([sys.executable, str(mapper), "--case-dir", str(case_dir)], cwd=repo_root_from_here())
                if proc.returncode != 0:
                    print_error("ERROR: IR plan mapper wizard failed.")
                else:
                    print_success("SUCCESS: IR plan mapper wizard completed.")
                    statuses = compute_inputs_status(case_dir, manifest)
                    refreshed = statuses["ir_plan_profile"]
                    print(f"Refreshed ir_plan_profile status: {refreshed['status']} ({refreshed['reason']})")

    tracker_path = resolve_case_path(case_dir, "00_admin/inputs_tracker.md")
    print(f"inputs_tracker.md: {tracker_path}")
    if manifest["inputs"].get("inputs_complete", False):
        print("Inputs are already marked complete in the manifest.")

    if not yes_no("Mark inputs complete now?", default_no=True):
        print("Inputs remain not complete.")
        return

    intake_state = statuses["intake_notes"]["status"]
    forced_completion = False
    if intake_state in ("WARN", "MISSING"):
        force = input("Intake status is WARN/MISSING. Type FORCE to proceed (case-insensitive): ").strip()
        if force.lower() != "force":
            print("Inputs not marked complete.")
            return
        forced_completion = True

    manifest["inputs"]["inputs_complete"] = True
    note = "Inputs reviewed and marked complete via tracker."
    if forced_completion:
        note = "Inputs marked complete with WARN status (forced)."
    update_manifest(
        manifest,
        "mark_inputs_collected",
        "S2_INPUTS_COLLECTED",
        note,
    )

    manifest_path = case_dir / "case_manifest.json"
    write_json(manifest_path, manifest)
    manifest_reloaded = read_json(manifest_path)
    if not bool(manifest_reloaded.get("inputs", {}).get("inputs_complete", False)):
        print_error("ERROR: inputs_complete verification failed after save.")
        raise SystemExit(1)

    step_key, _ = recommended_step(case_dir, manifest_reloaded)
    print(f"inputs_complete=true saved. Next recommended step: {step_key}")
    print_success("SUCCESS: inputs reviewed and marked complete.")


def action_set_scenario_meta(repo_root: Path, case_dir: Path, manifest: Dict[str, Any]) -> None:
    cats = read_taxonomy_categories(repo_root)
    if not cats:
        print_error("ERROR: taxonomy categories not found. Ensure dfir_backend/ttx/scenario_taxonomy.md exists.")
        return
    print("\nCanonical categories:")
    for i, c in enumerate(cats, start=1):
        print(f"{i}) {c}")
    raw = input("Choose category by number (or type exact text): ").strip()

    category = ""
    if raw.isdigit():
        idx = int(raw)
        if 1 <= idx <= len(cats):
            category = cats[idx - 1]
    else:
        category = raw

    if category not in cats:
        print_error("ERROR: category must match taxonomy exactly.")
        return

    title_hint = prompt("Scenario title hint", manifest["scenario"].get("title_hint", ""))

    manifest["scenario"]["category"] = category
    manifest["scenario"]["title_hint"] = title_hint.strip()
    update_manifest(manifest, "set_scenario_metadata", manifest.get("state", "S1_CASE_INITIALIZED"), "Scenario category/title hint updated.")
    print_success("SUCCESS: scenario metadata updated.")


def action_draft_scenario(repo_root: Path, case_dir: Path, manifest: Dict[str, Any], overwrite: bool) -> None:
    scenario_yaml = resolve_case_path(case_dir, manifest["scenario"]["scenario_yaml_path"])
    print("\nDraft scenario.yaml")
    print("1) Option A: Copy a base scenario from the repo library (fast, deterministic)")
    print("2) Option B: Build an AI bundle for bespoke YAML (NO AI called by repo)")
    print("3) Compile from Library (Option C; deterministic; no AI)")
    print("   Uses validated library content + case inputs to compile scenario.yaml.")
    print("4) Cancel")
    choice = input("Choose (1-4): ").strip()

    if choice == "1":
        scenarios = list_repo_scenarios(repo_root)
        if not scenarios:
            print_error("ERROR: No repo scenarios found under dfir_backend/ttx/scenarios/")
            return
        manifest_category = str(manifest.get("scenario", {}).get("category", "")).strip()
        if manifest_category:
            filtered_scenarios: List[Path] = []
            for scenario_path in scenarios:
                try:
                    scenario_doc = yaml.safe_load(scenario_path.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if not isinstance(scenario_doc, dict):
                    continue
                scenario_section = scenario_doc.get("scenario")
                if not isinstance(scenario_section, dict):
                    continue
                scenario_category = str(scenario_section.get("category", "")).strip()
                if scenario_category == manifest_category:
                    filtered_scenarios.append(scenario_path)

            if filtered_scenarios:
                scenarios = filtered_scenarios
            else:
                print(f"WARN: No repo scenarios matched manifest category '{manifest_category}'. Showing all scenarios.")

        sel = choose_from_list(scenarios, "Select a base scenario to copy into this case:")
        if sel is None:
            return
        if scenario_yaml.exists() and not yes_no("scenario.yaml already exists. Overwrite it?", default_no=True):
            print("Aborted.")
            return

        scenario_yaml.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(sel, scenario_yaml)

        try:
            selected_doc = yaml.safe_load(sel.read_text(encoding="utf-8"))
        except Exception:
            selected_doc = None
        selected_category = ""
        selected_title = ""
        if isinstance(selected_doc, dict):
            selected_section = selected_doc.get("scenario")
            if isinstance(selected_section, dict):
                selected_category = str(selected_section.get("category", "")).strip()
                selected_title = str(selected_section.get("title", "")).strip()

        previous_category = str(manifest.get("scenario", {}).get("category", "")).strip()
        manifest["scenario"]["category"] = selected_category
        if previous_category != selected_category:
            print(f"INFO: Scenario category updated from '{previous_category or '-'}' to '{selected_category or '-'}'.")
        if not str(manifest["scenario"].get("title_hint", "")).strip() and selected_title:
            manifest["scenario"]["title_hint"] = selected_title

        tailorer = repo_root / "dfir_backend" / "ttx" / "scripts" / "tailor_base_scenario_from_intake.py"
        if yes_no("Auto-tailor base scenario from intake now? (recommended)", default_no=True):
            if not tailorer.exists():
                print_error(f"ERROR: base scenario tailorer not found: {tailorer}")
                return
            p = run_cmd([sys.executable, str(tailorer), "--case-dir", str(case_dir)], cwd=repo_root)
            if p.returncode != 0:
                print_error("ERROR: base scenario tailoring FAILED.")
                print(p.stderr or p.stdout)
                return
            if p.stdout.strip():
                print(p.stdout.strip())

        manifest["scenario"]["draft_method"] = "BASE_SCENARIO"
        update_manifest(manifest, "copy_base_scenario", "S3_SCENARIO_DRAFTED", f"Copied base scenario from repo: {sel}")

        print_success(f"SUCCESS: scenario.yaml created: {scenario_yaml}")
        print("Next: tailor scenario.yaml for the client, then validate and approve.")

    elif choice == "2":
        ai_bundle = repo_root / "dfir_backend" / "ttx" / "scripts" / "build_ttx_scenario_ai_bundle_from_case.py"
        if not ai_bundle.exists():
            print_error(f"ERROR: AI bundle builder not found: {ai_bundle}")
            return
        if not str(manifest["scenario"].get("category", "")).strip():
            print_error("ERROR: scenario category is not set. Set category first.")
            return

        cmd = [sys.executable, str(ai_bundle), "--case-dir", str(case_dir)]
        p = run_cmd(cmd, cwd=repo_root)
        if p.returncode != 0:
            print_error("ERROR: AI bundle generation FAILED.")
            print(p.stderr or p.stdout)
            return

        manifest["scenario"]["draft_method"] = "AI_ASSISTED"
        update_manifest(manifest, "build_ai_bundle", "S3_SCENARIO_DRAFTED", "Built AI bundle for bespoke scenario YAML (no AI called).")
        print(p.stdout.strip())

        print("\nNext steps:")
        print("1) Open 10_inputs/ttx_scenario_generation/ttx_scenario_ai_bundle.txt")
        print("2) Paste into your approved AI tool and REQUIRE YAML-only output")
        print("3) Paste YAML into 20_delivery/scenario.yaml (canonical)")
        print("4) Validate and approve before packaging")

    elif choice == "3":
        compiler = repo_root / "dfir_backend" / "ttx" / "scripts" / "compile_ttx_scenario_from_library.py"
        if not compiler.exists():
            print_error(f"ERROR: scenario compiler not found: {compiler}")
            return
        if not bool(manifest.get("inputs", {}).get("inputs_complete", False)):
            print("WARN: inputs_complete is false. Option C compile will run with less-tailored defaults.")
        cmd = [sys.executable, str(compiler), "--case-dir", str(case_dir)]
        if overwrite:
            cmd.append("--force")
        p = run_cmd(cmd, cwd=repo_root)
        if p.returncode != 0:
            print_error("ERROR: scenario compile FAILED.")
            print(p.stderr or p.stdout)
            return

        manifest["scenario"]["draft_method"] = "OPTION_C_COMPILE_FROM_LIBRARY"
        update_manifest(manifest, "compile_scenario_from_library", "S3_SCENARIO_DRAFTED", "Compiled deterministic scenario from library.")
        print_success("SUCCESS: scenario compiled from library.")
        if p.stdout.strip():
            print(p.stdout.strip())
        scenario_yaml_path = case_dir / "20_delivery" / "scenario.yaml"
        print(f"scenario.yaml: {scenario_yaml_path}")
        snapshot_path = case_dir / "20_delivery" / "scenario_inputs_snapshot.json"
        if snapshot_path.exists():
            print(f"scenario_inputs_snapshot.json: {snapshot_path}")
    else:
        print("Cancelled.")
        return


def action_validate_library_and_compile(repo_root: Path, case_dir: Path, manifest: Dict[str, Any], overwrite: bool) -> None:
    library_validator = repo_root / "dfir_backend" / "ttx" / "scripts" / "validate_ttx_library.py"
    compiler = repo_root / "dfir_backend" / "ttx" / "scripts" / "compile_ttx_scenario_from_library.py"

    if not library_validator.exists():
        print_error(f"ERROR: library validator not found: {library_validator}")
        return
    if not compiler.exists():
        print_error(f"ERROR: scenario compiler not found: {compiler}")
        return

    p_validate = run_cmd([sys.executable, str(library_validator)], cwd=repo_root)
    if p_validate.returncode != 0:
        print_error("ERROR: library validation FAILED.")
        print(p_validate.stderr or p_validate.stdout)
        return

    cmd_compile = [sys.executable, str(compiler), "--case-dir", str(case_dir)]
    if overwrite:
        cmd_compile.append("--force")
    p_compile = run_cmd(cmd_compile, cwd=repo_root)
    if p_compile.returncode != 0:
        print_error("ERROR: scenario compile FAILED.")
        print(p_compile.stderr or p_compile.stdout)
        return

    manifest["scenario"]["draft_method"] = "OPTION_C_COMPILE_FROM_LIBRARY"
    update_manifest(manifest, "validate_library_and_compile_scenario", "S3_SCENARIO_DRAFTED", "Validated library and compiled deterministic scenario from library.")
    print_success("SUCCESS: library validated and scenario compiled from library.")
    if p_compile.stdout.strip():
        print(p_compile.stdout.strip())
    scenario_yaml_path = case_dir / "20_delivery" / "scenario.yaml"
    print(f"scenario.yaml: {scenario_yaml_path}")
    snapshot_path = case_dir / "20_delivery" / "scenario_inputs_snapshot.json"
    if snapshot_path.exists():
        print(f"scenario_inputs_snapshot.json: {snapshot_path}")


def action_validate(repo_root: Path, case_dir: Path, manifest: Dict[str, Any]) -> None:
    scenario_yaml = resolve_case_path(case_dir, manifest["scenario"]["scenario_yaml_path"])
    validator_one = repo_root / "dfir_backend" / "ttx" / "scripts" / "validate_ttx_scenario_file.py"

    if not validator_one.exists():
        print_error(f"ERROR: single-file validator not found: {validator_one}")
        return
    if not scenario_yaml.exists():
        print_error(f"ERROR: scenario.yaml not found: {scenario_yaml}")
        return

    cmd = [sys.executable, str(validator_one), "--input", str(scenario_yaml)]
    p = run_cmd(cmd, cwd=repo_root)

    manifest["scenario"]["validation_last_run_utc"] = now_iso()
    if p.returncode == 0:
        manifest["scenario"]["validated"] = True
        manifest["scenario"]["validation_errors"] = []
        update_manifest(manifest, "validate_scenario", "S4_SCENARIO_VALIDATED", "Scenario YAML validated successfully.")
        print_success("SUCCESS: Validation PASSED.")
    else:
        manifest["scenario"]["validated"] = False
        err_lines = (p.stderr or p.stdout or "").splitlines()
        err_lines = [ln.strip() for ln in err_lines if ln.strip()]
        manifest["scenario"]["validation_errors"] = err_lines[:200]
        print_error("ERROR: Validation FAILED.")
        print(p.stderr or p.stdout)


def action_approve(case_dir: Path, manifest: Dict[str, Any]) -> None:
    if not manifest["scenario"].get("validated", False):
        print_error("ERROR: scenario is not validated. Validate first.")
        return

    approver = prompt("Facilitator approver (name or role)", manifest["scenario"].get("approved_by", "") or "DFIR Facilitator")
    manifest["scenario"]["approved"] = True
    manifest["scenario"]["approved_by"] = approver.strip()
    manifest["scenario"]["approved_at_utc"] = now_iso()
    update_manifest(manifest, "approve_scenario", "S4_SCENARIO_APPROVED", f"Scenario approved by {approver.strip()}.")
    print_success("SUCCESS: scenario approved.")


def action_build_package(repo_root: Path, case_dir: Path, manifest: Dict[str, Any]) -> None:
    builder = repo_root / "dfir_backend" / "ttx" / "scripts" / "build_ttx_package_from_yaml.py"
    scenario_yaml = resolve_case_path(case_dir, manifest["scenario"]["scenario_yaml_path"])
    package_dir = resolve_case_path(case_dir, manifest["package"]["package_dir"])

    if not builder.exists():
        print_error(f"ERROR: package builder not found: {builder}")
        return
    if not scenario_yaml.exists():
        print_error("ERROR: scenario.yaml missing. Draft it first.")
        return
    if not manifest["scenario"].get("approved", False):
        print_error("ERROR: scenario not approved. Validate and approve before packaging.")
        return

    package_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(builder),
        "--input",
        str(scenario_yaml),
        "--out-dir",
        str(package_dir),
        "--case-dir",
        str(case_dir),
        "--force",
    ]
    p = run_cmd(cmd, cwd=repo_root)
    if p.returncode != 0:
        print_error("ERROR: Package build FAILED.")
        print(p.stderr or p.stdout)
        return

    manifest["package"]["built"] = True
    manifest["package"]["built_at_utc"] = now_iso()
    update_manifest(manifest, "build_package", "S5_PACKAGE_BUILT", "Generated ttx_package from scenario.yaml.")
    print_success("SUCCESS: package built.")
    print(p.stdout.strip())


def action_export_handouts(repo_root: Path, case_dir: Path, manifest: Dict[str, Any]) -> None:
    exporter = repo_root / "dfir_backend" / "ttx" / "scripts" / "export_ttx_handouts_html.py"
    package_dir = resolve_case_path(case_dir, manifest["package"]["package_dir"])
    handouts_dir = resolve_case_path(case_dir, manifest["handouts"]["handouts_dir"])

    if not exporter.exists():
        print_error(f"ERROR: handouts exporter not found: {exporter}")
        return
    if not package_dir.is_dir():
        print_error("ERROR: package dir not found. Build the package first.")
        return

    make_zip = yes_no("Create ZIP as well? (--zip)", default_no=False)
    cmd = [sys.executable, str(exporter), "--package-dir", str(package_dir), "--out-dir", str(handouts_dir)]
    if make_zip:
        cmd.append("--zip")

    p = run_cmd(cmd, cwd=repo_root)
    if p.returncode != 0:
        print_error("ERROR: Handouts export FAILED.")
        print(p.stderr or p.stdout)
        return

    manifest["handouts"]["exported"] = True
    manifest["handouts"]["exported_at_utc"] = now_iso()
    update_manifest(manifest, "export_handouts", "S6_HANDOUTS_EXPORTED", "Exported participant handouts to offline HTML.")
    print_success("SUCCESS: handouts exported.")
    print(p.stdout.strip())


def action_launch_ui(repo_root: Path, case_dir: Path, manifest: Dict[str, Any]) -> None:
    ui_app = repo_root / "dfir_backend" / "ttx" / "ui" / "ttx_studio.py"
    if not ui_app.exists():
        print_error(f"ERROR: Streamlit UI not found: {ui_app}")
        return

    manifest["facilitation"]["status"] = "IN_PROGRESS"
    if not manifest["facilitation"].get("started_at_utc"):
        manifest["facilitation"]["started_at_utc"] = now_iso()
    update_manifest(manifest, "launch_ui", "S7_FACILITATION_IN_PROGRESS", "Launched Streamlit UI for facilitation.")
    print("\nLaunching Streamlit UI (Facilitator Mode). Close the browser tab and press Ctrl+C to stop.\n")

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(ui_app),
        "--",
        "--mode",
        "facilitate",
        "--case-dir",
        str(case_dir),
    ]
    subprocess.run(cmd, cwd=str(repo_root))


def action_generate_aar(repo_root: Path, case_dir: Path, manifest: Dict[str, Any]) -> None:
    draft_builder = repo_root / "dfir_backend" / "ttx" / "scripts" / "build_aar_draft_from_runtime.py"

    scenario_yaml = resolve_case_path(case_dir, manifest["scenario"]["scenario_yaml_path"])
    runtime_json = resolve_case_path(case_dir, manifest["outputs"]["scribe_runtime_json_path"])
    aar_path = resolve_case_path(case_dir, manifest["outputs"]["aar_draft_path"])

    if not scenario_yaml.exists():
        print_error("ERROR: scenario.yaml missing. Draft/validate package first.")
        return
    if not runtime_json.exists():
        print_error("ERROR: scribe_runtime.json missing. Export logs from facilitation UI first.")
        return

    if not draft_builder.exists():
        print_error("ERROR: AAR script is missing under dfir_backend/ttx/scripts/.")
        return

    print("\nGenerate deterministic AAR draft")
    cmd_draft = [
        sys.executable,
        str(draft_builder),
        "--case-dir",
        str(case_dir),
    ]
    p_draft = run_cmd(cmd_draft, cwd=repo_root)
    if p_draft.returncode != 0:
        print_error("ERROR: Deterministic AAR draft build FAILED.")
        print(p_draft.stderr or p_draft.stdout)
        return
    print_success(f"SUCCESS: deterministic AAR draft created: {aar_path}")

    update_manifest(manifest, "generate_aar", "S9_AAR_DRAFTED", "Generated AAR draft.")


def action_generate_exec_readout(repo_root: Path, case_dir: Path, manifest: Dict[str, Any]) -> None:
    draft_builder = repo_root / "dfir_backend" / "ttx" / "scripts" / "build_executive_readout_draft_from_runtime.py"
    bundle_builder = repo_root / "dfir_backend" / "ttx" / "scripts" / "build_executive_readout_ai_bundle.py"
    ai_generator = repo_root / "dfir_backend" / "ttx" / "scripts" / "generate_markdown_with_openai.py"
    prompt_template = repo_root / "dfir_backend" / "ai_assist" / "prompts" / "ttx_executive_readout_from_runtime.md"

    scenario_yaml = resolve_case_path(case_dir, manifest["scenario"]["scenario_yaml_path"])
    runtime_json = resolve_case_path(case_dir, manifest["outputs"]["scribe_runtime_json_path"])
    executive_readout_path = resolve_case_path(case_dir, manifest["outputs"]["executive_readout_path"])
    out_dir = case_dir / "30_outputs"
    intake_notes = case_dir / "10_inputs" / "intake_notes.md"
    ir_plan = case_dir / "10_inputs" / "ir_plan.txt"
    ai_out_path = out_dir / "executive_readout_ai.md"

    if not scenario_yaml.exists():
        print_error("ERROR: scenario.yaml missing. Draft/validate package first.")
        return
    if not runtime_json.exists():
        print_error("ERROR: scribe_runtime.json missing. Export logs from facilitation UI first.")
        return

    if not draft_builder.exists() or not bundle_builder.exists() or not ai_generator.exists() or not prompt_template.exists():
        print_error("ERROR: one or more executive readout scripts are missing under dfir_backend/ttx/scripts/.")
        return

    print("\nStep 1/3: Generate deterministic executive readout draft")
    cmd_draft = [
        sys.executable,
        str(draft_builder),
        "--scenario-yaml",
        str(scenario_yaml),
        "--runtime-json",
        str(runtime_json),
        "--case-manifest",
        str(case_dir / "case_manifest.json"),
        "--out-path",
        str(executive_readout_path),
    ]
    p_draft = run_cmd(cmd_draft, cwd=repo_root)
    if p_draft.returncode != 0:
        print_error("ERROR: Deterministic executive readout build FAILED.")
        print(p_draft.stderr or p_draft.stdout)
        return
    print_success(f"SUCCESS: deterministic executive readout created: {executive_readout_path}")
    update_manifest(manifest, "generate_executive_readout", manifest.get("state", "S8_LOGS_EXPORTED"), "Generated deterministic executive readout draft.")

    print("\nStep 2/3: Generate AI paste bundle")
    cmd_bundle = [
        sys.executable,
        str(bundle_builder),
        "--scenario-yaml",
        str(scenario_yaml),
        "--runtime-json",
        str(runtime_json),
        "--out-dir",
        str(out_dir),
    ]
    if intake_notes.exists():
        cmd_bundle.extend(["--intake-notes", str(intake_notes)])
    if ir_plan.exists():
        cmd_bundle.extend(["--ir-plan", str(ir_plan)])
    p_bundle = run_cmd(cmd_bundle, cwd=repo_root)
    if p_bundle.returncode != 0:
        print_error("ERROR: Executive readout AI bundle build FAILED.")
        print(p_bundle.stderr or p_bundle.stdout)
        return
    print_success(f"SUCCESS: executive readout AI bundle created: {out_dir / 'executive_readout_ai_bundle.txt'}")

    if not os.environ.get("OPENAI_API_KEY", "").strip():
        print("\nOPENAI_API_KEY not set; skipping optional direct AI generation.")
        return

    if not yes_no("\nGenerate AI version now? (requires client permission)", default_no=True):
        print("Skipped optional AI generation.")
        return

    confirm = input("Type exact confirmation string to continue: I_HAVE_CLIENT_PERMISSION\n> ").strip()
    if confirm != "I_HAVE_CLIENT_PERMISSION":
        print_error("ERROR: Confirmation string mismatch. Skipping network call.")
        return

    cmd_ai = [
        sys.executable,
        str(ai_generator),
        "--prompt-template",
        str(prompt_template),
        "--scenario-yaml",
        str(scenario_yaml),
        "--runtime-json",
        str(runtime_json),
        "--out-path",
        str(ai_out_path),
        "--confirm-send",
        confirm,
    ]
    if intake_notes.exists():
        cmd_ai.extend(["--intake-notes", str(intake_notes)])
    if ir_plan.exists():
        cmd_ai.extend(["--ir-plan", str(ir_plan)])

    p_ai = run_cmd(cmd_ai, cwd=repo_root)
    if p_ai.returncode != 0:
        print_error("ERROR: OpenAI executive readout generation FAILED.")
        print(p_ai.stderr or p_ai.stdout)
        return
    print_success(f"SUCCESS: AI-generated executive readout created: {ai_out_path}")


def action_close_case(manifest: Dict[str, Any]) -> None:
    update_manifest(manifest, "close_case", "S10_CLOSED", "Case closed.")
    print_success("SUCCESS: case closed.")


def action_optional_ai_scenario_enhancement(repo_root: Path, case_dir: Path, manifest: Dict[str, Any]) -> None:
    scenario_yaml = resolve_case_path(case_dir, manifest["scenario"]["scenario_yaml_path"])
    enhancer = repo_root / "dfir_backend" / "ttx" / "scripts" / "enhance_ttx_scenario_with_openai.py"
    suggestions_out = case_dir / "30_outputs" / "scenario_enhancement_suggestions.md"

    if not enhancer.exists():
        print_error(f"ERROR: enhancement script not found: {enhancer}")
        return
    if not scenario_yaml.exists():
        print_error(f"ERROR: scenario.yaml not found: {scenario_yaml}")
        return

    print("\n============================================================")
    print("OPTIONAL AI SCENARIO ENHANCEMENT (SUGGESTIONS-ONLY)")
    print("This helper NEVER modifies 20_delivery/scenario.yaml.")
    print("Any output requires human review before manual application.")
    print("============================================================")

    cmd_dry_run = [
        sys.executable,
        str(enhancer),
        "--scenario-yaml",
        str(scenario_yaml),
        "--out-path",
        str(suggestions_out),
        "--confirm-send",
        "I_HAVE_CLIENT_PERMISSION",
        "--dry-run",
    ]
    p_dry = run_cmd(cmd_dry_run, cwd=repo_root)
    if p_dry.returncode != 0:
        print_error("ERROR: dry-run bundle generation FAILED.")
        print(p_dry.stderr or p_dry.stdout)
        return
    print_success(
        "SUCCESS: Dry-run prompt bundle generated: "
        f"{suggestions_out}.prompt.txt"
    )

    api_key_set = bool(os.environ.get("OPENAI_API_KEY", "").strip())
    if not api_key_set:
        print("\nOPENAI_API_KEY not set. Skipping optional network call.")
        return

    if not yes_no("\nOPENAI_API_KEY detected. Run optional network call now?", default_no=True):
        print("Skipped optional network call.")
        return

    confirm = input("Type exact confirmation string to continue: I_HAVE_CLIENT_PERMISSION\n> ").strip()
    if confirm != "I_HAVE_CLIENT_PERMISSION":
        print_error("ERROR: Confirmation string mismatch. Skipping network call.")
        return

    cmd_network = [
        sys.executable,
        str(enhancer),
        "--scenario-yaml",
        str(scenario_yaml),
        "--out-path",
        str(suggestions_out),
        "--confirm-send",
        confirm,
    ]
    p_net = run_cmd(cmd_network, cwd=repo_root)
    if p_net.returncode != 0:
        print_error("ERROR: Optional AI enhancement network call FAILED.")
        print(p_net.stderr or p_net.stdout)
        return

    print_success(f"SUCCESS: Suggestions written: {suggestions_out}")


def advanced_menu() -> str:
    print("\nAdvanced actions:")
    print("1) Inputs & Intake")
    print("2) Scenario")
    print("3) Delivery / Outputs")
    print("4) AI Helpers")
    print("5) Back")
    return input("Choose (1-5): ").strip()


def advanced_inputs_intake_menu() -> str:
    print("\nAdvanced actions > Inputs & Intake:")
    print("1) Review inputs tracker / locations")
    print("2) Run quick intake wizard (auto-fill required fields)")
    print("3) Back")
    return input("Choose (1-3): ").strip()


def advanced_scenario_menu() -> str:
    print("\nAdvanced actions > Scenario:")
    print("1) Set scenario category + title hint")
    print("2) Draft scenario.yaml (Option A, B, or C)")
    print("3) Validate scenario.yaml")
    print("4) Approve scenario")
    print("5) Validate library + compile scenario")
    print("6) Back")
    return input("Choose (1-6): ").strip()


def advanced_delivery_outputs_menu() -> str:
    print("\nAdvanced actions > Delivery / Outputs:")
    print("1) Build package")
    print("2) Export handouts")
    print("3) Launch facilitation UI")
    print("4) Generate AAR draft")
    print("5) Generate Executive Readout (draft + AI bundle + optional AI)")
    print("6) Close case")
    print("7) Back")
    return input("Choose (1-7): ").strip()


def advanced_ai_helpers_menu() -> str:
    print("\nAdvanced actions > AI Helpers:")
    print("1) Optional: AI scenario enhancement (suggestions-only)")
    print("2) Back")
    return input("Choose (1-2): ").strip()


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Run the TTX case workflow state machine (guided).")
    parser.add_argument("--case-dir", required=True, help="Case folder containing case_manifest.json")
    parser.add_argument("--allow-in-repo", action="store_true", help="Allow operating on a case folder inside the repo (synthetic only).")
    parser.add_argument("--overwrite", action="store_true", help="Enable overwrite behavior for workflow actions that support --force.")
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

    manifest_path = case_dir / "case_manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: case_manifest.json not found in case folder: {manifest_path}", file=sys.stderr)
        print("Initialize the case first with:")
        print("  python3 dfir_backend/ttx/scripts/init_ttx_case.py --case-dir <path> --bundle-type EXECUTIVE --duration-minutes 90 --timezone <tz> --audience-roles \"...\"")
        return 2

    while True:
        manifest = read_json(manifest_path)
        best_effort_autoadvance(case_dir, manifest)
        write_json(manifest_path, manifest)

        clear_screen()
        print_header(case_dir, manifest)

        print("1) Continue (recommended)")
        print("2) Advanced actions")
        print("3) Launch facilitation UI")
        print("4) Quit")
        print("------------------------------------------------------------")
        choice = input("Choose (1-4): ").strip()

        if choice == "1":
            step_key, _ = recommended_step(case_dir, manifest)

            if step_key == "REVIEW_INPUTS":
                action_review_inputs(case_dir, manifest)
            elif step_key == "SET_SCENARIO_META":
                action_set_scenario_meta(repo_root, case_dir, manifest)
            elif step_key == "DRAFT_SCENARIO":
                action_draft_scenario(repo_root, case_dir, manifest, args.overwrite)
            elif step_key == "VALIDATE_SCENARIO":
                action_validate(repo_root, case_dir, manifest)
            elif step_key == "APPROVE_SCENARIO":
                action_approve(case_dir, manifest)
            elif step_key == "BUILD_PACKAGE":
                action_build_package(repo_root, case_dir, manifest)
            elif step_key == "EXPORT_HANDOUTS_OR_FACILITATE":
                print("\nHandouts are optional.")
                print("1) Export handouts now")
                print("2) Launch facilitation UI now")
                print("3) Cancel")
                c2 = input("Choose (1-3): ").strip()
                if c2 == "1":
                    action_export_handouts(repo_root, case_dir, manifest)
                elif c2 == "2":
                    action_launch_ui(repo_root, case_dir, manifest)
                else:
                    print("Cancelled.")
            elif step_key == "FACILITATE":
                action_launch_ui(repo_root, case_dir, manifest)
            elif step_key == "GENERATE_AAR":
                action_generate_aar(repo_root, case_dir, manifest)
            elif step_key == "GENERATE_EXEC_READOUT":
                action_generate_exec_readout(repo_root, case_dir, manifest)
            elif step_key == "CLOSE_CASE":
                action_close_case(manifest)
            else:
                print("Nothing to do.")

            write_json(manifest_path, manifest)
            pause()

        elif choice == "2":
            while True:
                clear_screen()
                print_header(case_dir, manifest)
                sel = advanced_menu()
                if sel == "1":
                    while True:
                        sub_sel = advanced_inputs_intake_menu()
                        if sub_sel == "1":
                            action_review_inputs(case_dir, manifest)
                        elif sub_sel == "2":
                            wizard = repo_root / "dfir_backend" / "ttx" / "scripts" / "run_quick_intake_wizard.py"
                            if not wizard.exists():
                                print_error(f"ERROR: quick intake wizard script not found: {wizard}")
                            else:
                                proc = run_cmd_interactive([sys.executable, str(wizard), "--case-dir", str(case_dir)], cwd=repo_root)
                                if proc.returncode != 0:
                                    print_error("ERROR: quick intake wizard failed.")
                                else:
                                    print_success("SUCCESS: quick intake wizard completed.")
                        elif sub_sel == "3":
                            break
                        else:
                            print("Invalid selection.")
                        write_json(manifest_path, manifest)
                        pause()
                        manifest = read_json(manifest_path)
                        best_effort_autoadvance(case_dir, manifest)
                        write_json(manifest_path, manifest)
                elif sel == "2":
                    while True:
                        sub_sel = advanced_scenario_menu()
                        if sub_sel == "1":
                            action_set_scenario_meta(repo_root, case_dir, manifest)
                        elif sub_sel == "2":
                            action_draft_scenario(repo_root, case_dir, manifest, args.overwrite)
                        elif sub_sel == "3":
                            action_validate(repo_root, case_dir, manifest)
                        elif sub_sel == "4":
                            action_approve(case_dir, manifest)
                        elif sub_sel == "5":
                            action_validate_library_and_compile(repo_root, case_dir, manifest, args.overwrite)
                        elif sub_sel == "6":
                            break
                        else:
                            print("Invalid selection.")
                        write_json(manifest_path, manifest)
                        pause()
                        manifest = read_json(manifest_path)
                        best_effort_autoadvance(case_dir, manifest)
                        write_json(manifest_path, manifest)
                elif sel == "3":
                    while True:
                        sub_sel = advanced_delivery_outputs_menu()
                        if sub_sel == "1":
                            action_build_package(repo_root, case_dir, manifest)
                        elif sub_sel == "2":
                            action_export_handouts(repo_root, case_dir, manifest)
                        elif sub_sel == "3":
                            action_launch_ui(repo_root, case_dir, manifest)
                        elif sub_sel == "4":
                            action_generate_aar(repo_root, case_dir, manifest)
                        elif sub_sel == "5":
                            action_generate_exec_readout(repo_root, case_dir, manifest)
                        elif sub_sel == "6":
                            action_close_case(manifest)
                        elif sub_sel == "7":
                            break
                        else:
                            print("Invalid selection.")
                        write_json(manifest_path, manifest)
                        pause()
                        manifest = read_json(manifest_path)
                        best_effort_autoadvance(case_dir, manifest)
                        write_json(manifest_path, manifest)
                elif sel == "4":
                    while True:
                        sub_sel = advanced_ai_helpers_menu()
                        if sub_sel == "1":
                            action_optional_ai_scenario_enhancement(repo_root, case_dir, manifest)
                        elif sub_sel == "2":
                            break
                        else:
                            print("Invalid selection.")
                        write_json(manifest_path, manifest)
                        pause()
                        manifest = read_json(manifest_path)
                        best_effort_autoadvance(case_dir, manifest)
                        write_json(manifest_path, manifest)
                elif sel == "5":
                    break
                else:
                    print("Invalid selection.")

        elif choice == "3":
            action_launch_ui(repo_root, case_dir, manifest)
            write_json(manifest_path, manifest)
            pause()

        elif choice == "4":
            clear_screen()
            print("Bye.")
            return 0

        else:
            print("Invalid selection.")
            pause()


if __name__ == "__main__":
    raise SystemExit(main())
