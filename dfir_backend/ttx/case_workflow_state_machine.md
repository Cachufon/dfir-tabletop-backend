# INTERNAL - TTX Case Workflow State Machine

This document defines the **single, seamless engagement workflow** for Tabletop Exercises (TTX) as a **state machine**.

## Core principles

### Single source of truth
For each engagement, the canonical scenario definition is:

- `20_delivery/scenario.yaml`

Everything else is generated from it (package, handouts), or recorded during execution (runtime logs), then used for after-action deliverables.

### Determinism and scalability
Bespoke scenario drafting may be manual or AI-assisted, but **scenario acceptance is deterministic**:
- Scenario YAML must pass schema + taxonomy + policy validation.
- A facilitator must explicitly approve the scenario before packaging/delivery.

### Handling label (non-government)
We do NOT use government classifications in commercial client work.

Instead, we optionally track a simple handling label in the case manifest (default: `CLIENT_CONFIDENTIAL`), purely for internal hygiene. This label is not required and should not appear in participant-facing materials unless requested.

---

## Case folder layout (outside git)

Each client engagement lives in secure project storage outside the repo:

- `<case_dir>/`
  - `00_admin/`
  - `10_inputs/`
    - `intake_notes.md`
    - `ir_plan.txt` (optional but recommended)
    - `threat_brief.md` (optional; high-level)
    - `ttx_scenario_generation/` (optional; AI bundle outputs)
  - `20_delivery/`
    - `scenario.yaml` (canonical)
    - `ttx_package/` (generated)
    - `handouts_html/` (generated; participant-facing)
  - `30_outputs/`
    - `ttx_logs/` (exports from facilitation)
    - `after_action_report_draft.md` (optional; future)
    - `aar_ai_bundle.txt` (optional; future)
  - `90_internal/`

The **workflow memory** is stored in:
- `<case_dir>/case_manifest.json`

---

## State machine

### States (canonical)
- `S1_CASE_INITIALIZED`
- `S2_INPUTS_COLLECTED`
- `S3_SCENARIO_DRAFTED`
- `S4_SCENARIO_VALIDATED`
- `S4_SCENARIO_APPROVED`
- `S5_PACKAGE_BUILT`
- `S6_HANDOUTS_EXPORTED`
- `S7_FACILITATION_IN_PROGRESS`
- `S8_LOGS_EXPORTED`
- `S9_AAR_DRAFTED` (optional; future)
- `S10_CLOSED`

### Transitions (high-level)
1. Initialize case → `S1_CASE_INITIALIZED`
2. Collect intake inputs → `S2_INPUTS_COLLECTED`
3. Draft scenario YAML (two paths) → `S3_SCENARIO_DRAFTED`
   - Path A (base scenario): copy from repo scenario library and tailor
   - Path B (bespoke): AI-assisted draft via bundle; paste YAML into `scenario.yaml`
4. Validate scenario YAML → `S4_SCENARIO_VALIDATED`
5. Facilitator approval → `S4_SCENARIO_APPROVED`
6. Build package from YAML → `S5_PACKAGE_BUILT`
7. Export participant handouts to HTML/ZIP → `S6_HANDOUTS_EXPORTED` (optional)
8. Facilitation (Streamlit UI) → `S7_FACILITATION_IN_PROGRESS`
9. Export logs (scribe_runtime.json + MD/CSV) → `S8_LOGS_EXPORTED`
10. Generate AAR draft and/or AI bundle → `S9_AAR_DRAFTED` (optional; future)
11. Close case → `S10_CLOSED`

---

## Where Option A vs Option B fits (no separate workflows)
Both options live within **one state** (`S3_SCENARIO_DRAFTED`), and both converge to the same deterministic gate (`S4_SCENARIO_VALIDATED`).

- **Option A** (prebuilt generalized scenario):
  - copy a repo scenario to `<case_dir>/20_delivery/scenario.yaml`
  - tailor manually
  - validate
- **Option B** (bespoke / AI-assisted):
  - generate an AI bundle from case inputs (NO AI called by repo)
  - paste YAML output into `<case_dir>/20_delivery/scenario.yaml`
  - validate

---

## Tools
This repo provides scripts to implement the workflow:
- `init_ttx_case.py` (create case folder + manifest)
- `ttx_case_workflow.py` (run the state machine, update manifest)
- `validate_ttx_scenario_file.py` (deterministic scenario validation)
- `build_ttx_scenario_ai_bundle_from_case.py` (AI bundle creation without calling AI)

The CLI launcher is updated to be a guided wizard:
- open existing case
- create new case
- launch facilitation UI
- power tools

End of document.
