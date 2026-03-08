# Identity Scope Area Data Sources

This document describes the minimum and optional data sources required to run the Identity scope area effectively.

## Minimum Data Sources

At least ONE of the following identity providers must be available:

- Okta System Logs, OR
- Entra / Azure AD sign-in logs, OR
- Google Workspace login/admin logs

And, in addition:

- Authentication / sign-in events (success and failure) for in-scope users
- MFA events (e.g., push, app, SMS, FIDO), when in use

These minimum sources allow Gruve to:
- Identify risky sign-in patterns
- Detect potential account takeover
- Review MFA usage and potential MFA fatigue patterns

## Optional Data Sources (Recommended Where Available)

- IDP audit/admin logs (admin role changes, app assignments, policy changes)
- OAuth / app grant logs (applications, scopes, and token usage)
- SAML logs (SSO assertions, application mappings)
- Risk or anomaly logs (e.g., “risky sign-in” feeds or conditional access events)

Optional sources strengthen:
- Detection of subtle abuse (OAuth-based access, stealthy admin actions)
- Understanding of how identities map to applications and privileges
- Confidence in identity-related findings and severity ratings
