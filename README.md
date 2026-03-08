# DFIR_Team

Gruve’s internal source-of-truth for DFIR service delivery scaffolding—workflows, templates, stubs, and playbooks—designed to be repeatable and automation-ready. Everything here is structured for internal consumption and operational reuse.

## Services
- **Compromise Assessment** — Repeatable assessments across defined scope areas.
- **macOS Investigations** — Mac-focused triage and response workflows.
- **Tabletop Exercises** — Structured, repeatable incident response simulations.

## Compromise Assessment Models
- **Model 1: Broad Sweep**
- **Model 2: Post-Incident Sweep**
- **Model 3: Targeted Threat Hunt**
- **Model 4: Continuous Compromise Monitoring**
- **Model 5: AI Safety and Prompt Security Assessment (MAPS used here)**

## macOS Investigations Offerings
- macOS Insider and Departed Employee Investigation
- macOS Executive and High-Risk User Investigation
- macOS Incident Response (Reactive)
- macOS Digital Forensics (HR / Legal)
- Premium Add-On: macOS Compromise Assessment

## Tabletop Exercise Offerings
- Core Tabletop Exercise
- Advanced Tabletop Exercise
- Executive Tabletop Exercise
- TTX-as-a-Service (Quarterly Readiness Program)

## Where to Find Backend Delivery Materials
- Compromise Assessment:
  - dfir_backend/ca/ (blueprint: templates, scripts, validation)
  - dfir_backend/workflows/ca_workflow.md
  - dfir_backend/workflows/ca_models.md
  - dfir_backend/scope_areas/
  - dfir_backend/collectors/ , normalization/ , detections/ , triage/ , runbooks/

- AI Safety and Prompt Security Assessment (Model 5):
  - dfir_backend/workflows/ai_safety_prompt_assessment_workflow.md
  - dfir_backend/reporting/ai_safety_report_template.md

- macOS Investigations:
  - dfir_backend/workflows/macos_investigation_workflow.md
  - dfir_backend/reporting/macos_investigation_report_template.md
  - dfir_backend/reporting/macos_finding_categories.md

- Tabletop Exercises:
  - dfir_backend/workflows/ttx_workflow.md
  - dfir_backend/ttx/ (templates, scoring model, scenario taxonomy)

## Scope Areas
Compromise Assessment is executed across selectable scope areas:
- Identity
- SaaS
- Cloud
- Endpoint
- AI

## Where things live
- `/services` — Internal marketing and sales enablement material.
- `/operations` — Internal strategy/ops documentation (if present).
- `/dfir_backend` — Internal execution backbone. Key directories:
  - `workflows/`
  - `reporting/`
  - `scope_areas/` (replaces "modules")
  - `rules/`
  - `collectors/`
  - `normalization/`
  - `detections/`
  - `triage/`
  - `runbooks/`
  - `ttx/`
  - `custom/example_case` (synthetic training/testing data)

## Status / Maturity
- This repo currently contains scaffolding and stubs (Phase 1).
- Tooling implementations will be added iteratively.
- Example cases are synthetic and safe for training/testing.

## Contribution Guidelines
- Prefer small, atomic commits.
- Keep docs marked INTERNAL when not customer-facing.
- Avoid changing service definitions without updating battle card/data sheet alignment.
- Run periodic validation.
