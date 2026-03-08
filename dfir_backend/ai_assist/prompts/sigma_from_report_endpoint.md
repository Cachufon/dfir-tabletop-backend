# Prompt: Generate Endpoint Sigma Rules from Incident Summary

## Purpose

Use this prompt when generating Sigma rules for endpoint behavior (via EDR telemetry or similar logs) from a structured incident summary and detection_plan.yaml in dfir_backend/custom/<case>.

The goal is to translate endpoint-related TTPs into Sigma rules that detect persistence, suspicious processes, potential privilege escalation, lateral movement, endpoint exfiltration, or EDR tampering.

---

## Inputs

Provide the model with:

1. `intel/summary.md` for the case:
   - Endpoint OS types involved (macOS, Windows, Linux)
   - Tools used (EDR type, triage tools)
   - Observed/suspected TTPs
   - IOCs

2. `detection_plan.yaml` focusing on:
   - scope_areas.endpoint.goals
   - scope_areas.endpoint.outputs.sigma_rules

3. The Sigma rule template:
   `dfir_backend/rules/sigma/SIGMA_RULE_TEMPLATE.yml`

---

## Instructions to the Model (v1)

You are an expert endpoint forensics and detection engineer. Based on the incident summary and detection goals:

1. Identify endpoint behaviors requiring detection, such as:
   - Persistence mechanisms (LaunchAgents, services, scheduled tasks, registry keys)
   - Suspicious process execution (LOLBins, malware, remote execution tools)
   - Privilege escalation or credential dumping attempts
   - Lateral movement indicators (SSH, RDP, SMB, WMI, remote exec frameworks)
   - EDR tampering and evasion behavior
   - Host-based exfiltration (CLI uploads, archiving + network transfer)
   - Suspicious network behavior from endpoints

2. For each behavior, generate Sigma rules using the template structure. Populate at minimum:
   - title
   - id (placeholder: GRV-CUSTOM-ENDPOINT-XXXX)
   - description
   - logsource (edr, winlog, sysmon, osquery, etc.)
   - detection (selection + condition)
   - fields
   - falsepositives
   - level
   - tags (MITRE ATT&CK if known)

3. Make assumptions about log fields based on EDR type when relevant. If the EDR is unspecified or inconsistent across intel, use generalized field names and document assumptions in comments.

4. Incorporate names from detection_plan.yaml for rule naming when provided.

5. Output only valid Sigma YAML. Separate multiple rules with `---`.

---

## Output

Output Sigma rule files suitable for placement in:

`dfir_backend/custom/<case_id>/sigma/`

Example filename:
`sigma_case_<case_id>_endpoint_persistence.yml`
