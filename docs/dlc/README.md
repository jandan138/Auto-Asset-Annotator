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

## Supported Workflows

- Full annotation batch: `bash scripts/dlc/submit_annotate.sh`
- Retry assets from `archive/temp_lists/failed_assets.txt`: `bash scripts/dlc/submit_retry_failed.sh`
- Retry incomplete physical-property results: `bash scripts/dlc/submit_retry_incomplete.sh`
- Submit an explicit asset list: `bash scripts/dlc/submit_asset_list.sh --asset_list_file <path>`
- Submit a tiny real/probe job: `MODEL_BACKEND=<backend> ASSET_LIST_FILE=<small-list> bash scripts/dlc/submit_probe.sh`
- Raw batch submission for custom `main.py` flags: `python scripts/dlc/submit_batch.py ... --command_args "..."`

Direct `run_task.sh` named modes (`annotate`, `classify`, `extract`, `custom`) still exist for debugging, but chunk mode is the maintained DLC operator path.

## Preflight Checklist

- Confirm the DLC CLI is available: `./dlc get jobs`
- Confirm the repository path mounted in DLC matches `DLC_CODE_ROOT`
- Confirm `.venv_dlc` or `.venv` exists under `DLC_CODE_ROOT`
- Confirm `INPUT_DIR` and `OUTPUT_DIR` point to DLC-accessible paths if you override them
- Confirm the selected backend is intentional:
  `local_hf`: local model path or config-backed model must exist in the worker image
  `openai_compatible`: both `--api_base_url` and `--api_key_env` must resolve, and the named key must be non-empty in the runtime environment
- Run a dry-run wrapper command before real submission

## Submission Methods

Preferred entrypoints:

```bash
bash scripts/dlc/submit_annotate.sh --dry-run
bash scripts/dlc/submit_retry_failed.sh --dry-run
bash scripts/dlc/submit_retry_incomplete.sh --dry-run
bash scripts/dlc/submit_asset_list.sh --dry-run --asset_list_file archive/temp_lists/failed_assets.txt
```

Useful wrapper overrides:

```bash
TOTAL=8 INPUT_DIR=/data/assets OUTPUT_DIR=/data/results bash scripts/dlc/submit_annotate.sh --dry-run
NAME=retry_failed_hotfix bash scripts/dlc/submit_retry_failed.sh --dry-run
ASSET_LIST_FILE=archive/temp_lists/custom_assets.txt bash scripts/dlc/submit_asset_list.sh --dry-run
EXTRA_MAIN_ARGS="--prompt_type classify_object_category_prompt" bash scripts/dlc/submit_annotate.sh --dry-run
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
ASSET_LIST_FILE=archive/temp_lists/probe_assets.txt \
MODEL_BACKEND=openai_compatible MODEL_PATH=gemini-2.5-flash-image \
API_BASE_URL=http://your-host API_KEY_ENV=NEWAPI_API_KEY \
bash scripts/dlc/submit_probe.sh --dry-run

# Local-HF probe (dry-run first)
DLC_PROFILE=local_hf_default TOTAL=1 NAME=local_probe \
ASSET_LIST_FILE=archive/temp_lists/probe_assets.txt \
MODEL_BACKEND=local_hf MODEL_PATH=/path/to/local/model \
bash scripts/dlc/submit_probe.sh --dry-run
```

The real submission path is the same command without `--dry-run`.

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

`local_hf` and `openai_compatible` use the same chunk submission chain but have different runtime requirements.

`local_hf`:
- Requires a valid model path or config-backed model name in the worker environment
- Uses local GPU memory and the `local_hf_default` or `local_hf_heavy` profile in most cases

`openai_compatible`:
- Sends images to a remote chat-completions-compatible endpoint
- Requires an API base URL, an API key env var name, and a non-empty API key in the worker runtime
- Usually fits the `api_light` profile because inference happens remotely

For both backends, the wrapper and launcher logs should make the final runtime configuration explicit before a real job is submitted.
