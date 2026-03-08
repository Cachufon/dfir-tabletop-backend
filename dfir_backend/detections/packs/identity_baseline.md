# Identity Baseline Pack

Use this pack to cover identity-focused detections drawing from normalized identity datasets.

- Source rules from `dfir_backend/rules/sigma/` that relate to identity and authentication flows.
- Typical categories: suspicious sign-ins, MFA abuse, OAuth abuse, and administrative actions.
- Pair Sigma rules with case-specific overrides in `dfir_backend/custom/<case_id>/` when needed.
