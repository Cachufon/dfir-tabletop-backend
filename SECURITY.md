# SECURITY (INTERNAL)

## What this repo is
This repository is Gruve DFIR’s internal delivery backbone: workflows, templates, rule packs, schemas, and tooling stubs.

## What must NEVER be committed
Do not commit any of the following:
- Client data of any kind (raw logs, exports, IR reports, screenshots, tickets, transcripts).
- Credentials, secrets, API tokens, private keys, certificates.
- Anything containing client PII or confidential business information.

## Casework storage
Client casework must live in approved secured evidence storage (e.g., encrypted NAS / evidence media) and be referenced by case ID.

## Synthetic examples
Only explicitly labeled synthetic example data may be committed for testing/training (e.g., dfir_backend/custom/example_case).

## Reporting security issues
Report any security concerns or accidental sensitive commits immediately to the DFIR lead. Rotate secrets and purge history as required.
