# AI Safety and Prompt Security Assessment Workflow (Internal)

This workflow is internal-only for Model 5. It outlines how Gruve conducts AI Safety and Prompt Security Assessments using Gruve MAPS and analyst validation.

## Phases

1. **Scoping**
   - Identify AI systems, agents, and policies in scope.
   - Confirm intended capabilities, guardrails, and business context.
   - Determine available artifacts and telemetry.

2. **Artifact Intake**
   - Collect system and developer prompts, transcripts, and agent manifests/tool schemas.
   - Ingest supporting telemetry such as model gateway logs, allow/deny decisions, and policy enforcement logs when available.
   - Preserve prompt provenance and context for downstream analysis.

3. **MAPS Execution**
   - Run Gruve MAPS against collected prompts, transcripts, and agent schemas.
   - Screen for misuse patterns, prompt injection vectors, unsafe capability exposure, and guardrail gaps.
   - Generate preliminary findings and capability risk observations.

4. **Analyst Validation**
   - Review MAPS outputs for accuracy and relevance.
   - Reproduce or simulate risky interactions where safe to do so.
   - Align findings to AI risk categories and customer governance requirements.

5. **Reporting**
   - Produce AI safety posture reporting tailored to the in-scope systems.
   - Summarize capability risk scoring, prompt hardening guidance, and transcript-based findings.
   - Highlight governance-aligned recommendations with near-term prioritization.

6. **Recommendations**
   - Deliver detailed prompt and policy hardening actions.
   - Provide remediation guidance for risky agent/tool configurations and access controls.
   - Outline operational follow-ups for monitoring and governance.

## Inputs

- System prompts and developer prompts
- Interaction transcripts
- Agent manifests and tool schemas
- Model gateway, policy, or allow/deny logs (when available)
- Evaluation or red-team artifacts (if provided)

## Outputs

- AI safety posture report
- Prompt hardening guidance
- Transcript findings highlighting misuse or leakage
- Capability risk scoring summary
- Governance-aligned recommendations with 0–7 / 30 / 90 day actions

## Limitations

AI artifact availability varies by customer. Assessment depth, coverage, and confidence depend on the completeness of prompts, transcripts, and policy or gateway logs provided.
