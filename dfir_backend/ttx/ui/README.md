# TTX Studio (Local Facilitator App)

TTX Studio is a lightweight local UI to:
1) build a TTX package from a scenario YAML,
2) export participant handouts as offline HTML + ZIP,
3) facilitate injects and capture scribe logs for AAR.

## Critical data handling rule
- Do NOT store or commit client-tailored scenarios or generated packages in git.
- Use secure project storage for outputs (outside the repo).
- The backend scripts include guardrails; do not bypass them for real client work.

## Install (local)
From repo root:

- python3 -m venv .venv
- source .venv/bin/activate
- pip install -r dfir_backend/ttx/ui/requirements.txt

(Optional) install script deps:
- pip install -r dfir_backend/ttx/scripts/requirements.txt

## Run
From repo root:

- streamlit run dfir_backend/ttx/ui/ttx_studio.py

## What it uses
- Package builder: dfir_backend/ttx/scripts/build_ttx_package_from_yaml.py
- Handouts exporter: dfir_backend/ttx/scripts/export_ttx_handouts_html.py
- Validator: dfir_backend/ttx/scripts/validate_ttx_scenarios.py

End.
