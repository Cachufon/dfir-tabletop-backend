# INTERNAL - TTX Scenario Taxonomy

This document defines the **canonical scenario categories** for Gruve DFIR Tabletop Exercises (TTX).

Use these categories for:
- `scenario.category` in YAML scenarios under `dfir_backend/ttx/scenarios/`
- consistent packaging/reporting across engagements
- future automation (agentic scenario generation, inject orchestration)

## Category naming rules (must follow)
- Use the category strings **exactly** as written in the headings below.
- Store the human-readable scenario summary in `scenario.summary`.
- Keep category stable even when tailoring a scenario for a specific client.

---

## SaaS / Identity
**Description:** Compromise of identities (IdP, email, SaaS apps) leading to mailbox abuse, token theft, OAuth consent abuse, data access, and downstream fraud/social engineering.

**Common entry vectors**
- Phishing / MFA fatigue / token theft
- Password spraying / credential stuffing
- OAuth malicious app consent
- Compromised vendor / shared credentials

**Primary risks tested**
- Incident command ownership and escalation triggers
- Containment tradeoffs (revoke sessions, disable accounts, reset MFA)
- Scope decisions (single user vs tenant-wide compromise)
- Internal + external communications governance

**Typical participants (roles)**
- Security, IT, Exec, Legal/PR, Finance (optional for fraud cases)

**Key decision points**
- When to contain aggressively vs observe briefly
- When and how to notify impacted clients/partners
- How to handle suspected vs confirmed compromise under uncertainty
- What logs/telemetry are required to establish scope

**Common inject themes**
- Unusual sign-in + mailbox rule creation
- Forwarding rules / data access anomalies
- Client receives suspicious email from your domain
- Multiple users targeted (phish wave), potential spread

---

## Ransomware / Extortion
**Description:** Data encryption and/or data theft with extortion demand targeting critical operations.

**Common entry vectors**
- Exploited internet-facing service (VPN/RDP/web app)
- Phishing leading to initial foothold
- Credential compromise + lateral movement
- Managed service provider compromise

**Primary risks tested**
- Business continuity decisions and recovery sequencing
- Containment authority (network isolation vs uptime)
- Executive decision rights under uncertainty
- Legal/regulatory notification and external comms posture

**Typical participants (roles)**
- IT, Security, Exec, Legal/PR, Finance, Business owners

**Key decision points**
- Declare major incident and activate IR plan
- Containment vs operational continuity
- Restoration prioritization (crown jewels first)
- External communications and notification triggers

**Common inject themes**
- Encryption begins + systems impacted
- Threat actor claims data exfiltration
- Media inquiry / client inquiry arrives
- Third-party (insurer/outside counsel) engagement

---

## Business Email Compromise (BEC) / Fraud
**Description:** Compromised mailbox (or look-alike domain) used for payment fraud, impersonation, and sensitive data theft.

**Common entry vectors**
- Phishing leading to mailbox takeover
- Delegated access abuse / OAuth consent
- Look-alike domain registration + social engineering
- Vendor-side compromise

**Primary risks tested**
- Fraud loss mitigation and financial controls
- Vendor/customer communications coordination
- Evidence handling for civil/regulatory follow-up
- Decision rights between Finance, Security, and Exec

**Typical participants (roles)**
- Security, Finance/AP, Legal/PR, IT, Exec

**Key decision points**
- Transaction holds and recall attempts
- Notification to bank, vendor, impacted clients
- Email containment actions and validation steps
- Whether to engage outside counsel/insurer

**Common inject themes**
- Invoice diversion attempt discovered late
- Vendor disputes payment instructions
- Multiple fraudulent threads identified
- Legal/PR pressure to disclose vs confirm

---

## Insider / Data Exfiltration
**Description:** Malicious or negligent insider removes sensitive data from the environment (often via cloud storage, email, or removable media).

**Common entry vectors**
- Disgruntled employee or contractor
- Excessive permissions + weak monitoring
- Shadow IT file sharing
- Offboarding gaps

**Primary risks tested**
- Coordination between Security, HR, and Legal
- Evidence handling for civil/regulatory actions
- Access suspension and containment without retaliation risk
- Communications to stakeholders and leadership

**Typical participants (roles)**
- Security, HR, Legal, IT, Exec, Data owners

**Key decision points**
- When to suspend access and how broadly
- Preservation actions (legal hold, log retention)
- Employee communications and HR actions
- Notification triggers and contractual obligations

**Common inject themes**
- Large downloads from sensitive repo
- Upload to personal cloud storage
- Unapproved forwarding to personal email
- Offboarding occurs during investigation

---

## Cloud (IaaS) Compromise
**Description:** Unauthorized access to cloud control plane (AWS/Azure/GCP) leading to resource manipulation, data access, or persistence.

**Common entry vectors**
- Leaked access keys / tokens
- Compromised CI/CD credentials
- Misconfigured identity policies
- Compromised admin workstation

**Primary risks tested**
- Cloud incident containment mechanics (key rotation, policy lockdown)
- Blast-radius assessment and scoping decisions
- Coordination between Cloud Ops, Security, and Product owners
- Third-party / customer notification decisions (SLA/SOC2 posture)

**Typical participants (roles)**
- Cloud Ops, Security Engineering, Product/Engineering, Exec, Legal/PR

**Key decision points**
- Freeze vs continue deployments
- Containment steps that may cause outages
- Scope actions (which accounts/subscriptions/projects)
- External notification and messaging posture

**Common inject themes**
- New IAM principals created
- Logging altered or disabled
- Unexpected egress or snapshot activity
- Production impact risk vs containment urgency

---

## Third-Party / Supply Chain
**Description:** Incident originates from a vendor/partner/managed service provider or software update chain.

**Common entry vectors**
- Vendor compromise and lateral access via SSO/VPN
- Compromised integration token/API key
- Software update or package compromise
- MSP tooling compromise

**Primary risks tested**
- Vendor management and contractual obligations
- Coordinated incident response with third parties
- Containment of integrations and access pathways
- External communications and trust management

**Typical participants (roles)**
- Security, IT, Procurement/Vendor Mgmt, Legal/PR, Exec, Product (optional)

**Key decision points**
- Disable vendor access vs business disruption
- Data sharing boundaries with vendor
- Notification triggers and customer commitments
- Validation requirements before restoring connectivity

**Common inject themes**
- Vendor reports breach impacting your tenant
- Suspicious activity traced to integration account
- Vendor requests logs or access for investigation
- Customer asks for attestation and details

---

## Web Application / API Breach
**Description:** Web app or API compromise resulting in unauthorized access, data exposure, or integrity issues.

**Common entry vectors**
- Exploited vulnerability (auth bypass, injection, deserialization)
- Credential abuse against admin portals
- Misconfigured storage or API authorization flaws

**Primary risks tested**
- Product/security coordination and release management under incident pressure
- Containment (disable features, hotfix vs rollback)
- Customer/regulatory notification decisions under uncertainty
- Evidence preservation and scope mapping (what data, which users)

**Typical participants (roles)**
- Product/Engineering, Security, IT (optional), Exec, Legal/PR, Support

**Key decision points**
- Feature disablement vs continuity
- Patch rollout strategy and verification
- Customer messaging and support escalation
- Determining exposure scope and impacted populations

**Common inject themes**
- Bug bounty report escalates to active exploitation
- Customer reports anomalous access to records
- Logs show unusual API enumeration
- Pressure to disclose before full scope confirmed

---

## AI System Misuse / Prompt Abuse
**Description:** Abuse of AI systems to extract sensitive data, bypass controls, poison inputs, or produce harmful outputs.

**Common entry vectors**
- Prompt injection via external content
- Data leakage through retrieval augmentation (RAG)
- Model output abuse (policy bypass)
- Insider misuse of AI tooling

**Primary risks tested**
- Responsible AI governance and guardrails
- Data handling and least-privilege access to knowledge sources
- Legal/privacy review, disclosures, and customer communications
- Product decisions: disable feature vs degrade capability

**Typical participants (roles)**
- AI/ML Engineering, Product, Security, Legal/PR, Exec

**Key decision points**
- Suspend feature vs apply mitigations
- Confirm and scope data exposure
- Customer communication posture and approvals
- Long-term governance/control changes

**Common inject themes**
- User reports model returned sensitive internal content
- Red-team finds prompt bypass method shared publicly
- Logging reveals repeated extraction attempts
- Media inquiry about AI safety incident

---

## Tailoring guidance (internal)
When tailoring a scenario for a client:
- Keep `scenario.category` unchanged (use canonical categories above).
- Tailor *within* `scenario.business_context`, `scenario.assumptions`, and inject prompts.
- Store client-tailored scenarios OUTSIDE git (secure project storage).
- If a scenario does not fit any category above, add a new category here first (small PR, internal review).
