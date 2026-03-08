# Custom Cases (Local Case Workspaces)

This directory describes the *structure* of case-specific custom content used during Post-Incident Compromise Assessments and Targeted Threat Hunts.

## Critical rule: do not commit client data
**Client-specific case folders MUST NOT be committed to git.**
This repo is for reusable content (templates, workflows, generalized rules) and **synthetic** examples only.

Casework belongs in approved secured evidence storage (encrypted NAS / encrypted evidence media) and should be referenced by case ID.

The repo includes `.gitignore` rules to ignore case folders under `dfir_backend/custom/` except:
- `dfir_backend/custom/README.md`
- `dfir_backend/custom/example_case/` (synthetic, safe)

## Typical local case folder structure (NOT committed)
A typical local case folder contains:

- `intel/` — Analyst-written summaries and notes (store client source material only in evidence storage, not git)
- `detection_plan.yaml` — Machine-readable detection plan driving scope areas and rule execution
- `iocs/` — Case-specific IOC bundles
- `sigma/` — Case-specific Sigma rules
- `yara/` — Case-specific YARA rules
- `ai_prompts/` — Case-specific prompt/NOVA-style rules
- `notes.md` — Analyst notes and follow-ups

## Promoting reusable content
Only generalized, reusable rules (after internal review) should be promoted into `dfir_backend/rules/`.
