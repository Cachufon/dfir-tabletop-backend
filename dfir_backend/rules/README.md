# DFIR Rules

This folder contains all detection and hunting rules used by Gruve DFIR.

We follow native community formats to preserve compatibility and analyst familiarity:
- Sigma for log/SIEM and compromise assessment detections.
- YARA for file, memory, and binary detections.
- IOC bundles for indicator packs (hashes, IPs, domains, URLs, etc.).
- NOVA rules for AI prompt pattern detection (inspired by YARA but tailored to prompts).

macOS Investigations, Compromise Assessments (including the Threat Hunting & Recovery Validation add-on), and Tabletop Exercises all draw from this rule library.

See `rules_index.md` for a curated mapping of which rules are relevant to each service.
