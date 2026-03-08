EXAMPLE REPORT — FOR TRAINING AND TESTING PURPOSES ONLY

# Technical Report (EXAMPLE)

## Title Page
- Engagement title and client: "Example Compromise Assessment" for synthetic org
- Date range: 2024-05-01 to 2024-05-03
- Authors and reviewers: Example DFIR Team
- Version history: v0.1 (example)

## Executive Summary
- Unauthorized access likely achieved via MFA fatigue against `alice@example.com`.
- Session from `198.51.100.42` led to mailbox forwarding to `exfil@example.net`.
- No real data impacted; scenario built for training and tooling validation.

## Scope
- Systems: Identity provider and Microsoft 365 mailbox for `alice@example.com`.
- Timeframe: MFA activity and mailbox changes on 2024-05-01.
- Out-of-scope: Real customer data; this is purely example telemetry.

## Methodology
- Reviewed identity MFA and session logs for frequency anomalies.
- Correlated SaaS audit logs for configuration changes post-login.
- Used scripted IOC sweeps for documentation-range IPs and forwarding domains.

## Data Sources
- Identity authentication and MFA audit logs (example Okta events).
- Microsoft 365 audit logs for mailbox settings and rule creation.
- Normalized parquet placeholders aligned to `normalized_data_contract.md`.

## Detailed Findings
- ID-001: MFA fatigue approval enabled foreign session from `198.51.100.42`.
- ID-002: Mailbox forwarding and inbox rule created to `exfil@example.net`.
- Both findings are synthetic and provided for demonstration purposes.

## Blast Radius
- Assets: Single test identity `alice@example.com`.
- No lateral movement observed; scenario constrained to mailbox and identity platform.
- Business impact hypothetical: potential mail exposure if this were real.

## Remediation Recommendations
- Enforce phishing-resistant MFA and suppress repeated prompts.
- Alert on foreign logins and mailbox forwarding to external domains.
- Review session management policies for rapid revocation.

## Limitations
- Dataset intentionally minimal and synthetic.
- No endpoint or network telemetry included beyond identity/SaaS artifacts.
- Confidence derived from curated example rather than live investigation.

## Appendices
- Timeline of MFA prompts and mailbox changes (example only).
- Sample queries for identifying forwarding rules to external domains.
- Glossary of documentation-range IPs used in the scenario.
