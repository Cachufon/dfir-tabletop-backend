# SaaS Scope Area Workflow (Stub)

This document outlines the high-level workflow for running the SaaS scope area within a Compromise Assessment. It can be used:

- As a SaaS-only compromise assessment, or
- Combined with Identity and/or Endpoint scope areas.

## High-Level Steps (v1 Stub)

1. Confirm in-scope SaaS platforms (e.g., O365, Google Workspace, Slack, GitHub) and time window.
2. Collect SaaS activity logs:
   - O365 Unified Audit Log or Google Workspace audit logs (minimum).
   - Optional logs for mail, files, Slack, GitHub, and OAuth apps as available.
3. Normalize and prepare SaaS events for analysis.
4. Apply SaaS-focused detection logic (e.g., suspicious inbox rules, mass downloads, abnormal external sharing, risky app usage).
5. Triage and investigate notable SaaS events and user actions.
6. Summarize SaaS-related findings, focusing on data access and potential exfiltration.
7. When combined with other scope areas, correlate SaaS findings with suspect identities and/or endpoints.

This file will be expanded with more detailed steps, queries, and mappings to specific detection rules.

## SaaS Scope Area Detection Categories (v1)

The SaaS scope area focuses on detecting misuse, abuse, or suspicious activity across business applications such as O365, Google Workspace, Slack, and GitHub. These behaviors often correlate with account takeover, data exfiltration, persistence mechanisms, or configuration abuse within SaaS environments.

### 1. Mailbox Manipulation & Forwarding Abuses

Goal: Determine whether email inboxes were misused for persistence, silent monitoring, or exfiltration.

Example patterns:
- Creation of forwarding rules to external domains.
- Modification of existing rules or filters that hide or redirect messages.
- Delegation added to unexpected or unauthorized users.
- Hidden inbox rules (e.g., delete or move specific messages).
- Unusual Send-As or Send-On-Behalf activity.

### 2. File Access, Download & Sync Anomalies

Goal: Detect unusual or high-risk access to documents and files stored in collaboration platforms.

Example patterns:
- Mass downloads within short time windows.
- Unusual file access by low-risk or atypical users.
- Access to VIP or sensitive folders outside normal patterns.
- Excessive Drive/SharePoint sync operations not normally seen for a user.

### 3. External Sharing & Data Exposure

Goal: Identify behavior that exposes internal data to external parties.

Example patterns:
- New external share links created.
- Changes in sharing permissions (e.g., internal-only → anyone with link).
- Sharing with personal or unmanaged accounts.
- Addition of external collaborators to shared folders or repositories.

### 4. OAuth Application Abuse / Third-Party Integrations

Goal: Detect risky or malicious third-party applications that gain broad or unexpected access.

Example patterns:
- New OAuth app consents with sensitive scopes (e.g., Mail.ReadWrite, offline_access).
- Consent to applications from low-reputation publishers.
- Token usage from unusual devices or geographic regions.
- Dormant third-party applications suddenly active with wide access.

### 5. Admin Actions & Configuration Changes

Goal: Detect administrative changes that weaken security posture or indicate prep for deeper compromise.

Example patterns:
- Assignment or removal of admin roles.
- Disabling of security features or retention/audit configurations.
- Slack workspace permission changes.
- GitHub org-level role changes or repo protection rule edits.

### 6. Slack Workspace Misuse

Goal: Detect suspicious lateral communication, persistence, or data access via Slack.

Example patterns:
- Download of sensitive files by unusual users.
- Installation of Slack apps or bots.
- Channel membership changes by unauthorized users.
- OAuth token creation within Slack.

### 7. Developer Platform (GitHub/GitLab) Abuse

Goal: Detect anomalous access or modification of source code and engineering assets.

Example patterns:
- Repo clones from unexpected IP addresses.
- New PATs or SSH keys added to user profiles.
- OAuth applications receiving repository-level permissions.
- Deletion, renaming, or transfer of repositories.

### 8. SaaS Hygiene & Risk Indicators

Goal: Identify structural risks and misconfigurations that increase the likelihood or impact of compromise.

Example patterns:
- Mailboxes without audit logging enabled.
- External sharing allowed by default.
- Overprivileged SaaS administrators.
- Weak or inconsistent retention settings.

These categories serve as the foundation for detection rule selection, AI-assisted rule generation, and findings classification within the SaaS scope area.
