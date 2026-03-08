# EXAMPLE Finding ID-001

## Finding ID
ID-001

## Title
MFA Fatigue Approval Leading to Foreign Session

## Category (Identity / SaaS / Endpoint / Executive)
Identity

## Description
Unsolicited MFA push prompts were sent to `alice@example.com` over ~15 minutes. A successful push at 10:14:55Z was immediately followed by a session from `198.51.100.42`, indicating potential coercion and unauthorized access.

## Evidence Summary
- Multiple MFA challenges with mixed outcomes for `alice@example.com`.
- Successful login event from `198.51.100.42` seconds after approval.
- Shared user and timeframe linking MFA fatigue to session start.

## Impact
Potential unauthorized access to identity-backed resources, enabling further SaaS changes and data exposure.

## Likelihood / Confidence
High likelihood based on temporal proximity and foreign IP; medium confidence pending device fingerprint confirmation.

## Severity
High

## Recommended Actions
- Reset credentials and revoke active sessions for `alice@example.com`.
- Enforce number-matching or phishing-resistant MFA methods.
- Monitor for additional attempts from `198.51.100.0/24` and similar ranges.

## Related Data Sources
- Identity platform authentication and MFA logs.
- VPN and proxy logs for corroborating IP usage.

## ATT&CK Mapping
- T1078: Valid Accounts
- T1621: Multi-Factor Authentication Request Generation
