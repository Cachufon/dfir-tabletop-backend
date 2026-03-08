# Identity Scope Area Workflow (Stub)

This document outlines the high-level workflow for running the Identity scope area within a Compromise Assessment. It is designed to be used both:

- As a standalone Identity-only assessment, and
- In combination with SaaS and Endpoint scope areas.

## High-Level Steps (v1 Stub)

1. Confirm in-scope identity provider(s) and time window.
2. Collect identity logs:
   - Primary IDP logs (Okta, Entra / Azure AD, or Google Workspace).
   - MFA events, if applicable.
3. Normalize and prepare identity events for analysis.
4. Apply identity-focused detection logic (e.g., risky sign-ins, MFA abuse, suspicious OAuth grants).
5. Triage and investigate notable identity events.
6. Summarize identity-related findings, including suspected account compromise and high-risk users.
7. When combined with other scope areas, provide a list of suspect users and sessions to SaaS and/or Endpoint workflows.

This file will be expanded with more detailed steps, queries, and mappings to specific detection rules.

## Identity Scope Area Detection Categories (v1)

The Identity scope area focuses on detecting identity-centric behaviors that indicate account compromise, abuse of access, or weakening of defenses. The following are the initial detection categories we intend to cover with rules and queries:

### 1. Account Takeover / Suspicious Sign-ins

Goal: Identify logins that are unlikely to be legitimate.

Example patterns:
- Impossible travel (logins from distant geolocations within a short time window).
- Logins from unusual IP ranges or ASNs (e.g., hosting providers, TOR exit nodes, foreign regions).
- New or unusual device fingerprints per user.
- Successful sign-ins after multiple failed attempts.
- Use of legacy or weak auth flows that are not typical for the environment.

### 2. MFA Abuse & MFA Weakness

Goal: Detect abuse or bypass of MFA mechanisms.

Example patterns:
- MFA fatigue / push bombing (many prompts in a short period, followed by eventual success).
- Repeated MFA prompts denied or refused by the user.
- MFA approvals from unusual locations or devices.
- Registration of new MFA methods shortly before suspicious activity.
- Removal or disabling of MFA for specific high-risk accounts.

### 3. Privilege and Role Escalation

Goal: Detect unauthorized or risky elevation of privileges.

Example patterns:
- New admin roles granted to standard users.
- Privilege assignments during atypical times (late nights, weekends, or outside change windows).
- Creation or enabling of powerful service accounts.
- Assignment of roles that allow wide access to identity configuration or application management.

### 4. OAuth / Application Abuse

Goal: Detect abuse of OAuth or application integrations for access and persistence.

Example patterns:
- New OAuth applications with broad or sensitive scopes (e.g., Mail.ReadWrite, offline_access).
- Consent to applications from low-reputation publishers.
- Unusual token usage patterns (e.g., tokens used from unexpected locations).
- Dormant or rarely used apps that suddenly become active and access large volumes of data.

### 5. Policy / Configuration Changes

Goal: Detect weakening or misconfiguration of identity security policies.

Example patterns:
- Changes to Conditional Access policies that reduce enforcement.
- Disabling of security defaults or baseline protection policies.
- Changes that reduce or remove MFA requirements.
- Disabling sign-in risk evaluation or related protections.

### 6. Identity Hygiene / Risk Indicators

Goal: Identify structural identity risks that increase likelihood or impact of compromise.

Example patterns:
- High-privilege accounts without MFA enabled.
- Dormant accounts with standing access to sensitive resources.
- Excessive or unused administrator roles.
- Overly broad or unused application permissions and consents.

These categories will guide rule development (Sigma, IOC searches, AI-based analysis) and provide structure for how Identity scope area findings are grouped and reported.
