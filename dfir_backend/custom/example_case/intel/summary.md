# EXAMPLE Post-Incident Intel Summary

## Scenario Overview
- **Identity Target:** Single user `alice@example.com` reported multiple unsolicited MFA prompts over a 15-minute window.
- **Suspicious Access:** Subsequent successful login originated from a foreign IP in the documentation block `198.51.100.42`.
- **SaaS Change:** Attacker created an Outlook rule to forward all inbound mail to `exfil@example.net` using a newly granted mailbox rule permission.

## Key Questions
1. Did MFA fatigue result in unauthorized session establishment?
2. Were additional assets or applications accessed from the suspicious IP?
3. What mailbox or SaaS configuration changes occurred after the suspicious login?

## Investigative Leads
- Correlate MFA challenge frequency and outcomes for `alice@example.com`.
- Trace session tokens or device identifiers tied to IP `198.51.100.42`.
- Enumerate mailbox rule creations and forwarding destinations following the login.
