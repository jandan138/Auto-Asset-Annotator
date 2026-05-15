# DLC Operator Runbook

This runbook covers the maintained DLC workflow for this repository:

```text
submit_*.sh -> submit_batch.py -> launch_job.sh -> run_task.sh -> python_runtime.sh -> python -m auto_asset_annotator.main
```

The primary batch contract is:

```text
run_task.sh <chunk_id> <chunk_total> [extra main.py flags...]
```

Use the wrapper scripts for routine operations. Use `submit_batch.py` directly only when you need a non-standard batch shape.

## Current Gemma4 Status

As of 2026-05-15, Gemma4 reannotation for the GRScenes test0 dataset has two real one-asset DLC probe failures diagnosed and a third one-asset probe submitted with the corrected Genesis-LLM image:

- `dlc1i6qia2inzfmv` failed before model loading because the remote runtime did not include `$CODE_ROOT/src` on `PYTHONPATH`.
- `dlc14l1zbec0ofk2` reached model initialization and failed with `Failed to load model: No module named 'natsort'`.

The second failure used the USD/Isaac image:

```text
Job ID:   dlc14l1zbec0ofk2
Job name: gemma4_grscenes_probe_v2_0_1
Status:   Failed
Run root: /cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T005924Z_gemma4_probe_v2
Image:    dsw-registry-vpc.cn-beijing.cr.aliyuncs.com/pai-training-algorithm/isaac-sim:isaacsim450-vnc-v8
Error:    Failed to load model: No module named 'natsort'
```

The Gemma4 wrapper now defaults to the Genesis-LLM successful QLoRA image and preflights `natsort` before model loading:

```text
pj4090acr-registry-vpc.cn-beijing.cr.aliyuncs.com/pj4090/mahaoxiang:genmanip-mahaoxiang
```

Current v3 probe:

```text
Job ID:   dlc10pg3d6j8izbv
Job name: gemma4_grscenes_probe_v3_0_1
Status:   EnvPreparing
Run root: /cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T012454Z_gemma4_probe_v3
```

The full real DLC run has not been submitted.

Current target:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets
```

Current preflight:

- `53,167` `category/asset_id` directories
- `0` assets missing `front.png`, `left.png`, `back.png`, or `right.png`
- old Qwen outputs remain in `./output` and `./output_reannotate`
- new Gemma4 output must go to `annotation_runs/<run_id>/output`

The concise status and next commands are in `docs/changes/2026-05-14_gemma4_dlc_reannotation_status.md`.

## Supported Workflows

- Full annotation batch: `bash scripts/dlc/submit_annotate.sh`
- Retry assets from `archive/temp_lists/failed_assets.txt`: `bash scripts/dlc/submit_retry_failed.sh`
- Retry incomplete physical-property results: `bash scripts/dlc/submit_retry_incomplete.sh`
- Submit an explicit asset list: `bash scripts/dlc/submit_asset_list.sh --asset_list_file <path>`
- Submit a tiny real/probe job: `MODEL_BACKEND=<backend> ASSET_LIST_FILE=<small-list> bash scripts/dlc/submit_probe.sh`
- Submit an isolated Gemma4 reannotation run: `ASSET_LIST_FILE=<list> bash scripts/dlc/submit_gemma4_reannotate.sh`
- Raw batch submission for custom `main.py` flags: `python scripts/dlc/submit_batch.py ... --command_args "..."`

Direct `run_task.sh` named modes (`annotate`, `classify`, `extract`, `custom`) still exist for debugging, but chunk mode is the maintained DLC operator path.

## Preflight Checklist

- Confirm the DLC CLI is available before real submission: `./dlc get jobs`
- Confirm the repository path mounted in DLC matches `DLC_CODE_ROOT`
- Confirm `.venv_dlc` or `.venv` exists under `DLC_CODE_ROOT` for normal `local_hf` / API runs
- Confirm `INPUT_DIR` and `OUTPUT_DIR` point to DLC-accessible paths if you override them
- Confirm the selected backend is intentional:
  `local_hf`: local model path or config-backed model must exist in the worker image
  `local_gemma4_multimodal`: `MODEL_PATH` is required, must point to a DLC-visible Gemma4 release path, and dry-run output must show both `--model_backend local_gemma4_multimodal` and `--model_path ...`
  `openai_compatible`: both `--api_base_url` and `--api_key_env` must resolve, and the named key must be non-empty in the runtime environment
- Run a dry-run wrapper command before real submission
- For Gemma4, confirm the worker runtime is equivalent to the Genesis-LLM QLoRA env: Transformers must expose Gemma4 multimodal classes and Unsloth must be available for 4-bit checkpoints. A runtime with `transformers 5.2.0` is not enough even if it can import `AutoProcessor`.
- Gemma4 DLC status: the launcher now embeds explicit worker runtime variables into the submitted command. Dry-run output must show `DLC_WORKER_SETUP_SCRIPT`, `AUTO_ASSET_VENV`, `MODEL_BACKEND=local_gemma4_multimodal`, `MODEL_PATH=...`, and `UNSLOTH_COMPILE_LOCATION=...` before any real probe.
- For Gemma4, set `UNSLOTH_COMPILE_LOCATION` to a job-local output/cache path if possible, so Unsloth does not write `unsloth_compiled_cache/` into the code root.
- For Gemma4, dry-run output should show the Genesis-LLM successful image unless there is an intentional override:
  `pj4090acr-registry-vpc.cn-beijing.cr.aliyuncs.com/pj4090/mahaoxiang:genmanip-mahaoxiang`.
- For Gemma4, `AUTO_ASSET_VENV` must be able to import `natsort` directly. The managed env currently has `natsort==8.4.0` installed under `/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/lib/python3.10/site-packages/natsort`.

## Submission Methods

Preferred entrypoints:

```bash
bash scripts/dlc/submit_annotate.sh --dry-run
bash scripts/dlc/submit_retry_failed.sh --dry-run
bash scripts/dlc/submit_retry_incomplete.sh --dry-run
bash scripts/dlc/submit_asset_list.sh --dry-run --asset_list_file archive/temp_lists/failed_assets.txt
```

All wrapper submissions default to dry-run. A real submission requires both:

- passing `--submit` to the wrapper or `submit_batch.py`
- setting explicit `DLC_WORKSPACE_ID` and `DLC_RESOURCE_ID`

This means an accidental missing `--dry-run` no longer submits a job. The launcher still prints the resolved DLC command in dry-run mode. `submit_batch.py --submit` also injects a per-job confirmation value for `launch_job.sh`; direct `launch_job.sh` real submissions require `DLC_SUBMIT=1`, `DLC_DRY_RUN=0`, explicit workspace/resource IDs, and `DLC_REAL_SUBMIT_CONFIRM=<task>_<chunk>_<total>`.

Useful wrapper overrides:

```bash
TOTAL=8 INPUT_DIR=/data/assets OUTPUT_DIR=/data/results bash scripts/dlc/submit_annotate.sh --dry-run
NAME=retry_failed_hotfix bash scripts/dlc/submit_retry_failed.sh --dry-run
ASSET_LIST_FILE=archive/temp_lists/custom_assets.txt bash scripts/dlc/submit_asset_list.sh --dry-run
EXTRA_MAIN_ARGS="--prompt_type classify_object_category_prompt" bash scripts/dlc/submit_annotate.sh --dry-run
```

Worker runtime selection:

```bash
DLC_WORKER_SETUP_SCRIPT=/cpfs/user/zhuzihou/conda-managed/bin/use-gcc-toolchain-hf-offline.sh \
AUTO_ASSET_VENV=/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310 \
MODEL_BACKEND=local_gemma4_multimodal \
MODEL_PATH=/cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8 \
bash scripts/dlc/run_task.sh 0 1 \
  --input_dir /data/assets \
  --asset_list_file archive/temp_lists/test_assets_dlc.txt \
  --output_dir /data/results
```

This is the supported worker-runtime mechanism for overriding `.venv_dlc`. `launch_job.sh` forwards only an allowlist of runtime variables into the remote worker command, including `DLC_WORKER_SETUP_SCRIPT`, `AUTO_ASSET_VENV`, `DLC_PYTHON_RUNTIME`, `UNSLOTH_COMPILE_LOCATION`, `MODEL_BACKEND`, `MODEL_PATH`, `API_BASE_URL`, and `API_KEY_ENV`.

## Gemma4 GRScenes Reannotation

Use `submit_gemma4_reannotate.sh` for the GRScenes test0 reannotation path. It defaults to the verified Gemma4 release, Genesis-LLM QLoRA Python environment, worker setup script, offline Hugging Face mode, and isolated output under:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/<run_id>/output
```

It also defaults to the Genesis-LLM successful QLoRA image:

```text
pj4090acr-registry-vpc.cn-beijing.cr.aliyuncs.com/pj4090/mahaoxiang:genmanip-mahaoxiang
```

Reference image split:

| Project | Successful image | Use here |
|---------|------------------|----------|
| `/cpfs/user/zhuzihou/dev/genesis-llm` | `pj4090acr-registry-vpc.cn-beijing.cr.aliyuncs.com/pj4090/mahaoxiang:genmanip-mahaoxiang` | Gemma4 / QLoRA / Unsloth inference |
| `/cpfs/shared/simulation/zhuzihou/dev/usd-scene-physics-prep` | `dsw-registry-vpc.cn-beijing.cr.aliyuncs.com/pai-training-algorithm/isaac-sim:isaacsim450-vnc-v8` | Isaac Sim / USD / physics preprocessing |

It refuses unsafe output directories such as `./output`, `./output_reannotate`, and the source `dataset/GRScenes_assets` tree.
It also requires the exact output shape `/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/<run_id>/output`.

For this wrapper, do not put protected routing/model/chunk flags in `EXTRA_MAIN_ARGS`. The script rejects `--input_dir`, `--output_dir`, `--asset_list_file`, `--num_chunks`, `--chunk_index`, `--model_backend`, and `--model_path` there, because those fields are owned by the wrapper and must not be overridden after the safe values are generated.

Create a full asset list outside the repo:

```bash
DATA_ROOT=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets
RUN_ID=$(date -u +%Y%m%dT%H%M%SZ)_gemma4_full_v1
RUN_ROOT=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/$RUN_ID
mkdir -p "$RUN_ROOT/input" "$RUN_ROOT/output" "$RUN_ROOT/logs" "$RUN_ROOT/cache"
find "$DATA_ROOT" -mindepth 2 -maxdepth 2 -type d -printf '%P\n' | LC_ALL=C sort > "$RUN_ROOT/input/all_assets.txt"
wc -l "$RUN_ROOT/input/all_assets.txt"
head "$RUN_ROOT/input/all_assets.txt"
tail "$RUN_ROOT/input/all_assets.txt"
```

Dry-run one explicit probe asset first. Use a unique `RUN_ID` and `NAME` for each real submission so job names and output paths stay traceable:

```bash
RUN_ID=$(date -u +%Y%m%dT%H%M%SZ)_gemma4_probe_v3 \
ASSET_LIST_FILE=/path/to/one_asset.txt \
TOTAL=1 NAME=gemma4_grscenes_probe_v3 \
bash scripts/dlc/submit_gemma4_reannotate.sh --dry-run
```

Then run a one-asset real DLC probe only after reviewing the dry-run:

```bash
DLC_WORKSPACE_ID=270969 \
DLC_RESOURCE_ID=quota1r947pmazvk \
RUN_ID=$RUN_ID \
ASSET_LIST_FILE=/path/to/one_asset.txt \
TOTAL=1 NAME=gemma4_grscenes_probe_v3 \
bash scripts/dlc/submit_gemma4_reannotate.sh --submit
```

Dry-run the full reannotation shape:

```bash
RUN_ID=$RUN_ID \
ASSET_LIST_FILE="$RUN_ROOT/input/all_assets.txt" \
TOTAL=64 NAME=gemma4_grscenes_full_v1 \
bash scripts/dlc/submit_gemma4_reannotate.sh --dry-run
```

After a tiny real probe writes valid JSON, submit the full run by adding `--submit` and explicit DLC IDs:

```bash
DLC_WORKSPACE_ID=270969 \
DLC_RESOURCE_ID=quota1r947pmazvk \
RUN_ID=$RUN_ID \
ASSET_LIST_FILE="$RUN_ROOT/input/all_assets.txt" \
TOTAL=64 NAME=gemma4_grscenes_full_v1 \
bash scripts/dlc/submit_gemma4_reannotate.sh --submit
```

When you need raw control, `submit_batch.py` accepts extra `main.py` flags through `--command_args`. Those flags are appended after the chunk pair and do not change `run_task.sh` mode.

```bash
python scripts/dlc/submit_batch.py --total 4 --name classify_assets \
    --command_args "--input_dir /data/assets --output_dir /data/results --prompt_type classify_object_category_prompt" \
    --dry-run
```

## Resource Profiles

`launch_job.sh` resolves one of three repository-specific profiles through `DLC_PROFILE`:

- `api_light`: remote multimodal API usage, smaller CPU and memory footprint
- `local_hf_default`: default local VLM inference profile
- `local_hf_heavy`: larger local profile for heavier local runs

These semantic profiles are now backed by canonical GPU-count templates and the newer smartbot sub-quota split:

- `1/2/4 GPU` -> `quota1r947pmazvk`
- `8 GPU` -> `quotaksvqq2oh2pg`

Current profile defaults:

- `api_light` -> `1 GPU` template
- `local_hf_default` -> `1 GPU` template
- `local_hf_heavy` -> `4 GPU` template

The launcher prints a resolved config summary before submission. You can still override individual resolved values with `DLC_GPU_COUNT`, `DLC_WORKER_GPU`, `DLC_WORKER_CPU`, `DLC_WORKER_MEMORY`, `DLC_WORKER_SHARED_MEMORY`, and `DLC_RESOURCE_ID`.

## Probe Workflow

Use `submit_probe.sh` for the smallest safe real-submit path.

The probe wrapper keeps `TOTAL=1` by default, but more importantly it requires an explicit `ASSET_LIST_FILE` so the probe scope stays tiny and operator-controlled.

It also requires an explicit `MODEL_BACKEND`, so the probe cannot silently fall back to the repository's checked-in default backend.

Examples:

```bash
# API-backed probe (dry-run first)
DLC_PROFILE=api_light TOTAL=1 NAME=api_probe \
ASSET_LIST_FILE=archive/temp_lists/test_assets_dlc.txt \
MODEL_BACKEND=openai_compatible MODEL_PATH=gemini-2.5-flash-image \
API_BASE_URL=http://your-host API_KEY_ENV=NEWAPI_API_KEY \
bash scripts/dlc/submit_probe.sh --dry-run

# Local-HF probe (dry-run first)
DLC_PROFILE=local_hf_default TOTAL=1 NAME=local_probe \
ASSET_LIST_FILE=archive/temp_lists/test_assets_dlc.txt \
MODEL_BACKEND=local_hf MODEL_PATH=/path/to/local/model \
bash scripts/dlc/submit_probe.sh --dry-run

# Gemma4 local multimodal probe (dry-run first)
DLC_PROFILE=local_hf_default TOTAL=1 NAME=gemma4_probe \
ASSET_LIST_FILE=archive/temp_lists/test_assets_dlc.txt \
MODEL_BACKEND=local_gemma4_multimodal \
MODEL_PATH=/cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8 \
bash scripts/dlc/submit_probe.sh --dry-run
```

The real submission path is the same command with `--submit` plus explicit `DLC_WORKSPACE_ID` and `DLC_RESOURCE_ID`.

## Monitoring And Logs

- List jobs: `./dlc get jobs`
- Inspect a job: `./dlc get job <job_id>`
- Stream logs: `./dlc logs <job_id>`

Watch for these signals in launcher output and worker logs:

- Resolved profile, CPU, GPU, memory, and resource quota
- The final `run_task.sh` command shape
- `python_runtime.sh` preflight failures before model startup
- `auto_asset_annotator.main` progress through chunk processing

## Post-Run Validation

- Confirm expected output JSON files were written under `OUTPUT_DIR`
- Sample output files to verify parsed fields instead of `raw_output`
- If the run was a retry workflow, verify the expected source list was consumed
- For chunked runs, spot-check that multiple chunks produced disjoint outputs
- Record the submission command, job ID, profile, input path, and output path

## Recovery And Rerun

- Parse failures or previously failed assets: `bash scripts/dlc/submit_retry_failed.sh`
- Incomplete physical-property fields: `bash scripts/dlc/submit_retry_incomplete.sh`
- Explicit operator-curated subset: `bash scripts/dlc/submit_asset_list.sh --asset_list_file <path>`

Use `--dry-run` first on every rerun. Only fall back to raw `submit_batch.py` when the maintained wrappers do not cover the batch you need.

## Backend Notes

`local_hf`, `local_gemma4_multimodal`, and `openai_compatible` use the same chunk submission chain but have different runtime requirements.

`local_hf`:
- Requires a valid model path or config-backed model name in the worker environment
- Uses local GPU memory and the `local_hf_default` or `local_hf_heavy` profile in most cases

`local_gemma4_multimodal`:
- Requires explicit `MODEL_PATH`; the probe wrapper rejects missing Gemma4 paths
- Requires a Gemma4-capable Transformers runtime and DLC visibility of `/cpfs/user/zhuzihou/models/gemma4/...`
- Requires Unsloth for `unsloth/*-bnb-4bit` or local 4-bit bitsandbytes Gemma4 checkpoints
- Uses local GPU memory and starts with the `local_hf_default` profile for tiny probes
- Dry-run output must include both `--model_backend local_gemma4_multimodal` and `--model_path <pinned-release-path>`
- For DLC jobs, dry-run output must also include the forwarded worker runtime variables described above
- Local single-asset smoke evidence and exact runtime commands are documented in `docs/usage/gemma4_local_smoke.md`

`openai_compatible`:
- Sends images to a remote chat-completions-compatible endpoint
- Requires an API base URL, an API key env var name, and a non-empty API key in the worker runtime
- Usually fits the `api_light` profile because inference happens remotely

For both backends, the wrapper and launcher logs should make the final runtime configuration explicit before a real job is submitted.
