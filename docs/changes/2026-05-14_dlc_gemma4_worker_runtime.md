# DLC Gemma4 Worker Runtime

## Summary

This change wires the Auto-Asset DLC submission path to the Genesis-LLM-style worker runtime pattern:

```text
submit_*.sh -> submit_batch.py -> launch_job.sh -> run_task.sh -> python_runtime.sh -> python -m auto_asset_annotator.main
```

The Gemma4 path now has a maintained GRScenes reannotation wrapper, explicit worker setup/env forwarding, dry-run-by-default submission semantics, and output-directory guards to keep new Gemma4 output out of the older Qwen result folders.

## What Changed

- Added `scripts/dlc/submit_gemma4_reannotate.sh`.
- Made `submit_batch.py` default to dry-run and require `--submit` for real submission.
- Made dry-run launcher validation fail the process when any chunk fails validation.
- Made `launch_job.sh` embed an allowlist of runtime env vars into the worker command:
  - `DLC_WORKER_SETUP_SCRIPT`
  - `AUTO_ASSET_VENV`
  - `DLC_PYTHON_RUNTIME`
  - `UNSLOTH_COMPILE_LOCATION`
  - `MODEL_BACKEND`
  - `MODEL_PATH`
  - `API_BASE_URL`
  - `API_KEY_ENV`
  - offline/cache flags
- Made `launch_job.sh` require explicit `DLC_WORKSPACE_ID` and `DLC_RESOURCE_ID` for real submission.
- Made `launch_job.sh` require `DLC_DRY_RUN=0` and a per-job `DLC_REAL_SUBMIT_CONFIRM` for real submission.
- Made `run_task.sh` source `DLC_WORKER_SETUP_SCRIPT` before resolving the Python runtime.
- Made `python_runtime.sh` prefer `AUTO_ASSET_VENV/bin/python` before falling back to `.venv_dlc` / `.venv`.
- Made `python_runtime.sh` reject `MODEL_BACKEND=local_gemma4_multimodal` when `MODEL_PATH` is empty.
- Updated DLC docs and Gemma4 smoke docs with the new batch reannotation entrypoint.

## GRScenes Reannotation Contract

Source dataset:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets
```

Current preflight count:

```text
79 categories
53,167 category/asset_id directories
53,167 assets with front.png, left.png, back.png, and right.png
0 assets missing required view images
```

Old outputs that must not be overwritten:

```text
./output
./output_reannotate
```

New Gemma4 output root:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/<run_id>/output
```

The Gemma4 wrapper refuses the old output roots, refuses the source dataset tree, and now requires the exact output shape:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/<run_id>/output
```

It also rejects protected `EXTRA_MAIN_ARGS` tokens that could override wrapper-owned routing, chunking, or model flags.

## Recommended Operator Flow

1. Generate an explicit asset list under the run root.
2. Dry-run `submit_gemma4_reannotate.sh` and confirm:
   - output path contains `annotation_runs/<run_id>/output`
   - final worker command contains `DLC_WORKER_SETUP_SCRIPT`
   - final worker command contains `AUTO_ASSET_VENV`
   - final worker command contains `MODEL_BACKEND=local_gemma4_multimodal`
   - final worker command contains the pinned Gemma4 release `MODEL_PATH`
   - final worker command contains `UNSLOTH_COMPILE_LOCATION`
3. Run a tiny real DLC probe with `--submit`, explicit workspace/resource IDs, and one or a few assets. The wrapper path will inject the per-job submit confirmation automatically.
4. Inspect worker logs and output JSON.
5. Scale to a small multi-category run.
6. Only then submit the full all-asset run. Recommended full-run chunking starts with `TOTAL=64` (about 831 assets/chunk); `TOTAL=96` is a finer retry-granularity option if quota allows. Keep `TOTAL <= 100` unless intentionally overriding `submit_batch.py --max-total`.

## Verification Evidence

Fresh local verification for this change:

```text
bash -n scripts/dlc/launch_job.sh
bash -n scripts/dlc/run_task.sh
bash -n scripts/dlc/python_runtime.sh
bash -n scripts/dlc/submit_gemma4_reannotate.sh
python -m py_compile scripts/dlc/submit_batch.py
python -m unittest tests.test_dlc_scripts
```

The DLC unittest suite covered default dry-run behavior, explicit submit env propagation, launcher real-submit guards, worker setup sourcing, `AUTO_ASSET_VENV` selection, and the Gemma4 reannotation wrapper output guard.
