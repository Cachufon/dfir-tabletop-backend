# INTERNAL - TTX Intake Template

Use this template to capture the minimum information needed to scope, tailor, and deliver a discussion-based Tabletop Exercise (TTX).

**Data handling rule:** Do not paste client-sensitive artifacts into git. This document is intended to be copied into secure project storage (outside git) and filled there.

---

## How to fill

- Required fields are clearly marked.
- If unknown, write "Unknown" or "TBD" (do not leave blank).
- Put questions you can’t answer yet under "Notes / open questions".

---

## 0) Minimum required (10 minutes) — REQUIRED

- Engagement / Case ID:
- Client / Organization:
- Target exercise date:
- Timezone:
- Delivery format: (Virtual / In-person)
- Duration: (60 / 90 / 120 minutes)

### Desired audience(s) (roles) — REQUIRED
Selected: __________________
- [ ] Executive
- [ ] IT
- [ ] Security
- [ ] Legal
- [ ] PR / Comms
- [ ] HR
- [ ] Finance
- [ ] Product / Engineering
- [ ] Vendor / MSSP (optional)

### Primary objectives (3–5; decision-focused) — REQUIRED
- 
- 
- 

### Top 3 leadership concerns (in their words, if possible) — REQUIRED
- 
- 
- 

### Preferred scenario category (choose one) — REQUIRED
Selected: __________________
- [ ] SaaS / Identity
- [ ] Ransomware / Extortion
- [ ] Business Email Compromise (BEC) / Fraud
- [ ] Insider / Data Exfiltration
- [ ] Cloud (IaaS) Compromise
- [ ] Third-Party / Supply Chain
- [ ] Web Application / API Breach
- [ ] AI System Misuse / Prompt Abuse
- [ ] No preference (facilitator to recommend)

---

## Optional / fill later (improves tailoring)

### 1) Engagement metadata — OPTIONAL

- Date requested:
- Facilitator (role):
- Scribe (role):
- Customer POC(s) (role only):
- Recording requested? (Yes/No)
  - If Yes: where will recording be stored (secure location)?

---

### 2) Objectives and success criteria — OPTIONAL

### What “success” looks like (3–6 bullets)
Examples: “clear incident commander”, “time-boxed containment decisions”, “notification approvals defined”.

- 
- 
- 

### Audience focus (choose one primary)
Selected: __________________
- [ ] Executive decision-making and governance
- [ ] Technical response coordination (IT/Security)
- [ ] Communications + Legal/PR coordination
- [ ] Cross-functional alignment (Exec + Technical + Legal/PR)

---

### 3) Business context (minimum viable) — OPTIONAL

### Crown jewels (what matters most)
List top 3–5 business-critical assets/services/data.

- 
- 
- 

### Critical services and dependencies
What services must stay up? Any hard constraints?

- 
- 
- 

### High-impact outcomes to avoid
Examples: customer data exposure, prolonged outage, fraud loss, regulatory action, brand damage.

- 
- 
- 

---

### 4) Environment summary (high level; do not include secrets) — OPTIONAL

Identity / SSO:
Selected: __________________
- [ ] Okta
- [ ] Entra ID (Azure AD)
- [ ] Google Workspace
- [ ] Other: __________

Email / collaboration:
Selected: __________________
- [ ] Microsoft 365
- [ ] Google Workspace
- [ ] Slack
- [ ] Other: __________

Endpoint / EDR:
Selected: __________________
- [ ] CrowdStrike
- [ ] Defender for Endpoint
- [ ] SentinelOne
- [ ] Other: __________

Cloud:
Selected: __________________
- [ ] AWS
- [ ] Azure
- [ ] GCP
- [ ] None / On-prem only
- Notes (high level): __________

Key third parties (optional):
- MSSP / SOC provider: __________
- Incident response retainer (if any): __________
- Critical vendors relevant to incident response: __________

---

### 5) IR governance and decision rights (what we are testing) — OPTIONAL

### Incident command / roles
- Who acts as incident commander during major incidents? (role)
- Is there a defined incident bridge / war room process? (Yes/No/Unknown)

### Severity classification
- Is there a severity classification system? (Yes/No/Unknown)
- If Yes: summarize levels and triggers (high level)

### Escalation thresholds
- What triggers executive escalation? (e.g., outage, data exposure suspicion, extortion)
- What triggers Legal/PR involvement?

### Containment decision rights
Who can authorize:
- service isolation / shutdown / major disruption? (role)
- user account disablement / token revocation? (role)
- blocking vendor access / integrations? (role)

### Communications governance
- Who is authorized to communicate externally? (role)
- Who approves external statements? (role)
- Is there a “single source of truth” process for internal updates? (Yes/No/Unknown)

### Notification decision points
- Are there known contractual notification obligations? (Yes/No/Unknown)
- Any regulatory regimes that matter (high level)? (e.g., sector/regional obligations)

---

### 6) Constraints / redlines (must capture) — OPTIONAL

- Topics to avoid (check all that apply):
  Selected: __________________
  - [ ] Ransom payment discussion
  - [ ] Law enforcement engagement
  - [ ] Internal HR/employee discipline details
  - [ ] Technical deep dives (keep decisions only)
  - [ ] Other: __________
- Confidentiality level: (Internal only / Client shareable / Limited distribution)
- Notes handling: where will notes be stored (secure location)?

---

### 7) Scenario selection preferences — OPTIONAL

Preferred scenario category (choose one; align with dfir_backend/ttx/scenario_taxonomy.md):
Selected: __________________
- [ ] SaaS / Identity
- [ ] Ransomware / Extortion
- [ ] Business Email Compromise (BEC) / Fraud
- [ ] Insider / Data Exfiltration
- [ ] Cloud (IaaS) Compromise
- [ ] Third-Party / Supply Chain
- [ ] Web Application / API Breach
- [ ] AI System Misuse / Prompt Abuse
- [ ] No preference (facilitator to recommend)

Preferred realism level:
Selected: __________________
- [ ] Basic (verbal prompts only)
- [ ] Medium (mix of verbal + email/chat injects)
- [ ] High (simulated artifacts references + more branching)

---

### 8) Deliverables and scoring preferences — OPTIONAL

Deliverables requested:
Selected: __________________
- [ ] After-Action Report (AAR) + Improvement Plan (0/30/90)
- [ ] 1-page executive readout
- [ ] Consolidated improvement backlog (optional)

Scoring preference:
Selected: __________________
- [ ] Include numeric scores in AAR
- [ ] Keep numeric scores internal; provide qualitative assessment only

---

### 9) Optional: AI assistance permissions (for agentic workflow design) — OPTIONAL

The following are OPTIONAL and must be approved by the client.

- AI may read the customer IR plan to extract roles/escalation paths: (Yes/No)
- AI may generate a draft scenario YAML (reviewed by facilitator): (Yes/No)
- AI may draft an AAR outline from scribe notes (reviewed by facilitator): (Yes/No)

If Yes to any:
- Confirm storage/retention expectations for prompts/outputs (must be in secure storage, not git):
- Confirm redaction requirements (PII/secrets removal) before AI usage:

---

### 10) Notes / open questions — OPTIONAL

- 
- 
- 
