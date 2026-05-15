# Gemma4 DLC Reannotation Status

**Date**: 2026-05-15
**Dataset**: `/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets`
**Status**: First one-asset real DLC probe failed at runtime preflight; root cause identified and fixed. Replacement one-asset probe reached model initialization, then failed because the Gemma4 runtime was using the USD/Isaac image path and lacked `natsort` in the worker-visible Python stack. The Gemma4 wrapper now defaults to the Genesis-LLM successful DLC image, preflights `natsort`, and v3 succeeded with one valid annotation JSON. A later 8-asset multi-category probe succeeded, and the full `53,167`-asset Gemma4 reannotation run has been submitted as 64 DLC chunks into an isolated `annotation_runs` output tree.

## Plain Status

The repository can construct and submit a Gemma4 DLC batch command without polluting old outputs. The current state is:

```text
Full run:   submitted, in progress
Chunks:     64 submitted, 0 submission failures
Snapshot:   4 Running, 60 Queuing, 0 Failed
Run root:   /cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T015209Z_gemma4_full_v1
Output dir: /cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T015209Z_gemma4_full_v1/output
```

This means submission and initial DLC scheduling succeeded. It does not mean the full annotation pass has completed.

The v3 one-asset probe uses the Genesis-LLM successful image and succeeded:

```text
Job ID:   dlc10pg3d6j8izbv
Job name: gemma4_grscenes_probe_v3_0_1
Status:   Succeeded
Run root: /cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T012454Z_gemma4_probe_v3
Image:    pj4090acr-registry-vpc.cn-beijing.cr.aliyuncs.com/pj4090/mahaoxiang:genmanip-mahaoxiang
Output:   output/basket/6c68230d67112b1dfd2bd7fa9322c756_annotation.json
```

The v2 replacement one-asset probe reached model initialization and then failed:

```text
Job ID:   dlc14l1zbec0ofk2
Job name: gemma4_grscenes_probe_v2_0_1
Status:   Failed
Run root: /cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T005924Z_gemma4_probe_v2
Pod log:  Failed to load model: No module named 'natsort'
```

The failure is later than the first probe: repository import succeeded and model initialization started.

The previous one-asset probe failed before model loading because the remote Python runtime could not import this repository's `src` layout:

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

Important image/runtime detail: the Gemma4 path should follow the `genesis-llm` successful QLoRA runtime, not the USD physics-prep runtime.

| Reference project | Successful image | Interpretation for this repo |
|-------------------|------------------|------------------------------|
| `/cpfs/user/zhuzihou/dev/genesis-llm` | `pj4090acr-registry-vpc.cn-beijing.cr.aliyuncs.com/pj4090/mahaoxiang:genmanip-mahaoxiang` | Use for Gemma4 / QLoRA / Unsloth model inference. |
| `/cpfs/shared/simulation/zhuzihou/dev/usd-scene-physics-prep` | `dsw-registry-vpc.cn-beijing.cr.aliyuncs.com/pai-training-algorithm/isaac-sim:isaacsim450-vnc-v8` | Use for Isaac Sim / USD / physics preprocessing; not the right default for Gemma4 model loading. |

The second probe used the USD/Isaac image:

```text
dsw-registry-vpc.cn-beijing.cr.aliyuncs.com/pai-training-algorithm/isaac-sim:isaacsim450-vnc-v8
```

The Gemma4 reannotation wrapper now defaults to the Genesis-LLM image:

```text
pj4090acr-registry-vpc.cn-beijing.cr.aliyuncs.com/pj4090/mahaoxiang:genmanip-mahaoxiang
```

The worker-visible `AUTO_ASSET_VENV` now also has `natsort==8.4.0` installed directly under:

```text
/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/lib/python3.10/site-packages/natsort
```

This removes the previous implicit dependency on borrowing `natsort` from whatever `/isaac-sim` site-packages happened to exist in the active image.

## Safety Gates Now In Code

- `submit_batch.py` defaults to dry-run.
- Real submission requires `--submit`.
- `launch_job.sh` real submission requires `DLC_SUBMIT=1`, `DLC_DRY_RUN=0`, explicit `DLC_WORKSPACE_ID`, explicit `DLC_RESOURCE_ID`, and a per-job `DLC_REAL_SUBMIT_CONFIRM`.
- `submit_gemma4_reannotate.sh` only accepts the exact `annotation_runs/<run_id>/output` output shape.
- `submit_gemma4_reannotate.sh` defaults `DLC_IMAGE` to the Genesis-LLM successful QLoRA image.
- Gemma4 reannotation rejects protected `EXTRA_MAIN_ARGS` overrides for input, output, asset list, chunking, and model selection.
- `python_runtime.sh` rejects `MODEL_BACKEND=local_gemma4_multimodal` without a non-empty `MODEL_PATH`.
- `python_runtime.sh` preflights `natsort` before Gemma4 model loading, so a missing borrowed dependency fails with an actionable runtime error.

## First Submitted Probe Record

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

## Replacement Probe Record

Replacement probe asset:

```text
basket/6c68230d67112b1dfd2bd7fa9322c756
```

Replacement probe run paths:

```text
RUN_ID=20260515T005924Z_gemma4_probe_v2
RUN_ROOT=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T005924Z_gemma4_probe_v2
ASSET_LIST_FILE=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T005924Z_gemma4_probe_v2/input/one_asset.txt
OUTPUT_DIR=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T005924Z_gemma4_probe_v2/output
```

Submission command used after fixing the `src` layout import path:

```bash
DLC_WORKSPACE_ID=270969 \
DLC_RESOURCE_ID=quota1r947pmazvk \
RUN_ID=20260515T005924Z_gemma4_probe_v2 \
ASSET_LIST_FILE=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T005924Z_gemma4_probe_v2/input/one_asset.txt \
TOTAL=1 NAME=gemma4_grscenes_probe_v2 \
bash scripts/dlc/submit_gemma4_reannotate.sh --submit
```

Observed DLC state after submission:

```text
Job ID: dlc14l1zbec0ofk2
Status: EnvPreparing
ReasonCode: JobPreparing
ReasonMessage: PyTorchJob dlc14l1zbec0ofk2 has been successfully scheduled and is now entering the preparation phase.
GmtCreateTime: 2026-05-15T01:00:05Z
GmtSubmittedTime: 2026-05-15T01:00:10Z
PodId: dlc14l1zbec0ofk2-master-0
Pod status: Pending
```

Final observed DLC state:

```text
Status: Failed
ReasonCode: JobFailed
GmtFailedTime: 2026-05-15T01:04:20Z
PodId: dlc14l1zbec0ofk2-master-0
Pod status: Failed
```

Pod log:

```text
Initializing Model Engine with model: /cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8
Failed to load model: No module named 'natsort'
```

Root cause:

```text
The Gemma4 conda env could import natsort on the submit host only because the host Python path exposed /isaac-sim/kit/python/lib/python3.10/site-packages.
The DLC worker used the USD/Isaac image path where that borrowed package was not present for this model load.
The Gemma4 path should use the Genesis-LLM successful image and should not depend on borrowed image-local Python packages.
```

Fix:

```text
scripts/dlc/submit_gemma4_reannotate.sh now defaults DLC_IMAGE to pj4090acr-registry-vpc.cn-beijing.cr.aliyuncs.com/pj4090/mahaoxiang:genmanip-mahaoxiang.
scripts/dlc/python_runtime.sh now preflights natsort for local_gemma4_multimodal before model loading.
natsort==8.4.0 was copied into /cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/lib/python3.10/site-packages.
```

The output directory check found no files:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T005924Z_gemma4_probe_v2/output
```

Replacement probe logs are under:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T005924Z_gemma4_probe_v2/logs
```

Monitor with:

```bash
./dlc get job dlc14l1zbec0ofk2
find /cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T005924Z_gemma4_probe_v2/output -maxdepth 4 -type f -print
```

Do not resubmit with this exact job name. Use a new `RUN_ID` and `NAME`.

## Third Submitted Probe Record

Probe asset:

```text
basket/6c68230d67112b1dfd2bd7fa9322c756
```

Probe run paths:

```text
RUN_ID=20260515T012454Z_gemma4_probe_v3
RUN_ROOT=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T012454Z_gemma4_probe_v3
ASSET_LIST_FILE=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T012454Z_gemma4_probe_v3/input/one_asset.txt
OUTPUT_DIR=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T012454Z_gemma4_probe_v3/output
```

Submission command used after switching to the Genesis-LLM image and making `natsort` worker-visible in the conda env:

```bash
DLC_WORKSPACE_ID=270969 \
DLC_RESOURCE_ID=quota1r947pmazvk \
RUN_ID=20260515T012454Z_gemma4_probe_v3 \
ASSET_LIST_FILE=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T012454Z_gemma4_probe_v3/input/one_asset.txt \
TOTAL=1 NAME=gemma4_grscenes_probe_v3 \
bash scripts/dlc/submit_gemma4_reannotate.sh --submit
```

Observed DLC state after submission:

```text
Job ID: dlc10pg3d6j8izbv
Status: EnvPreparing
GmtCreateTime: 2026-05-15T01:25:27Z
GmtSubmittedTime: 2026-05-15T01:25:32Z
```

Final observed DLC state:

```text
Status: Succeeded
ReasonCode: JobSucceeded
ReasonMessage: PyTorchJob dlc10pg3d6j8izbv is successfully completed.
GmtRunningTime: 2026-05-15T01:37:39Z
GmtSuccessedTime: 2026-05-15T01:38:56Z
PodId: dlc10pg3d6j8izbv-master-0
Pod status: Succeeded
```

Pod log evidence:

```text
[INFO] Gemma4 multimodal model loaded successfully.
[INFO] Loaded 1 assets from list.
[INFO] Processing asset: 6c68230d67112b1dfd2bd7fa9322c756
[INFO] Finished 6c68230d67112b1dfd2bd7fa9322c756 in 19.48s
Processing complete.
```

The output directory contains exactly one annotation JSON:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T012454Z_gemma4_probe_v3/output/basket/6c68230d67112b1dfd2bd7fa9322c756_annotation.json
```

JSON validation:

```text
valid_json=true
asset=basket/6c68230d67112b1dfd2bd7fa9322c756
fields=category,description,dimensions,mass,material,placement
category=basket
dimensions=0.4 * 0.3 * 0.2
mass=1.5
placement=OnFloor
```

Output content summary:

```text
description=This is a woven basket with a natural, light brown color and a textured surface created by the interwoven strands. It features a sturdy handle attached to the rim, suggesting it is designed for carrying or storage. The basket has a generally rounded or cylindrical shape, and its construction appears durable and rustic. The overall proportion suggests it is a medium-sized utility or decorative item.
material=Woven natural fibers (likely wicker or reed) for the entire body and handle.
```

Probe logs are under:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T012454Z_gemma4_probe_v3/logs
```

Monitor with:

```bash
./dlc get job dlc10pg3d6j8izbv
find /cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T012454Z_gemma4_probe_v3/output -maxdepth 4 -type f -print
```

This one-asset result was followed by a small multi-asset/multi-category probe before full submission.

## Multi-Category Probe Record

Probe run paths:

```text
RUN_ID=20260515T015019Z_gemma4_multicat_probe_v1
RUN_ROOT=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T015019Z_gemma4_multicat_probe_v1
ASSET_LIST_FILE=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T015019Z_gemma4_multicat_probe_v1/input/multicat_8_assets.txt
OUTPUT_DIR=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T015019Z_gemma4_multicat_probe_v1/output
```

Probe asset list:

```text
backpack/3f99b44a34f7c6c935c508293a194502
basket/040600389fdab577a5376c28e6c5eb15
bath_tub/0a667a5f263ae01bdd94754668b7293a
bed/00ca2676bbed26d6a39a968d99d61176
bicycle/c251052c5cce6a2d5a18e465b5b1d6c2
blanket/005c2a0c4ca7d5d0daa8c6b84b810400
book/00017b8cdf1dfbf33ca0579bd36c74da
book_shelf/08fb65f0d846ef2e5b292a396564da58
```

Submission command used:

```bash
DLC_WORKSPACE_ID=270969 \
DLC_RESOURCE_ID=quota1r947pmazvk \
RUN_ID=20260515T015019Z_gemma4_multicat_probe_v1 \
ASSET_LIST_FILE=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T015019Z_gemma4_multicat_probe_v1/input/multicat_8_assets.txt \
TOTAL=1 NAME=gemma4_grscenes_multicat_probe_v1 \
bash scripts/dlc/submit_gemma4_reannotate.sh --submit
```

Final observed DLC state:

```text
Job ID: dlc173f6kqzyiovg
Job name: gemma4_grscenes_multicat_probe_v1_0_1
Status: Succeeded
GmtSuccessedTime: 2026-05-15T01:53:20Z
```

JSON validation:

```text
json_files=8
failures=0
fields=category,description,dimensions,mass,material,placement
```

Outputs:

```text
output/backpack/3f99b44a34f7c6c935c508293a194502_annotation.json
output/basket/040600389fdab577a5376c28e6c5eb15_annotation.json
output/bath_tub/0a667a5f263ae01bdd94754668b7293a_annotation.json
output/bed/00ca2676bbed26d6a39a968d99d61176_annotation.json
output/bicycle/c251052c5cce6a2d5a18e465b5b1d6c2_annotation.json
output/blanket/005c2a0c4ca7d5d0daa8c6b84b810400_annotation.json
output/book/00017b8cdf1dfbf33ca0579bd36c74da_annotation.json
output/book_shelf/08fb65f0d846ef2e5b292a396564da58_annotation.json
```

Schema/runtime gate result: pass. A later semantic QA pass should still sample placement and material quality before merging outputs into any downstream consumer, because this probe only validated runtime behavior and JSON shape.

## Full Run Submission Record

Full run paths:

```text
RUN_ID=20260515T015209Z_gemma4_full_v1
RUN_ROOT=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T015209Z_gemma4_full_v1
ASSET_LIST_FILE=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T015209Z_gemma4_full_v1/input/all_assets.txt
OUTPUT_DIR=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T015209Z_gemma4_full_v1/output
```

Full asset list facts:

```text
assets=53167
chunks=64
job_name_pattern=gemma4_grscenes_full_v1_<chunk>_64
average_assets_per_chunk=about 831
```

Dry-run result:

```text
Total chunks: 64
Successful chunks (64): [0, 1, ..., 63]
Failed chunks (0): []
Mode: dry-run
DRY RUN complete: no jobs were submitted
```

Real submission command:

```bash
DLC_WORKSPACE_ID=270969 DLC_RESOURCE_ID=quota1r947pmazvk \
  RUN_ID=20260515T015209Z_gemma4_full_v1 \
  ASSET_LIST_FILE=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T015209Z_gemma4_full_v1/input/all_assets.txt \
  TOTAL=64 NAME=gemma4_grscenes_full_v1 \
  bash scripts/dlc/submit_gemma4_reannotate.sh --submit \
  | tee /cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T015209Z_gemma4_full_v1/logs/submit.log
```

Real submission result:

```text
Total chunks: 64
Successful chunks (64): [0, 1, ..., 63]
Failed chunks (0): []
All chunks submitted successfully.
```

Tracking files generated from the submission:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T015209Z_gemma4_full_v1/logs/submit.log
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T015209Z_gemma4_full_v1/logs/job_ids.tsv
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T015209Z_gemma4_full_v1/logs/status_latest.tsv
```

Initial post-submit status snapshot:

```text
rows=64
Running=4
Queuing=60
Failed=0
```

Representative job IDs:

```text
chunk 0:  dlcmkamtmud866n9  gemma4_grscenes_full_v1_0_64
chunk 1:  dlcos7dvuwf27h8k  gemma4_grscenes_full_v1_1_64
chunk 2:  dlcqg4y6iuaduzdk  gemma4_grscenes_full_v1_2_64
chunk 3:  dlcs42ih6pnnkvjo  gemma4_grscenes_full_v1_3_64
chunk 60: dlciyhbey41mdpyk  gemma4_grscenes_full_v1_60_64
chunk 61: dlckcfabu3rgllt3  gemma4_grscenes_full_v1_61_64
chunk 62: dlcmacg0aw4n8rvq  gemma4_grscenes_full_v1_62_64
chunk 63: dlcn4b85m5olp3tk  gemma4_grscenes_full_v1_63_64
```

The full job writes only under this isolated output root:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T015209Z_gemma4_full_v1/output
```

It does not write to the old Qwen output locations:

```text
./output
./output_reannotate
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets
```

## Reference Probe Commands

Create a one-asset probe list:

```bash
RUN_ID=$(date -u +%Y%m%dT%H%M%SZ)_gemma4_probe_v3
RUN_ROOT=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/$RUN_ID
mkdir -p "$RUN_ROOT/input" "$RUN_ROOT/output" "$RUN_ROOT/logs" "$RUN_ROOT/cache"
printf '%s\n' 'basket/6c68230d67112b1dfd2bd7fa9322c756' > "$RUN_ROOT/input/one_asset.txt"
```

Dry-run that probe:

```bash
RUN_ID=$RUN_ID \
ASSET_LIST_FILE="$RUN_ROOT/input/one_asset.txt" \
TOTAL=1 NAME=gemma4_grscenes_probe_v3 \
bash scripts/dlc/submit_gemma4_reannotate.sh --dry-run
```

Run the real one-asset DLC probe only after reviewing the dry-run:

```bash
DLC_WORKSPACE_ID=270969 \
DLC_RESOURCE_ID=quota1r947pmazvk \
RUN_ID=$RUN_ID \
ASSET_LIST_FILE="$RUN_ROOT/input/one_asset.txt" \
TOTAL=1 NAME=gemma4_grscenes_probe_v3 \
bash scripts/dlc/submit_gemma4_reannotate.sh --submit
```

## Reference Full Run Shape

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

- DLC script tests: `46` passed.
- Model backend tests: `28` passed, `1` skipped.
- Markdown fence check and `git diff --check` passed before commit `8b58a75`.
- Dry-run output showed `annotation_runs/<run_id>/output`, `DLC_WORKER_SETUP_SCRIPT`, `AUTO_ASSET_VENV`, `MODEL_BACKEND=local_gemma4_multimodal`, `MODEL_PATH`, and `UNSLOTH_COMPILE_LOCATION`.
- Protected `EXTRA_MAIN_ARGS='--output_dir ./output'` failed before launcher execution.
- First failed probe diagnosis captured `pod_master_logs_failed_investigation.txt`, `pod_master_events_failed_investigation.txt`, and local reproduction of the import failure.
- Second failed probe diagnosis captured `pod_master_logs_failed.txt` with the `No module named 'natsort'` model-load error and local verification that `natsort` now resolves from the managed conda env itself.
