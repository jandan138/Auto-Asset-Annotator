# DLC Smoke And Probe Guide

This guide defines the smallest safe checks for the maintained DLC workflow. It is intentionally lightweight: verify command construction first, then escalate only when the evidence says the path is healthy.

## Smoke Test Scope

A DLC smoke test should prove these things without launching a large run:

- wrapper `--dry-run` proves `submit_batch.py` command assembly for the maintained wrapper workflows
- direct `launch_job.sh` checks are still required when you need launch-layer evidence such as the resolved profile and final worker command
- `run_task.sh` preserves the chunk contract `run_task.sh <chunk_id> <chunk_total> [extra main.py flags...]`
- `python_runtime.sh` can locate the Python environment and import the package

Recommended local checks:

```bash
PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_dlc_scripts
bash scripts/dlc/submit_annotate.sh --dry-run
MODEL_BACKEND=openai_compatible ASSET_LIST_FILE=archive/temp_lists/test_assets_dlc.txt bash scripts/dlc/submit_probe.sh --dry-run
MODEL_BACKEND=local_gemma4_multimodal MODEL_PATH=/cpfs/user/zhuzihou/models/gemma4/current ASSET_LIST_FILE=archive/temp_lists/test_assets_dlc.txt bash scripts/dlc/submit_probe.sh --dry-run
ASSET_LIST_FILE=archive/temp_lists/test_assets_dlc.txt bash scripts/dlc/submit_gemma4_reannotate.sh --dry-run
bash scripts/dlc/submit_retry_failed.sh --dry-run
bash scripts/dlc/submit_retry_incomplete.sh --dry-run
bash scripts/dlc/submit_asset_list.sh --dry-run --asset_list_file archive/temp_lists/failed_assets.txt

# Separate launch-layer probe when you need resolved profile / worker command evidence
# This is still dry-run unless DLC_SUBMIT=1 and DLC_DRY_RUN=0 are both set.
DLC_BIN=/path/to/fake/dlc bash scripts/dlc/launch_job.sh annotate_assets 0 4
```

## Minimum Safe Test Size

- Prefer dry-run first for every wrapper and any raw `submit_batch.py` command
- For a real DLC probe, use `TOTAL=1`
- Use a tiny input set or an explicit `--asset_list_file` with a few known assets
- Do not start with a full local-HF batch or quota-consuming API batch unless a smaller probe has already passed

Example minimal probe commands:

```bash
# API-backed probe
DLC_PROFILE=api_light TOTAL=1 NAME=api_probe \
ASSET_LIST_FILE=archive/temp_lists/test_assets_dlc.txt \
INPUT_DIR=/data/test_assets OUTPUT_DIR=/data/test_results \
MODEL_BACKEND=openai_compatible MODEL_PATH=gemini-2.5-flash-image \
API_BASE_URL=http://your-host API_KEY_ENV=NEWAPI_API_KEY \
bash scripts/dlc/submit_probe.sh --dry-run

# Local-HF probe
DLC_PROFILE=local_hf_default TOTAL=1 NAME=local_probe \
ASSET_LIST_FILE=archive/temp_lists/test_assets_dlc.txt \
INPUT_DIR=/data/test_assets OUTPUT_DIR=/data/test_results \
MODEL_BACKEND=local_hf MODEL_PATH=/path/to/local/model \
bash scripts/dlc/submit_probe.sh --dry-run

# Gemma4 local multimodal probe
DLC_PROFILE=local_hf_default TOTAL=1 NAME=gemma4_probe \
ASSET_LIST_FILE=archive/temp_lists/test_assets_dlc.txt \
INPUT_DIR=/data/test_assets OUTPUT_DIR=/data/test_results \
MODEL_BACKEND=local_gemma4_multimodal \
MODEL_PATH=/cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8 \
bash scripts/dlc/submit_probe.sh --dry-run
```

For a real probe, run the same command with `--submit` plus explicit `DLC_WORKSPACE_ID` and `DLC_RESOURCE_ID`.
The explicit `ASSET_LIST_FILE` is what keeps the real probe tiny; `TOTAL=1` alone does not narrow a full input directory.

Gemma4-specific local smoke should be run before any real DLC Gemma4 probe. The current validated local runtime is:

```text
/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python
```

The checked `.venv_dlc` runtime is not enough for Gemma4 multimodal image input because its Transformers build does not produce Gemma4 image tensors. Follow `docs/usage/gemma4_local_smoke.md` for processor-only smoke, single-asset CLI smoke, Unsloth cache isolation, and output schema checks.

Runtime wiring status:

- Direct `run_task.sh` execution can override the default `.venv_dlc` / `.venv` selection with worker-side `AUTO_ASSET_VENV=/path/to/env` or `DLC_PYTHON_RUNTIME=/path/to/runtime_wrapper.sh`.
- `launch_job.sh` now encodes an allowlist of worker runtime variables into the submitted DLC command. For Gemma4, dry-run output must show `DLC_WORKER_SETUP_SCRIPT`, `AUTO_ASSET_VENV`, `MODEL_BACKEND=local_gemma4_multimodal`, `MODEL_PATH=...`, and `UNSLOTH_COMPILE_LOCATION=...`.
- `launch_job.sh` only submits when `DLC_SUBMIT=1`, `DLC_DRY_RUN=0`, explicit workspace/resource IDs are set, and `DLC_REAL_SUBMIT_CONFIRM` exactly matches the job name. `submit_batch.py --submit` sets that confirmation per chunk.
- `submit_gemma4_reannotate.sh` is the maintained GRScenes reannotation wrapper. It defaults to the verified Genesis-LLM QLoRA environment, requires the exact `annotation_runs/<run_id>/output` output shape, and refuses protected `EXTRA_MAIN_ARGS` overrides for input, output, asset list, chunking, and model selection.
- A real Gemma4 DLC probe should remain blocked until the dry-run command is reviewed. The first real probe should then capture worker logs showing the effective Python executable, Transformers version, Gemma4 image tensor keys, and `UNSLOTH_COMPILE_LOCATION`.

## Required Evidence

Capture these artifacts for every smoke or probe run:

- exact command used
- whether it was dry-run or real submission
- wrapper dry-run output when verifying submit-layer assembly
- resolved DLC profile from direct `launch_job.sh` output when verifying the launch layer
- final `run_task.sh` command payload from direct `launch_job.sh` output when verifying the launch layer
- job ID for real submissions
- a sample worker log excerpt showing runtime preflight and first processing steps
- a sample output JSON path if the run writes results
- for Gemma4 probes, the effective Python executable, Transformers version, whether image tensor keys were produced in processor smoke, and the `UNSLOTH_COMPILE_LOCATION` path

## Pass/Fail Gates

Pass the smoke stage only if all of the following are true:

- `tests.test_dlc_scripts` passes
- wrapper dry-runs exit `0`
- dry-run output shows one chunk pair only, with no duplicated chunk args
- the intended retry or asset-list flags appear in the resolved command
- Gemma4 dry-run output shows isolated `annotation_runs/.../output` and the forwarded worker runtime variables
- the final Gemma4 command contains exactly one effective `--output_dir`, and it is the wrapper-owned `annotation_runs/<run_id>/output`
- direct `launch_job.sh` output is used with a fake `DLC_BIN` whenever you need to verify resolved profile or final worker command details without submitting a real job

Fail the smoke stage if any of these happen:

- wrapper scripts require manual `--command_args` editing for a standard workflow
- `run_task.sh` is invoked with duplicated chunk args
- a launch-layer check is needed but the launcher profile or resource summary is missing or wrong
- runtime preflight fails to find the environment or import the package
- a real probe run produces only `raw_output` files or no output files at all

## Escalation To Larger Runs

Escalate only in this order:

1. Local unit tests and wrapper dry-runs
2. One-chunk DLC probe with a tiny asset set
3. Small multi-chunk run after the one-chunk probe produces correct logs and output
4. Full production submission after the small run confirms throughput and output quality

Do not skip directly from a broken or incomplete smoke test to a large DLC submission.

Full GRScenes reannotation must use a new output root under:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/<run_id>/output
```

Do not reuse the existing repository `output/` or `output_reannotate/` directories. Those contain earlier Qwen-small-model results and should remain available for comparison.
