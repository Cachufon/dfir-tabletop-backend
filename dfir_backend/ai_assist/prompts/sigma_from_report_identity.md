# Prompt: Generate Identity Sigma Rules from Incident Summary

## Purpose

Use this prompt when you want an AI model to generate Sigma detection rules for the Identity scope area (Okta, Entra / Azure AD, Google Workspace, etc.) based on a structured incident summary and detection_plan.yaml found in a custom case folder under dfir_backend/custom/.

The goal is to translate described TTPs and detection goals into concrete Sigma rules that can be used in Gruve Compromise Assessments (Broad Sweep, Post-Incident, or Targeted Threat Hunt).

---

## Inputs

You should provide the model with:

1. The contents of `intel/summary.md` from a specific case:
   - Background
   - Environment
   - TTPs observed or suspected
   - IOCs (high-level)
   - Detection goals

2. The contents of `detection_plan.yaml` for the same case, focusing on:
   - `scope_areas.identity.goals`
   - Any `scope_areas.identity.outputs.sigma_rules` names, if present

3. The reference Sigma template at:
   - `dfir_backend/rules/sigma/SIGMA_RULE_TEMPLATE.yml`

---

## Instructions to the Model (v1)

You are an expert detection engineer. Based on the incident summary, detection goals, and the Sigma rule template:

1. Identify identity-related behaviors from the summary that should have corresponding detections, especially:
   - Suspicious sign-ins (locations, devices, IP ranges, time patterns)
   - MFA abuse or MFA fatigue patterns
   - Unauthorized or risky admin / role changes
   - Risky OAuth or app consent activity
   - Policy changes that weaken security

2. For each high-priority behavior, generate one Sigma rule in YAML format using the structure from `SIGMA_RULE_TEMPLATE.yml`. At a minimum, populate:
   - `title`
   - `id` (use a placeholder like GRV-CUSTOM-IDENTITY-XXXX)
   - `description`
   - `logsource` (Okta / Azure AD / Google Workspace, etc.)
   - `detection` (with a reasonable selection + condition, even if approximate)
   - `fields`
   - `falsepositives`
   - `level`
   - `tags` (include at least one relevant MITRE ATT&CK technique, if known)

3. Make reasonable assumptions about the log fields, but keep them realistic for the specified identity provider (Okta, Entra / Azure AD, or Google). If unsure, name the fields generically (e.g., user, ip_address, location, mfa_method) and document assumptions in comments.

4. If `detection_plan.yaml` specifies names under `scope_areas.identity.outputs.sigma_rules`, use those as the `title` or as part of the `title` where it makes sense.

5. Output only valid Sigma YAML rules. Multiple rules should be separated clearly (for example, with `---` between them).

---

## Output

The expected output is one or more Sigma rule definitions in YAML, ready to be saved under:

`dfir_backend/custom/<case_id>/sigma/`

with filenames that match the rule intent (for example, `sigma_case_<case_id>_okta_mfa_fatigue.yml`).

Ensure the markdown formatting is preserved correctly when updating these files.
