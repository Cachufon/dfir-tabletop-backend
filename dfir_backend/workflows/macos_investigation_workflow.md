# INTERNAL - macOS Investigation Workflow (Defensible Skeleton)

## Purpose
Apple-native forensic investigation support for insider risk, HR/legal, executive, and macOS incident scenarios. Content is placeholder for internal alignment with official battle cards and data sheets.

## macOS Investigation Types
- **Insider / Departed Employee Investigation**: Focused on potential misuse, data access, or pre-departure activity by current or recently exited personnel; often supports HR or legal review and relies on strict custodianship.
- **Executive / High-Risk User Investigation**: Prioritizes rapid, low-noise response for executives or monitored roles where confidentiality, minimal disruption, and privileged data handling are critical.
- **macOS Incident Response**: Reactive triage and scoping of suspected security events on macOS endpoints to confirm impact, identify entry vectors, and support containment.
- **macOS Digital Forensics (HR / Legal)**: Formal evidence collection and analysis to support HR investigations, litigation readiness, or regulatory inquiries with defensible chain-of-custody.
- **macOS Compromise Assessment (Add-On)**: Targeted sweep for signs of intrusion, persistence, or tooling on macOS endpoints to validate security posture or recent risk indicators.

## Phases
1. **Intake & Legal Alignment**: Capture request context, custodians, and objectives; confirm authorization, legal hold needs, HR involvement, and privacy constraints before any access.
2. **Evidence Acquisition**: Coordinate device access, ensure chain-of-custody logging, and collect approved macOS artifacts using sanctioned methods only (no tooling assumptions in this skeleton).
3. **Artifact Analysis**: Review system, user, and application artifacts for indicators aligned to the investigation type; maintain evidentiary integrity and annotate analysis steps.
4. **Timeline Reconstruction**: Correlate events into a defensible sequence with timestamps and sources noted; separate observed facts from hypotheses and maintain attribution to evidence.
5. **Findings & Conclusions**: Summarize supported observations, highlight gaps, and map to investigation objectives using neutral, fact-based language suitable for HR/Legal review.
6. **Reporting & Evidence Packaging**: Produce audience-appropriate reporting, attach evidence references with chain-of-custody details, and stage delivery packages in accordance with legal/HR guidance.

## Scope Clarifications
- This service is endpoint-centric and Apple-native.
- It does not replace enterprise-wide incident response.

## Notes
- Placeholder workflow only; add detailed procedures during full build-out.
- Avoid tooling or automation assumptions in this skeleton.
- Maintain documented chain-of-custody for all evidence handling decisions and transfers.
