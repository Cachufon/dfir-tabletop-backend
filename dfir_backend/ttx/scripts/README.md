# INTERNAL - TTX Scripts

These scripts support **repeatable Tabletop Exercise (TTX) delivery** and are designed to be safe-by-default.

## Critical data handling rule
- Do NOT write client-tailored outputs inside the git repo directory.
- Store client-tailored scenarios and generated packages in approved secure project storage outside git.
- Do NOT commit client-tailored outputs (scenario YAML, SitMan, facilitator packet, scribe logs, AARs).

## Dependencies
Install required Python dependencies:

- pip install -r dfir_backend/ttx/scripts/requirements.txt

## Intake questionnaire and Inputs Tracker
- The intake questionnaire is `10_inputs/intake_notes.md` in each case folder. It captures baseline details used to tailor scenario generation, facilitation, and reporting outputs.
- `10_inputs/intake_structured.json` is a primary deterministic metadata source used by Option C compile-from-library flow.
- `10_inputs/intake_notes.md` checkbox selections further tailor environment assumptions (Identity/SSO, Email/collaboration, Endpoint/EDR, Cloud) and redlines/constraints.
- Option C (Compile from Library) writes `20_delivery/scenario_inputs_snapshot.json` as a traceability snapshot of deterministic tailoring inputs when available.
- `run_quick_intake_wizard.py` is deterministic/offline and auto-fills only minimum required foundational fields.
- The quick intake wizard does **not** replace the full `intake_notes.md`; it only inserts/updates the top `## Minimum required (auto-filled)` section.
- Use the workflow runner's **Review inputs tracker / locations** action to review deterministic input status and file locations before continuing.
- Inputs must be reviewed and marked complete before drafting scenarios, because intake/IR context drives downstream tailoring quality and consistency.

Quick-start example:
- python3 dfir_backend/ttx/scripts/run_quick_intake_wizard.py --case-dir /secure_storage/ttx/<case_id>

## 1) Validate scenario YAML files (repo scenarios)
Validates all YAML files under:
- dfir_backend/ttx/scenarios/

Checks include:
- JSON schema validation (dfir_backend/ttx/schemas/ttx_scenario.schema.json)
- scenario.category matches canonical categories in dfir_backend/ttx/scenario_taxonomy.md
- basic inject conventions (i01/i02..., ordering, t_plus_min within duration)

Run from repo root:
- python3 dfir_backend/ttx/scripts/validate_ttx_scenarios.py

Optional args:
- --schema dfir_backend/ttx/schemas/ttx_scenario.schema.json
- --scenarios-dir dfir_backend/ttx/scenarios
- --taxonomy dfir_backend/ttx/scenario_taxonomy.md

## 2) Build a delivery package from a scenario YAML
Generates a human-usable package from a scenario YAML:
- scenario.yaml (copy)
- sitman.md (participant-facing)
- facilitator_packet.md
- participant_guide.md
- scribe_logs.md
- package_manifest.md

IMPORTANT:
- By default, this script **refuses** to write outputs inside the git repo directory.

Example (recommended; secure storage outside git):
- python3 dfir_backend/ttx/scripts/build_ttx_package_from_yaml.py --input /secure_storage/ttx/<case_id>/20_delivery/scenario.yaml --out-dir /secure_storage/ttx/<case_id>/20_delivery/ttx_package

Synthetic example only (allowed in repo):
- python3 dfir_backend/ttx/scripts/build_ttx_package_from_yaml.py --input dfir_backend/ttx/scenarios/example_ttx_saas_identity_compromise.yaml --out-dir dfir_backend/ttx/scenarios/_build_example --allow-in-repo --force

## 3) Build deterministic AAR draft (offline)
Generates a deterministic markdown draft from scenario YAML + scribe runtime export (no AI calls).

Preferred mode (case manifest resolution):
- python3 dfir_backend/ttx/scripts/build_aar_draft_from_runtime.py --case-dir /secure_storage/ttx/<case_id>

Explicit paths mode:
- python3 dfir_backend/ttx/scripts/build_aar_draft_from_runtime.py --scenario-yaml /secure_storage/ttx/<case_id>/20_delivery/scenario.yaml --runtime-json /secure_storage/ttx/<case_id>/30_outputs/ttx_logs/scribe_runtime.json --out-dir /secure_storage/ttx/<case_id>/30_outputs

## 4) Build AAR AI paste bundle (offline)
Builds a single paste-ready text bundle that includes the AAR prompt template, scenario YAML, runtime JSON, and optional intake/IR inputs (no AI calls):

- python3 dfir_backend/ttx/scripts/build_aar_ai_bundle.py --scenario-yaml /secure_storage/ttx/<case_id>/20_delivery/scenario.yaml --runtime-json /secure_storage/ttx/<case_id>/30_outputs/ttx_logs/scribe_runtime.json --intake-notes /secure_storage/ttx/<case_id>/10_inputs/intake_notes.md --ir-plan /secure_storage/ttx/<case_id>/10_inputs/ir_plan.txt --out-dir /secure_storage/ttx/<case_id>/30_outputs

## 5) Build deterministic executive readout draft (offline)
Generates a deterministic executive readout markdown draft from scenario YAML + scribe runtime export (no AI calls):

- python3 dfir_backend/ttx/scripts/build_executive_readout_draft_from_runtime.py --scenario-yaml /secure_storage/ttx/<case_id>/20_delivery/scenario.yaml --runtime-json /secure_storage/ttx/<case_id>/30_outputs/ttx_logs/scribe_runtime.json --out-path /secure_storage/ttx/<case_id>/30_outputs/executive_readout.md

## 6) Build executive readout AI paste bundle (offline)
Builds a single paste-ready text bundle that includes the executive readout prompt template, scenario YAML, runtime JSON, and optional intake/IR inputs (no AI calls):

- python3 dfir_backend/ttx/scripts/build_executive_readout_ai_bundle.py --scenario-yaml /secure_storage/ttx/<case_id>/20_delivery/scenario.yaml --runtime-json /secure_storage/ttx/<case_id>/30_outputs/ttx_logs/scribe_runtime.json --intake-notes /secure_storage/ttx/<case_id>/10_inputs/intake_notes.md --ir-plan /secure_storage/ttx/<case_id>/10_inputs/ir_plan.txt --out-dir /secure_storage/ttx/<case_id>/30_outputs


## Scenario Library (module maps + inject banks)
- Web Application / API Breach uses OWASP Top 10 + OWASP API Top 10 references and KEV/SSDF links in the reference catalog.

Validate scenario library references, inject banks, and module maps:
- python3 dfir_backend/ttx/scripts/validate_ttx_library.py

Compile deterministic scenario.yaml from the scenario library for a case (canonical path):
- python3 dfir_backend/ttx/scripts/compile_ttx_scenario_from_library.py --case-dir /secure_storage/ttx/<case_id>

Recommended advanced gate before compile:
- python3 dfir_backend/ttx/scripts/validate_ttx_library.py
- python3 dfir_backend/ttx/scripts/compile_ttx_scenario_from_library.py --case-dir /secure_storage/ttx/<case_id>

Optional args:
- --profile EXEC_90|HALF_DAY|FULL_DAY
- --force
- --allow-in-repo

## 7) Optional direct OpenAI markdown generation (network call)
Optionally generates markdown output directly using OpenAI Responses API.

WARNING:
- Requires explicit client permission before sending any client data.
- Uses OPENAI_API_KEY from environment (or --api-key).
- Network call is blocked unless --confirm-send I_HAVE_CLIENT_PERMISSION is provided exactly.
- Request body sets store: false.

Security controls:
- API keys should be loaded from environment variable `OPENAI_API_KEY` (do not hardcode keys).
- AI call is disabled unless `--confirm-send I_HAVE_CLIENT_PERMISSION` is provided exactly.

Example:
- OPENAI_API_KEY="<set-in-environment>" python3 dfir_backend/ttx/scripts/generate_markdown_with_openai.py --prompt-template dfir_backend/ai_assist/prompts/ttx_aar_from_scribe_notes.md --scenario-yaml /secure_storage/ttx/<case_id>/20_delivery/scenario.yaml --runtime-json /secure_storage/ttx/<case_id>/30_outputs/ttx_logs/scribe_runtime.json --intake-notes /secure_storage/ttx/<case_id>/10_inputs/intake_notes.md --ir-plan /secure_storage/ttx/<case_id>/10_inputs/ir_plan.txt --out-path /secure_storage/ttx/<case_id>/30_outputs/after_action_report_ai.md --confirm-send I_HAVE_CLIENT_PERMISSION

Do NOT commit any generated outputs if they contain client information.


## 8) Optional AI scenario enhancement suggestions (network call)
Generates markdown suggestions to improve inject wording clarity and add optional inject ideas.

Safety/usage rules:
- Optional only; deterministic compile remains canonical for scenario.yaml generation.
- Requires explicit client permission before sending data.
- Requires OPENAI_API_KEY (or --api-key) and exact confirmation string.
- Suggestions output is advisory and does not auto-deliver or overwrite scenario.yaml.

Example:
- OPENAI_API_KEY="<set-in-environment>" python3 dfir_backend/ttx/scripts/enhance_ttx_scenario_with_openai.py --scenario-yaml /secure_storage/ttx/<case_id>/20_delivery/scenario.yaml --out-path /secure_storage/ttx/<case_id>/20_delivery/scenario_enhancement_suggestions.md --confirm-send I_HAVE_CLIENT_PERMISSION

Dry-run example (no network call):
- python3 dfir_backend/ttx/scripts/enhance_ttx_scenario_with_openai.py --scenario-yaml /secure_storage/ttx/<case_id>/20_delivery/scenario.yaml --out-path /secure_storage/ttx/<case_id>/20_delivery/scenario_enhancement_suggestions.md --confirm-send I_HAVE_CLIENT_PERMISSION --dry-run
