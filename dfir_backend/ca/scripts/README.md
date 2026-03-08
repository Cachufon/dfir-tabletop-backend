# CA Scripts

## Files

- `init_ca_case.py`: Initializes a compromise assessment case skeleton with optional deterministic manifest timestamps.
- `validate_ca_example_case.py`: Validates `dfir_backend/custom/example_case` structure, copies it to a temporary directory, and executes detection stubs.
- `test_deterministic_case_init.py`: Runs deterministic case initialization twice and asserts identical file trees and file contents.

## Usage

```bash
python dfir_backend/ca/scripts/init_ca_case.py --case_dir /tmp/my_case --scope_area identity
python dfir_backend/ca/scripts/init_ca_case.py --case_dir /tmp/my_case --scope_area identity --deterministic
python dfir_backend/ca/scripts/validate_ca_example_case.py
python dfir_backend/ca/scripts/test_deterministic_case_init.py
```
