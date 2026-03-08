# Prompt: Generate SaaS Sigma Rules from Incident Summary

## Purpose

Use this prompt when generating Sigma detection rules for the SaaS scope area
(O365, Google Workspace, Slack, GitHub) from a structured incident summary
and detection_plan.yaml located under dfir_backend/custom/<case>.

The goal is to translate described TTPs and detection goals into concrete
Sigma rules that help identify mailbox manipulation, file exfiltration,
SaaS misuse, admin abuse, OAuth anomalies, or other SaaS-related threats.

---

## Inputs

Provide the model with:

1. The contents of `intel/summary.md` from the selected custom case:
   - Background
   - SaaS platforms in scope
   - TTPs observed or suspected
   - IOCs (high-level)
   - Detection goals

2. The contents of `detection_plan.yaml` focusing on:
   - scope_areas.saas.goals
   - scope_areas.saas.outputs.sigma_rules

3. The Sigma rule template located at:
   `dfir_backend/rules/sigma/SIGMA_RULE_TEMPLATE.yml`

---

## Instructions to the Model (v1)

You are an expert SaaS forensics and detection engineer. Based on the
incident summary, detection goals, and Sigma rule template:

1. Identify SaaS-related behaviors from the summary that require detection, such as:
   - Mailbox manipulation (rules, forwarding, filters, delegates)
   - File access anomalies (mass downloads, abnormal access patterns)
   - External sharing or data exposure
   - OAuth app consent or token misuse
   - Slack workspace anomalies (apps, file downloads, admin changes)
   - GitHub anomalies (PATs, SSH keys, repo clones)
   - Admin or configuration changes that weaken security

2. For each relevant behavior, generate a Sigma rule using the template structure. Populate at least:
   - `title`
   - `id` (placeholder: GRV-CUSTOM-SAAS-XXXX)
   - `description`
   - `logsource` (o365/exchange/sharepoint, google, slack, github)
   - `detection`
   - `fields`
   - `falsepositives`
   - `level`
   - `tags` (include MITRE ATT&CK mappings if applicable)

3. Make realistic assumptions about SaaS log fields depending on the platform. If unsure, use generic names and include a comment explaining assumptions.

4. If detection_plan.yaml provides rule names, incorporate them into titles or descriptions when appropriate.

5. Output **only valid Sigma YAML rules**, separating multiple rules with `---`.

---

## Output

Output one or more Sigma rule definitions in YAML, ready to be saved under:

`dfir_backend/custom/<case_id>/sigma/`

Example filename:
`sigma_case_<case_id>_o365_external_forwarding.yml`

Ensure valid YAML formatting and follow Sigma style conventions.

---

Ensure all markdown is properly formatted.
