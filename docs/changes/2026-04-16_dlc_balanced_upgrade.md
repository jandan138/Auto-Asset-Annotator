# DLC Balanced Upgrade

## Research / Investigation

- Reviewed the Task 4 scope in `docs/superpowers/plans/2026-04-16-dlc-balanced-upgrade.md` and the design notes in `docs/superpowers/specs/2026-04-16-dlc-balanced-upgrade-design.md`.
- Read the current DLC scripts and docs to align the operator-facing updates with the implemented submission chain.
- Confirmed the earlier launch contract bug documented by the plan: duplicated chunk arguments had to be fixed so the maintained path is now `run_task.sh <chunk_id> <chunk_total> [extra main.py flags...]`.
- Reviewed `tests/test_dlc_scripts.py` to keep wrapper verification grounded in the existing subprocess harness.

## Design Decisions

- Added four small wrapper scripts instead of importing the broader `usd-scene-physics-prep` mode matrix, because this repository only needs a few high-frequency annotation operations.
- Kept the wrappers thin and repetitive on purpose: they standardize `submit_batch.py` usage without hiding the underlying chunked submission chain.
- Used environment-variable overrides such as `TOTAL`, `NAME`, `INPUT_DIR`, `OUTPUT_DIR`, `ASSET_LIST_FILE`, and `EXTRA_MAIN_ARGS` so operators can adjust common parameters without editing the scripts.
- Kept `submit_asset_list.sh` as the only wrapper that requires an explicit asset-list path, because that workflow is inherently list-specific.
- Documented `python_runtime.sh` as the dedicated runtime seam because environment discovery and preflight should live outside `run_task.sh`.
- Shell-escaped the wrapper-built `COMMAND_ARGS` payload so spaced paths survive through `submit_batch.py` and its `shlex.split(...)` step.

## Code Changes

- Added `scripts/dlc/submit_annotate.sh` as the canonical wrapper for full annotation batches.
- Added `scripts/dlc/submit_retry_failed.sh` as the canonical wrapper for `archive/temp_lists/failed_assets.txt` plus `--force`.
- Added `scripts/dlc/submit_retry_incomplete.sh` as the canonical wrapper for `--retry_incomplete` reruns.
- Added `scripts/dlc/submit_asset_list.sh` as the canonical wrapper for explicit `--asset_list_file` runs.
- Updated all four wrappers to build their baked-in `COMMAND_ARGS` with shell escaping instead of unsafe plain-string flattening.
- Rewrote `docs/dlc/README.md` into an operator runbook centered on supported workflows, preflight, profiles, monitoring, validation, reruns, and backend notes.
- Rewrote `docs/dlc/TESTING.md` into a smoke/probe guide with explicit submit-layer versus launch-layer verification boundaries.
- Updated `README.md`, `CLAUDE.md`, and `docs/usage/cli_reference.md` so top-level docs point operators to the maintained DLC workflow and current chunk/rerun flags.

## Testing

- Verified the DLC script subprocess suite with `PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_dlc_scripts`.
- Verified dry-run forwarding with:
  `bash scripts/dlc/submit_annotate.sh --dry-run`
  `bash scripts/dlc/submit_retry_failed.sh --dry-run`
  `bash scripts/dlc/submit_retry_incomplete.sh --dry-run`
  `bash scripts/dlc/submit_asset_list.sh --dry-run --asset_list_file archive/temp_lists/failed_assets.txt`
- Avoided any real DLC submission during verification.

## Open Issues

- The wrappers intentionally cover only the maintained annotation workflows; uncommon operator cases still need raw `submit_batch.py` usage.
- `EXTRA_MAIN_ARGS` remains an operator-provided shell snippet appended after the safely escaped baked-in arguments, so it should still be checked with `--dry-run` before real submission.
