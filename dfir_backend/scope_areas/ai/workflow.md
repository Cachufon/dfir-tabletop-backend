# AI Scope Area Workflow (Stub)

This document outlines the high-level workflow for running the AI scope area within a Compromise Assessment. It can be used:

- As the dedicated Model 5 AI Safety / Prompt Security Assessment workflow, or
- Referenced in Models 1–4 when AI telemetry is available and relevant to compromise or misuse evaluation.

## High-Level Steps (v1 Stub)

1. Confirm AI systems, agents, and datasets in scope alongside the assessment model.
2. Collect AI-related artifacts and telemetry:
   - Minimum: prompt logs/transcripts, system and developer prompts, and agent manifests/tool schemas when applicable.
   - Optional: model gateway logs, policy/allow/deny logs, red-team or evaluation artifacts, and access control mappings.
3. Normalize and prepare AI artifacts for analysis, preserving prompt structure and context.
4. Apply AI-focused detection and MAPS-aligned review for misuse patterns, prompt injection indicators, and unsafe capability exposure.
5. Triage notable AI interactions or configuration issues and validate findings with analysts.
6. Summarize AI-related findings, highlight risky behaviors or design gaps, and provide prompt hardening guidance.
7. When combined with other scope areas, correlate AI findings with identity, SaaS, cloud, or endpoint observations.

This file will be expanded with more detailed steps, queries, and mappings to specific detection rules.
