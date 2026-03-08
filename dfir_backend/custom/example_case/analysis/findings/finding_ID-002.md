# EXAMPLE Finding ID-002

## Finding ID
ID-002

## Title
Mailbox Forwarding Rule Enabling Potential Exfiltration

## Category (Identity / SaaS / Endpoint / Executive)
SaaS

## Description
Immediately after the foreign login, the account `alice@example.com` configured mailbox forwarding to `exfil@example.net` and created an inbox rule to redirect all messages. The actions originated from `198.51.100.42` and align with common data exfiltration preparation.

## Evidence Summary
- `Set-Mailbox` event setting `ForwardingSmtpAddress` to `exfil@example.net`.
- `New-InboxRule` creating "EXAMPLE auto-forward all" from the same IP and session window.
- Temporal relationship to MFA fatigue and foreign login events.

## Impact
High risk of confidential mail being forwarded to an external domain without detection, leading to data loss.

## Likelihood / Confidence
High likelihood based on confirmed configuration changes and matching source IP; high confidence given correlated timeline.

## Severity
High

## Recommended Actions
- Remove forwarding address and inbox rule from `alice@example.com`.
- Review mailbox access logs for message access or downloads.
- Implement alerts for new forwarding rules targeting external domains.

## Related Data Sources
- SaaS audit logs for mailbox changes.
- Identity authentication logs to confirm session lineage.

## ATT&CK Mapping
- T1114.003: Email Collection: Email Forwarding Rule
- T1078: Valid Accounts
