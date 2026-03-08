#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import List


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[1]


def clear_screen() -> None:
    print("\033[2J\033[H", end="")


def pause() -> None:
    input("\nPress Enter to continue...")


def run(cmd: List[str], cwd: Path) -> int:
    print("\n>> Running:")
    print("   " + " ".join(cmd))
    print("")
    p = subprocess.run(cmd, cwd=str(cwd), text=True)
    return p.returncode


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


def main() -> int:
    repo_root = repo_root_from_here()

    init_case = repo_root / "dfir_backend" / "ttx" / "scripts" / "init_ttx_case.py"
    case_workflow = repo_root / "dfir_backend" / "ttx" / "scripts" / "ttx_case_workflow.py"
    validator_repo = repo_root / "dfir_backend" / "ttx" / "scripts" / "validate_ttx_scenarios.py"
    package_builder = repo_root / "dfir_backend" / "ttx" / "scripts" / "build_ttx_package_from_yaml.py"
    handouts = repo_root / "dfir_backend" / "ttx" / "scripts" / "export_ttx_handouts_html.py"
    aar_builder = repo_root / "dfir_backend" / "ttx" / "scripts" / "build_aar_draft_from_runtime.py"
    quick_intake_wizard = repo_root / "dfir_backend" / "ttx" / "scripts" / "run_quick_intake_wizard.py"
    library_validator = repo_root / "dfir_backend" / "ttx" / "scripts" / "validate_ttx_library.py"
    scenario_compiler = repo_root / "dfir_backend" / "ttx" / "scripts" / "compile_ttx_scenario_from_library.py"
    ui_app = repo_root / "dfir_backend" / "ttx" / "ui" / "ttx_studio.py"

    while True:
        clear_screen()
        print("============================================================")
        print("TTX Launcher")
        print("============================================================")
        print("1) Open existing case (recommended)")
        print("2) Create new case (guided)")
        print("3) Launch facilitation UI for a case (facilitator mode)")
        print("4) Power tools (advanced)")
        print("5) Quit")
        print("------------------------------------------------------------")
        choice = input("Choose (1-5): ").strip()

        if choice == "1":
            if not case_workflow.exists():
                print(f"ERROR: case workflow runner not found: {case_workflow}")
                pause()
                continue
            case_dir = prompt("Case folder path (must contain case_manifest.json)", "")
            if not case_dir.strip():
                print("ERROR: case folder path required.")
                pause()
                continue
            rc = run([sys.executable, str(case_workflow), "--case-dir", case_dir.strip()], cwd=repo_root)
            print(f"\nExit code: {rc}")
            pause()

        elif choice == "2":
            if not init_case.exists():
                print(f"ERROR: init case script not found: {init_case}")
                pause()
                continue
            if not case_workflow.exists():
                print(f"ERROR: case workflow runner not found: {case_workflow}")
                pause()
                continue

            case_dir = prompt("New case folder path (outside git)", str(Path.home() / "ttx_cases" / "TTX-CASE-ID-HERE"))
            case_id = prompt("Case ID", Path(case_dir).name)
            bundle_type = prompt("Bundle type (EXECUTIVE/HALF_DAY/FULL_DAY/CUSTOM)", "EXECUTIVE").strip().upper()
            duration = prompt("Duration minutes (e.g., 60/90/120/240/480)", "90").strip()
            timezone = prompt("Timezone (IANA, e.g., America/Los_Angeles)", "America/Los_Angeles").strip()
            handling = prompt("Handling label (PUBLIC/INTERNAL/CONFIDENTIAL/CLIENT_CONFIDENTIAL)", "CLIENT_CONFIDENTIAL").strip().upper()
            audience_roles = prompt("Audience roles (comma-separated)", "Executive, IT, Security, Legal/Privacy, PR/Comms")
            industry = prompt("Industry (optional)", "").strip()
            region = prompt("Region (optional)", "").strip()

            if not duration.isdigit():
                print("ERROR: duration-minutes must be an integer.")
                pause()
                continue

            cmd = [
                sys.executable,
                str(init_case),
                "--case-dir",
                case_dir,
                "--case-id",
                case_id,
                "--bundle-type",
                bundle_type,
                "--duration-minutes",
                str(int(duration)),
                "--timezone",
                timezone,
                "--handling-label",
                handling,
                "--audience-roles",
                audience_roles,
                "--industry",
                industry,
                "--region",
                region,
            ]

            rc = run(cmd, cwd=repo_root)
            print(f"\nExit code: {rc}")
            if rc == 0:
                print("\nOpening the new case in the workflow runner...")
                pause()
                run([sys.executable, str(case_workflow), "--case-dir", case_dir], cwd=repo_root)
            else:
                pause()

        elif choice == "3":
            if not ui_app.exists():
                print(f"ERROR: UI app not found: {ui_app}")
                pause()
                continue
            case_dir = prompt("Case folder path (must contain case_manifest.json)", "")
            if not case_dir.strip():
                print("ERROR: case folder path required.")
                pause()
                continue
            print("\nLaunching Streamlit (Facilitator Mode). Close the browser tab and press Ctrl+C to stop.\n")
            cmd = [sys.executable, "-m", "streamlit", "run", str(ui_app), "--", "--mode", "facilitate", "--case-dir", case_dir.strip()]
            run(cmd, cwd=repo_root)
            pause()

        elif choice == "4":
            # Power tools: keep what we already have, but out of the primary flow.
            while True:
                clear_screen()
                print("============================================================")
                print("TTX Power Tools (Advanced)")
                print("============================================================")
                print("1) Validate repo scenario YAML files (library hygiene)")
                print("2) Build a TTX package from a scenario YAML")
                print("3) Export participant handouts to offline HTML (+ optional ZIP)")
                print("4) Launch TTX Studio UI (FULL mode)")
                print("5) Generate AAR draft from a case")
                print("6) Review inputs tracker for a case")
                print("7) Run quick intake wizard for a case")
                print("8) Validate library and compile scenario for a case")
                print("9) Back")
                print("------------------------------------------------------------")
                c2 = input("Choose (1-9): ").strip()

                if c2 == "1":
                    if not validator_repo.exists():
                        print(f"ERROR: validator not found: {validator_repo}")
                    else:
                        run([sys.executable, str(validator_repo)], cwd=repo_root)
                    pause()

                elif c2 == "2":
                    if not package_builder.exists():
                        print(f"ERROR: package builder not found: {package_builder}")
                        pause()
                        continue
                    in_path = prompt("Scenario YAML path", "")
                    out_dir = prompt("Output directory", str(Path.home() / "ttx_outputs" / "ttx_package"))
                    force = yes_no("Overwrite output files if they exist? (--force)", default_no=False)
                    cmd = [sys.executable, str(package_builder), "--input", in_path, "--out-dir", out_dir]
                    if force:
                        cmd.append("--force")
                    run(cmd, cwd=repo_root)
                    pause()

                elif c2 == "3":
                    if not handouts.exists():
                        print(f"ERROR: handouts exporter not found: {handouts}")
                        pause()
                        continue
                    pkg_dir = prompt("Package directory (contains sitman.md + participant_guide.md)", "")
                    out_dir = prompt("HTML output directory", str(Path.home() / "ttx_outputs" / "handouts_html"))
                    make_zip = yes_no("Create a ZIP as well? (--zip)", default_no=False)
                    cmd = [sys.executable, str(handouts), "--package-dir", pkg_dir, "--out-dir", out_dir]
                    if make_zip:
                        cmd.append("--zip")
                    run(cmd, cwd=repo_root)
                    pause()

                elif c2 == "4":
                    if not ui_app.exists():
                        print(f"ERROR: UI app not found: {ui_app}")
                        pause()
                        continue
                    print("\nLaunching Streamlit (FULL mode). Close the browser tab and press Ctrl+C to stop.\n")
                    cmd = [sys.executable, "-m", "streamlit", "run", str(ui_app), "--", "--mode", "full"]
                    run(cmd, cwd=repo_root)
                    pause()

                elif c2 == "5":
                    if not aar_builder.exists():
                        print(f"ERROR: AAR builder not found: {aar_builder}")
                        pause()
                        continue
                    case_dir = prompt("Case folder path (must contain case_manifest.json)", "")
                    if not case_dir.strip():
                        print("ERROR: case folder path required.")
                        pause()
                        continue
                    run([sys.executable, str(aar_builder), "--case-dir", case_dir.strip()], cwd=repo_root)
                    pause()

                elif c2 == "6":
                    if not case_workflow.exists():
                        print(f"ERROR: case workflow runner not found: {case_workflow}")
                        pause()
                        continue
                    case_dir = prompt("Case folder path (must contain case_manifest.json)", "")
                    if not case_dir.strip():
                        print("ERROR: case folder path required.")
                        pause()
                        continue
                    run([sys.executable, str(case_workflow), "--case-dir", case_dir.strip()], cwd=repo_root)
                    pause()

                elif c2 == "7":
                    if not quick_intake_wizard.exists():
                        print(f"ERROR: quick intake wizard not found: {quick_intake_wizard}")
                        pause()
                        continue
                    case_dir = prompt("Case folder path (must contain case_manifest.json)", "")
                    if not case_dir.strip():
                        print("ERROR: case folder path required.")
                        pause()
                        continue
                    run([sys.executable, str(quick_intake_wizard), "--case-dir", case_dir.strip()], cwd=repo_root)
                    pause()

                elif c2 == "8":
                    if not library_validator.exists():
                        print(f"ERROR: library validator not found: {library_validator}")
                        pause()
                        continue
                    if not scenario_compiler.exists():
                        print(f"ERROR: scenario compiler not found: {scenario_compiler}")
                        pause()
                        continue
                    case_dir = prompt("Case folder path (must contain case_manifest.json)", "")
                    if not case_dir.strip():
                        print("ERROR: case folder path required.")
                        pause()
                        continue
                    force = yes_no("Overwrite scenario.yaml if it exists? (--force)", default_no=True)
                    rc_validate = run([sys.executable, str(library_validator)], cwd=repo_root)
                    if rc_validate != 0:
                        print(f"\nExit code: {rc_validate}")
                        pause()
                        continue
                    cmd = [sys.executable, str(scenario_compiler), "--case-dir", case_dir.strip()]
                    if force:
                        cmd.append("--force")
                    run(cmd, cwd=repo_root)
                    pause()

                elif c2 == "9":
                    break

                else:
                    print("Invalid selection.")
                    pause()

        elif choice == "5":
            clear_screen()
            print("Bye.")
            return 0

        else:
            print("Invalid selection.")
            pause()


if __name__ == "__main__":
    raise SystemExit(main())
