# DLC Gemma4 Worker Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make DLC workers run Auto-Asset Gemma4 jobs with the Genesis-LLM proven setup-script plus Python-env pattern, while keeping all new reannotation output isolated.

**Architecture:** Preserve the current DLC chain and add explicit runtime env forwarding at the launcher boundary. Source worker setup in `run_task.sh`, select `AUTO_ASSET_VENV` in `python_runtime.sh`, and document the safe Gemma4 probe/full-run command shape.

**Tech Stack:** Bash DLC wrappers, Python `unittest`, existing Auto-Asset CLI.

---

### Task 1: Runtime Env Forwarding Tests

**Files:**
- Modify: `tests/test_dlc_scripts.py`

- [x] Add a failing test that `launch_job.sh` embeds `DLC_WORKER_SETUP_SCRIPT`, `AUTO_ASSET_VENV`, `UNSLOTH_COMPILE_LOCATION`, `MODEL_BACKEND`, and `MODEL_PATH` into the final worker command.
- [x] Add a failing test that `run_task.sh` sources `DLC_WORKER_SETUP_SCRIPT` before invoking `DLC_PYTHON_RUNTIME`.
- [x] Add a failing test that `python_runtime.sh` uses `AUTO_ASSET_VENV/bin/python` even when `.venv_dlc` is absent.
- [x] Run `PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_dlc_scripts -v` and confirm the new tests fail for the expected missing behavior.

### Task 2: Minimal Runtime Implementation

**Files:**
- Modify: `scripts/dlc/launch_job.sh`
- Modify: `scripts/dlc/run_task.sh`
- Modify: `scripts/dlc/python_runtime.sh`

- [x] In `launch_job.sh`, build the worker command from env assignments plus `bash run_task.sh ...`.
- [x] In `run_task.sh`, source `DLC_WORKER_SETUP_SCRIPT` if set and fail early if the script is missing.
- [x] In `python_runtime.sh`, prefer `AUTO_ASSET_VENV` and validate its `bin/python`.
- [x] Run `PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_dlc_scripts -v` and confirm the DLC script tests pass.

### Task 3: Operator Docs And Validation Commands

**Files:**
- Modify: `docs/dlc/README.md`
- Modify: `docs/dlc/TESTING.md`
- Modify: `docs/usage/gemma4_local_smoke.md`

- [x] Replace “Gemma4 DLC not operationally wired” wording with the new setup-script and `AUTO_ASSET_VENV` mechanism.
- [x] Add dry-run and mock-submit commands for isolated Gemma4 probe output.
- [x] State that full reannotation output must go under `annotation_runs/.../output`.
- [x] Run `git diff --check` and the DLC unit tests.

### Task 4: Review And Readiness

**Files:**
- No direct file edits unless review finds issues.

- [x] Request multi-agent review of the DLC runtime wiring and operator commands.
- [x] Apply technically valid feedback.
- [x] Run fresh verification: DLC unit tests, model backend unit tests, markdown fence check, `git status --short`.
- [x] Commit and push the implementation if all verification passes.
