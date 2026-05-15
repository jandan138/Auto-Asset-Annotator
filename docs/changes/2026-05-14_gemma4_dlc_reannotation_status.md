# Gemma4 DLC Reannotation Status

**Date**: 2026-05-14
**Dataset**: `/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets`
**Status**: First one-asset real DLC probe failed at runtime preflight; root cause identified and fixed locally. Replacement probe is pending after verification.

## Plain Status

The repository can now construct and submit a Gemma4 DLC batch command without polluting old outputs. The submitted one-asset probe is:

```text
Job ID:   dlc1i6qia2inzfmv
Job name: gemma4_grscenes_probe_0_1
Status:   Failed
Run root: /cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260514T071350Z_gemma4_probe_v1
```

The safe entrypoint remains:

```bash
bash scripts/dlc/submit_gemma4_reannotate.sh --dry-run
```

This wrapper is not a merge/apply step. It writes Auto-Asset wrapped JSON to a new run directory:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/<run_id>/output
```

It does not write to:

```text
./output
./output_reannotate
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets
```

## Dataset Facts

Current filesystem preflight:

| Item | Count |
|------|------:|
| Categories | 79 |
| `category/asset_id` directories | 53,167 |
| Assets with `front.png` / `left.png` / `back.png` / `right.png` | 53,167 |
| Assets missing required view images | 0 |

The earlier 53,171 count and 4 missing-image exception list are stale for the current target directory.

## Runtime Facts

Gemma4 local smoke has already proven the usable Python/model pairing:

```text
AUTO_ASSET_VENV=/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310
MODEL_PATH=/cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8
DLC_WORKER_SETUP_SCRIPT=/cpfs/user/zhuzihou/conda-managed/bin/use-gcc-toolchain-hf-offline.sh
```

`launch_job.sh` now forwards these values into the remote worker command. The repository `.venv_dlc` runtime is still not enough for Gemma4 multimodal inference.

Important runtime packaging detail: this repository uses a `src/auto_asset_annotator` layout. The Genesis QLoRA env does not have `auto_asset_annotator` installed as an editable package, so the DLC runtime must add both `$CODE_ROOT/src` and `$CODE_ROOT` to `PYTHONPATH`.

## Safety Gates Now In Code

- `submit_batch.py` defaults to dry-run.
- Real submission requires `--submit`.
- `launch_job.sh` real submission requires `DLC_SUBMIT=1`, `DLC_DRY_RUN=0`, explicit `DLC_WORKSPACE_ID`, explicit `DLC_RESOURCE_ID`, and a per-job `DLC_REAL_SUBMIT_CONFIRM`.
- `submit_gemma4_reannotate.sh` only accepts the exact `annotation_runs/<run_id>/output` output shape.
- Gemma4 reannotation rejects protected `EXTRA_MAIN_ARGS` overrides for input, output, asset list, chunking, and model selection.
- `python_runtime.sh` rejects `MODEL_BACKEND=local_gemma4_multimodal` without a non-empty `MODEL_PATH`.

## Submitted Probe Record

Probe asset:

```text
basket/6c68230d67112b1dfd2bd7fa9322c756
```

Probe run paths:

```text
RUN_ID=20260514T071350Z_gemma4_probe_v1
RUN_ROOT=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260514T071350Z_gemma4_probe_v1
ASSET_LIST_FILE=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260514T071350Z_gemma4_probe_v1/input/one_asset.txt
OUTPUT_DIR=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260514T071350Z_gemma4_probe_v1/output
```

Submission command used:

```bash
DLC_WORKSPACE_ID=270969 \
DLC_RESOURCE_ID=quota1r947pmazvk \
RUN_ID=20260514T071350Z_gemma4_probe_v1 \
ASSET_LIST_FILE=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260514T071350Z_gemma4_probe_v1/input/one_asset.txt \
TOTAL=1 NAME=gemma4_grscenes_probe \
bash scripts/dlc/submit_gemma4_reannotate.sh --submit
```

Observed DLC state after submission, while queued:

```text
Status: Queuing
ReasonCode: JobEnqueued
ReasonMessage: sync enqueue status from queueUnit status
GmtCreateTime: 2026-05-14T07:14:14Z
GmtSubmittedTime: 2026-05-14T07:14:18Z
```

At this stage no output JSON is expected because the worker has not started. The output directory was checked and had no files while the job was still queuing.

Final observed DLC state:

```text
Status: Failed
ReasonCode: JobFailed
GmtFailedTime: 2026-05-14T15:24:41Z
PodId: dlc1i6qia2inzfmv-master-0
Pod status: Failed
```

Pod log:

```text
ERROR: Failed to import auto_asset_annotator with /cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python from /cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator
```

Root cause:

```text
python_runtime.sh set PYTHONPATH to $CODE_ROOT only.
The package lives at $CODE_ROOT/src/auto_asset_annotator.
The Genesis QLoRA env is valid for Gemma4, but it does not have this repository installed as an editable package.
Therefore the runtime preflight import failed before model loading or asset processing started.
```

Fix:

```text
scripts/dlc/python_runtime.sh now prepends $CODE_ROOT/src:$CODE_ROOT to PYTHONPATH.
```

Local verification of the failed layer after the fix:

```bash
AUTO_ASSET_VENV=/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310 \
DLC_CODE_ROOT=/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator \
bash scripts/dlc/python_runtime.sh -c 'import sys, auto_asset_annotator; print(sys.executable); print(auto_asset_annotator.__file__)'
```

Expected output includes:

```text
/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python
/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/src/auto_asset_annotator/__init__.py
```

Probe logs are under:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260514T071350Z_gemma4_probe_v1/logs
```

Monitor later with:

```bash
./dlc get job dlc1i6qia2inzfmv
find /cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260514T071350Z_gemma4_probe_v1/output -type f -maxdepth 4 -print
```

## Commands For A Future Probe

Create a one-asset probe list:

```bash
RUN_ID=$(date -u +%Y%m%dT%H%M%SZ)_gemma4_probe_v1
RUN_ROOT=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/$RUN_ID
mkdir -p "$RUN_ROOT/input" "$RUN_ROOT/output" "$RUN_ROOT/logs" "$RUN_ROOT/cache"
printf '%s\n' 'basket/6c68230d67112b1dfd2bd7fa9322c756' > "$RUN_ROOT/input/one_asset.txt"
```

Dry-run that probe:

```bash
RUN_ID=$RUN_ID \
ASSET_LIST_FILE="$RUN_ROOT/input/one_asset.txt" \
TOTAL=1 NAME=gemma4_grscenes_probe \
bash scripts/dlc/submit_gemma4_reannotate.sh --dry-run
```

Run the real one-asset DLC probe only after reviewing the dry-run:

```bash
DLC_WORKSPACE_ID=270969 \
DLC_RESOURCE_ID=quota1r947pmazvk \
RUN_ID=$RUN_ID \
ASSET_LIST_FILE="$RUN_ROOT/input/one_asset.txt" \
TOTAL=1 NAME=gemma4_grscenes_probe \
bash scripts/dlc/submit_gemma4_reannotate.sh --submit
```

## Full Run Shape

After the one-asset real probe and a small multi-category run pass, generate the full list:

```bash
DATA_ROOT=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets
RUN_ID=$(date -u +%Y%m%dT%H%M%SZ)_gemma4_full_v1
RUN_ROOT=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/$RUN_ID
mkdir -p "$RUN_ROOT/input" "$RUN_ROOT/output" "$RUN_ROOT/logs" "$RUN_ROOT/cache"
find "$DATA_ROOT" -mindepth 2 -maxdepth 2 -type d -printf '%P\n' | LC_ALL=C sort > "$RUN_ROOT/input/all_assets.txt"
wc -l "$RUN_ROOT/input/all_assets.txt"
```

Expected line count: `53,167`.

Recommended full-run dry-run:

```bash
RUN_ID=$RUN_ID \
ASSET_LIST_FILE="$RUN_ROOT/input/all_assets.txt" \
TOTAL=64 NAME=gemma4_grscenes_full_v1 \
bash scripts/dlc/submit_gemma4_reannotate.sh --dry-run
```

`TOTAL=64` is the current default recommendation, roughly 831 assets per chunk. `TOTAL=96` is reasonable if smaller retry units are more important and quota allows. Keep `TOTAL <= 100` unless intentionally overriding `submit_batch.py --max-total`.

## Evidence Already Recorded

- DLC script tests: `43` passed.
- Model backend tests: `28` passed, `1` skipped.
- Markdown fence check and `git diff --check` passed before commit `8b58a75`.
- Dry-run output showed `annotation_runs/<run_id>/output`, `DLC_WORKER_SETUP_SCRIPT`, `AUTO_ASSET_VENV`, `MODEL_BACKEND=local_gemma4_multimodal`, `MODEL_PATH`, and `UNSLOTH_COMPILE_LOCATION`.
- Protected `EXTRA_MAIN_ARGS='--output_dir ./output'` failed before launcher execution.
- Failed probe diagnosis captured `pod_master_logs_failed_investigation.txt`, `pod_master_events_failed_investigation.txt`, and local reproduction of the import failure.
