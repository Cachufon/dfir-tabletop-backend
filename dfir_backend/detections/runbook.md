# Detection Execution Runbook (Phase 1)

This runbook outlines the manual steps for executing detections against normalized datasets. Phase 1 focuses on scaffolding and placeholder outputs while full automation is developed.

## Steps

1. **Confirm normalized data exists**
   - Verify the case directory `dfir_backend/custom/<case_id>/normalized/` contains the datasets required for the scope areas in play.

2. **Identify model and scope areas in scope**
   - Determine which parts of the Model 5 (identity, SaaS, cloud, endpoint, AI) require coverage for the investigation.

3. **Select baseline packs**
   - Use the baseline pack documents under `dfir_backend/detections/packs/` to choose relevant rules from `dfir_backend/rules/` and any case-specific content under `dfir_backend/custom/<case_id>/`.

4. **Run stub scripts to generate placeholders**
   - Execute the stub scripts in `dfir_backend/detections/scripts/` (e.g., `run_sigma_stub.py`, `run_yara_stub.py`, `run_ioc_sweep_stub.py`, `run_maps_stub.py`) with the appropriate `--case_dir`, `--scope_area`, and `--output_dir` arguments to produce expected output folders and placeholder files.
   - These scripts currently do **not** execute engines; they scaffold `hits.json` and `hits_summary.md` for consistent structure.

5. **Place results in analysis directories**
   - Ensure outputs are located under `dfir_backend/custom/<case_id>/analysis/detections/<scope_area>/`.
   - In early engagements, analysts may run detection rules in external tools and paste results into `hits.json` following the contract in `execution_contract.md`.

6. **Generate rollup**
   - Run `rollup_hits.py` to produce `analysis/detections_rollup.md`, aggregating counts per scope area and rule type for reporting.

## Notes

- These scripts are stubs intended to define interfaces and file contracts.
- Replace placeholder content with real detection hits as tooling becomes available.
