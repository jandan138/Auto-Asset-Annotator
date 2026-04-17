# DLC Quota Alignment And Probe

## Research / Investigation

- Compared the repository's current DLC launcher against `usd-scene-physics-prep/scripts/dlc/launch_job.sh`.
- Confirmed that the old parent smartbot quota ID was still being used here.
- Confirmed that the newer reference repo routes `1/2/4 GPU` to `quota1r947pmazvk` and `8 GPU` to `quotaksvqq2oh2pg`.
- Identified three additional operator gaps worth closing:
  - weak chunk validation
  - weak wrapper input validation
  - no canonical probe wrapper

## Design Decisions

- Keep semantic DLC profiles in this repository rather than switching to a pure GPU-count UX.
- Back those semantic profiles with canonical `1/2/4/8 GPU` templates and the new less-gpu / more-gpu quota routing.
- Add fail-fast validation where operators are most likely to make mistakes.
- Add `submit_probe.sh` as the smallest safe real-submit workflow rather than expecting operators to improvise probe commands.

## Code Changes

- Updated `scripts/dlc/launch_job.sh` so quota/resource templates are derived from canonical GPU-count mappings.
- Added chunk-value validation to `launch_job.sh`.
- Strengthened `scripts/dlc/python_runtime.sh` with backend-specific preflight for `openai_compatible` and local model-path checks.
- Added wrapper-level existence checks to `submit_retry_failed.sh` and `submit_asset_list.sh`.
- Added `scripts/dlc/submit_probe.sh`.
- Tightened the probe wrapper so it requires an explicit backend and an explicit asset-list file, preventing accidental full-dataset probe submissions.
- Updated DLC operator docs with:
  - current quota mapping
  - semantic-profile-to-template explanation
  - explicit API/local probe recipes

## Testing

- `PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_dlc_scripts`
- `MODEL_BACKEND=openai_compatible ASSET_LIST_FILE=archive/temp_lists/probe_assets.txt bash scripts/dlc/submit_probe.sh --dry-run`
- final fake-launcher probes should verify:
  - `1 GPU -> quota1r947pmazvk`
  - `8 GPU -> quotaksvqq2oh2pg`

## Open Issues

- This pass does not submit a real probe job; it only prepares and validates the maintained probe workflow.
- If the cluster policy changes again, the canonical GPU-count template table in `launch_job.sh` should be refreshed from the current operator reference repo.
