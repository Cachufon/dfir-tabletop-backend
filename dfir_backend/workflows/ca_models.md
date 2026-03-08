# Compromise Assessment Models (Backend Workflows)

This document describes how each Compromise Assessment (CA) model behaves on top of the core CA workflow in ca_workflow.md. Models define the approach and depth, while scope areas (Identity, SaaS, Cloud, Endpoint, AI) define the surfaces included.

The five models are:
- Model 1 — Broad Sweep
- Model 2 — Post-Incident Sweep
- Model 3 — Targeted Threat Hunt
- Model 4 — Continuous Compromise Monitoring (subscription)
- Model 5 — AI Safety and Prompt Security Assessment

---

## Model 1 — Broad Sweep

### Purpose

A fast, low-friction assessment that uses baseline global detection content to look for obvious or likely signs of compromise across selected scope areas. Intended for recurring health checks or first-time customers with no specific incident.

### Characteristics

- Scope areas: Any combination of Identity, SaaS, Cloud, Endpoint, and (where telemetry exists) AI.
- Intel: No detailed incident intel required; environment context is optional.
- Rules:
  - Baseline global rules only (dfir_backend/rules/), minimal or no case-specific custom rules.
- Depth:
  - Light triage focused on high-confidence matches and clear patterns.
  - Emphasis on compromise indicators and hygiene issues rather than exhaustive investigation.

### Workflow Adjustments vs Core CA

- Phase 1:
  - Scope is often broad (full tenant or environment for chosen scope areas).
  - detection_plan.yaml is minimal, effectively indicating use of baseline rule packs per scope area.
- Phase 2:
  - Collect minimum required data sources for selected scope areas.
  - Optional data sources are collected only if easily available.
- Phase 3:
  - Execute Identity, SaaS, Cloud, Endpoint, and (if in scope) AI workflows using baseline rule packs.
  - Focus triage on clear, high-severity or high-confidence events.
- Phase 4:
  - Blast radius is characterized more as “risk posture and signal” than a detailed incident reconstruction.
  - Limited storyline building; prioritize identifying at-risk users, mailboxes, cloud accounts, and hosts.
- Phase 5:
  - Report focuses on:
    - Whether any strong evidence of compromise was found.
    - Top risky identities, SaaS accounts, cloud resources, and endpoints.
    - Structural risks and hygiene issues.
    - A concise set of prioritized recommendations.

---

## Model 2 — Post-Incident Sweep

### Purpose

A compromise assessment driven by a known incident. The primary questions are: “Did we fully contain this?” and “What did we miss?”

### Characteristics

- Inputs:
  - Incident report(s) from internal teams or external IR providers.
  - IOCs (hashes, domains, IPs, users, etc.).
  - Known impacted accounts, mailboxes, systems, cloud resources, or endpoints.
- Scope areas:
  - Identity, SaaS, Cloud, and/or Endpoint selected according to incident impact; AI included when relevant telemetry exists.
- Rules:
  - Baseline global rules.
  - Plus case-specific custom rules and IOC bundles under dfir_backend/custom/<case>/.

### Workflow Adjustments vs Core CA

- Phase 1:
  - intel/summary.md is populated from the IR report and incident artifacts.
  - detection_plan.yaml explicitly lists:
    - Incident-related TTPs.
    - IOC bundles to use.
    - Scope areas and expected detection outputs.
- Phase 2:
  - Data collection is prioritized around impacted services and time ranges.
  - Time window typically extends before first known indicator and after remediation.
- Phase 3:
  - Run baseline rules plus incident-specific Sigma/YARA/IOC searches.
  - Use custom rules to capture behaviors and indicators not covered by global content.
- Phase 4:
  - Heavy emphasis on blast radius:
    - Which users, mailboxes, cloud resources, or devices show related activity?
    - Any signs of lateral movement or persistence?
  - Validate containment:
    - Password resets, MFA changes, token revokes, app removal, endpoint remediation, cloud policy changes.
- Phase 5:
  - Report answers:
    - Whether there is evidence of residual or previously undetected activity.
    - Whether containment appears sufficient.
    - What cleanup or follow-up actions remain.
    - Where telemetry, controls, or processes were insufficient.

---

## Model 3 — Targeted Threat Hunt

### Purpose

A proactive, threat-led assessment that hunts for a specific threat actor, campaign, TTP cluster, or scenario. The main question is: “Are we seeing evidence of this particular threat in our environment, and how exposed are we to it?”

### Characteristics

- Inputs:
  - Threat intel (e.g., vendor reports, ISAC/CISA notices, sector-specific intelligence).
  - Customer hypotheses and scenarios (e.g., “We think ransomware group X is targeting us.”).
- Scope areas:
  - Any combination of Identity, SaaS, Cloud, Endpoint, and AI (if relevant to the threat’s TTPs).
- Rules:
  - Baseline global rules.
  - Scenario-specific IOC bundles.
  - Scenario-specific Sigma/YARA/NOVA rules, often generated or refined with AI assist.

### Workflow Adjustments vs Core CA

- Phase 1:
  - intel/summary.md captures the threat actor or scenario, associated TTPs, and targeted surfaces.
  - detection_plan.yaml drives scope area selection and defines detection goals and required outputs per scope area.
- Phase 2:
  - Data collection is tailored:
    - Some hunts may require longer time ranges.
    - Scope area selection is aligned with the actor’s known TTPs (e.g., identity-centric APT vs. endpoint-centric ransomware).
- Phase 3:
  - Use ai_assist prompts (sigma_from_report_identity, sigma_from_report_saas, sigma_from_report_endpoint, yara_from_malware_notes) to generate or refine scenario-specific detection artifacts.
  - Run both baseline and scenario-specific rules across the selected scope areas.
- Phase 4:
  - Focus investigation on:
    - Clear matches to the threat actor’s behavior or tooling.
    - Weak signals and near-misses (e.g., anomalies that resemble but don’t fully match the actor’s profile).
    - Environmental gaps that would enable the actor to succeed.
- Phase 5:
  - Report answers:
    - Whether there is evidence of the specific actor/campaign or similar behavior.
    - How prepared the environment is against that threat.
    - What changes would most effectively reduce exposure to that threat’s TTPs.

---

## Model 4 — Continuous Compromise Monitoring (subscription)

### Purpose

An ongoing compromise monitoring subscription that re-runs the CA workflow on a scheduled cadence with light intake and rapid reporting.

### Characteristics

- Cadence-driven with agreed-upon scope areas (Identity, SaaS, Cloud, Endpoint, and AI where available).
- Uses standardized detection plans and baseline rule packs with incremental tuning informed by prior cycles.
- Lightweight intake for each cycle focusing on changes in architecture, threat landscape, or telemetry availability.

### Workflow Adjustments vs Core CA

- Phase 1:
  - Reuse prior detection_plan.yaml, updating only where architecture, threat intel, or scope areas change.
- Phase 2:
  - Data pulls aligned to the monitoring cadence; prioritize automation for recurring exports.
- Phase 3:
  - Run standardized rule packs per scope area with targeted triage on deltas from prior cycles.
- Phase 4:
  - Track trends, recurring signals, and emerging gaps across cycles.
- Phase 5:
  - Provide concise reports with trendlines, repeated offenders, and prioritized remediation themes.

---

## Model 5 — AI Safety and Prompt Security Assessment

### Purpose

A dedicated assessment model to evaluate system prompts, developer prompts, transcripts, and agent manifests for misuse patterns, unsafe capability exposure, guardrail weaknesses, and prompt injection risk.

### Characteristics

- Scope areas: AI as the primary focus; Identity, SaaS, Cloud, and Endpoint referenced only when AI telemetry intersects with those surfaces.
- Inputs:
  - System and developer prompts, transcripts, and agent manifests/tool schemas.
  - Model gateway or policy logs, allow/deny logs, and evaluation or red-team artifacts when available.
- Method:
  - Gruve MAPS–assisted analysis with analyst validation and dedicated AI safety reporting.

### Workflow Adjustments vs Core CA

- Phase 1:
  - Define AI systems, agents, and policies in scope and confirm artifact availability.
- Phase 2:
  - Collect AI artifacts and telemetry with emphasis on prompt provenance and agent capability mapping.
- Phase 3:
  - Execute the AI safety and prompt security workflow (ai_safety_prompt_assessment_workflow.md) leveraging MAPS.
- Phase 4:
  - Validate AI-focused findings, score capability and governance risk, and map to misuse categories.
- Phase 5:
  - Deliver dedicated AI safety reporting and prompt hardening guidance.

---

These model overlays should be used in conjunction with the general CA workflow defined in ca_workflow.md and the scope area workflows under dfir_backend/scope_areas/.
