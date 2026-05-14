# DLC Gemma4 Worker Runtime Design

## Goal

Enable Auto-Asset-Annotator DLC jobs to use the same proven worker-runtime pattern as Genesis-LLM: explicitly inject a worker setup script and a Gemma4-capable Python environment into the DLC command, then write new Gemma4 reannotation outputs to an isolated run directory.

## Background

Local Gemma4 single-asset smoke succeeds with:

```text
/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python
```

The repository `.venv_dlc` runtime is insufficient for Gemma4 multimodal image input. Genesis-LLM real DLC evidence shows the reliable remote-worker pattern is to embed worker-visible environment variables directly into the DLC `--command`, source a worker setup script on the worker, then force the Python executable from a known environment.

## Design

Use the existing Auto-Asset DLC chain:

```text
submit_*.sh -> submit_batch.py -> launch_job.sh -> run_task.sh -> python_runtime.sh -> python -m auto_asset_annotator.main
```

Add three narrow capabilities:

1. `launch_job.sh` forwards only explicit, allowlisted environment variables into the worker command. The critical variables are `DLC_WORKER_SETUP_SCRIPT`, `AUTO_ASSET_VENV`, `DLC_PYTHON_RUNTIME`, `UNSLOTH_COMPILE_LOCATION`, `MODEL_BACKEND`, `MODEL_PATH`, `API_BASE_URL`, and `API_KEY_ENV`.
2. `run_task.sh` sources `DLC_WORKER_SETUP_SCRIPT` before invoking `python_runtime.sh`, then restores strict shell guards. This lets the worker setup inject compiler paths, offline Hugging Face cache settings, and other runtime-only environment.
3. `python_runtime.sh` prefers `AUTO_ASSET_VENV/bin/python` when `AUTO_ASSET_VENV` is set, falling back to the existing `.venv_dlc` / `.venv` behavior for current Qwen/API jobs.

## Output Isolation

New Gemma4 full reannotation must not write to:

```text
./output
./output_reannotate
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets
```

Recommended full-run output root:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260514_gemma4_full_v1/output
```

Recommended probe output root:

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260514_gemma4_probe_v1/output
```

## Validation Gates

Proceed in this order:

1. Unit tests for env forwarding, setup sourcing, and `AUTO_ASSET_VENV` selection.
2. Local DLC dry-run showing worker command contains the explicit setup/runtime variables.
3. Mock submit with `DLC_BIN=/bin/echo` showing the final `dlc submit pytorchjob` command without creating a paid job.
4. Local `run_task.sh` smoke proving setup variables are visible to the runtime wrapper.
5. Real DLC smoke-env/probe only after the above evidence is recorded.

## Non-Goals

- Do not change annotation parser/schema in this step.
- Do not merge Auto-Asset output back into GRScenes original metadata.
- Do not overwrite existing Qwen outputs.
- Do not start full DLC reannotation before a tiny Gemma4 DLC probe has produced inspectable JSON in an isolated output root.
