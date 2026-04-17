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
MODEL_BACKEND=openai_compatible ASSET_LIST_FILE=archive/temp_lists/probe_assets.txt bash scripts/dlc/submit_probe.sh --dry-run
bash scripts/dlc/submit_retry_failed.sh --dry-run
bash scripts/dlc/submit_retry_incomplete.sh --dry-run
bash scripts/dlc/submit_asset_list.sh --dry-run --asset_list_file archive/temp_lists/failed_assets.txt

# Separate launch-layer probe when you need resolved profile / worker command evidence
# Use a fake DLC binary locally for this check. A real DLC binary will submit a real job.
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
ASSET_LIST_FILE=archive/temp_lists/probe_assets.txt \
INPUT_DIR=/data/test_assets OUTPUT_DIR=/data/test_results \
MODEL_BACKEND=openai_compatible MODEL_PATH=gemini-2.5-flash-image \
API_BASE_URL=http://your-host API_KEY_ENV=NEWAPI_API_KEY \
bash scripts/dlc/submit_probe.sh --dry-run

# Local-HF probe
DLC_PROFILE=local_hf_default TOTAL=1 NAME=local_probe \
ASSET_LIST_FILE=archive/temp_lists/probe_assets.txt \
INPUT_DIR=/data/test_assets OUTPUT_DIR=/data/test_results \
MODEL_BACKEND=local_hf MODEL_PATH=/path/to/local/model \
bash scripts/dlc/submit_probe.sh --dry-run
```

For a real probe, run the same command without `--dry-run`.
The explicit `ASSET_LIST_FILE` is what keeps the real probe tiny; `TOTAL=1` alone does not narrow a full input directory.

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

## Pass/Fail Gates

Pass the smoke stage only if all of the following are true:

- `tests.test_dlc_scripts` passes
- wrapper dry-runs exit `0`
- dry-run output shows one chunk pair only, with no duplicated chunk args
- the intended retry or asset-list flags appear in the resolved command
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
