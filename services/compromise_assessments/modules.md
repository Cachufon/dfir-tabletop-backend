# Compromise Assessment Modules

Modules describe WHERE Gruve Compromise Assessments look for evidence of compromise. Each module can run independently, but modules can also enrich each other when combined (for example, Identity can provide a list of suspect users to focus SaaS or Endpoint analysis).

The three primary modules are Identity, SaaS, and Endpoint.

## Identity Module

The Identity module focuses on identity providers and authentication flows. It answers: “Were accounts abused? Who did what, from where, and with which access?”

Examples of in-scope sources:
- Okta, Entra / Azure AD, Google Workspace as identity providers
- Sign-in and authentication logs
- MFA events
- Admin and directory changes
- OAuth and SAML-based access

This module can be run by itself (Identity-only compromise assessment) or combined with SaaS and/or Endpoint modules.

## SaaS Module

The SaaS module focuses on business applications such as email, collaboration, storage, and developer platforms. It answers: “What data and messaging systems were touched or exfiltrated?”

Examples of in-scope sources:
- O365 and Google Workspace audit logs
- Exchange / Gmail mailbox activity
- SharePoint / OneDrive / Google Drive file access and sharing
- Slack workspace and file activity
- GitHub audit logs

This module can be run alone (SaaS-only assessment) or combined with Identity and/or Endpoint modules.

## Endpoint Module

The Endpoint module focuses on endpoint telemetry (EDR and host-level artifacts). It answers: “What happened on the devices? Did attackers establish persistence, move laterally, or attempt to evade controls?”

Examples of in-scope sources:
- EDR alert and detection feeds
- EDR timelines and behavior telemetry
- Host triage bundles from selected endpoints
- OS-level artifacts such as persistence entries and process/network data

This module can be run independently (Endpoint-only assessment) or alongside Identity and SaaS.

## Cross-Module Enrichment

When multiple modules are selected, they can provide enrichment to each other without being strictly dependent:

- Identity → SaaS: suspect users and sessions can focus mailbox and file reviews.
- Identity → Endpoint: suspicious accounts and devices can guide which endpoints to triage.
- SaaS → Identity: suspicious mailboxes or collaboration behavior can drive deeper identity investigation.

Each module remains standalone, but combined modules produce higher-quality and more targeted results.

---
