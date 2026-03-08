EXAMPLE REPORT — FOR TRAINING AND TESTING PURPOSES ONLY

# Executive Summary (EXAMPLE)

## Purpose
- Demonstrate how a Compromise Assessment summarizes identity and SaaS risks using synthetic data.
- Provide reusable training material for analysts and tooling validation.

## Key Questions Answered
- Was MFA fatigue used to gain access to `alice@example.com`? **Yes, in this example scenario.**
- Did the attacker establish persistence via mailbox rules? **Yes, through forwarding to `exfil@example.net`.**
- Are additional accounts impacted? **No; scope limited to a single test identity.**

## High-Level Findings
- MFA fatigue prompted unauthorized session creation from `198.51.100.42`.
- Mailbox forwarding and inbox rule changes enabled potential data exfiltration.
- Activity is purely illustrative; no customer data involved.

## Risk Summary
- **Business impact:** Demonstrates how confidential mail could leave the organization if unmitigated.
- **Likelihood:** High within the example due to confirmed configuration changes.
- **Urgency:** Immediate action recommended if observed in production environments.

## Top Recommendations
- Enforce phishing-resistant MFA and limit push retries.
- Alert on foreign logins and new mailbox forwarding to external domains.
- Review and revoke suspicious sessions tied to documentation-range IPs.

## Next 7 / 30 / 90 Day Actions
- **Immediate (7 days):** Remove forwarding rules, reset credentials, enable number-matching MFA.
- **Near term (30 days):** Deploy detections for MFA fatigue and mailbox rule creation; validate alert tuning.
- **Strategic (90 days):** Harden identity governance, periodic mailbox rule audits, and user education on push fatigue.
