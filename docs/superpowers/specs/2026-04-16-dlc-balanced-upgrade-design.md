# DLC Balanced Upgrade Design

## Summary

This design upgrades the repository's DLC workflow from a mostly working migrated script set into a maintained, annotation-focused operator workflow.

The upgrade is intentionally balanced:

- keep the current `submit_batch.py -> launch_job.sh -> run_task.sh -> python -m auto_asset_annotator.main` chain
- fix concrete correctness bugs in the current scripts
- borrow the best operational patterns from `usd-scene-physics-prep`
- avoid copying Isaac-Sim-specific runtime logic or unrelated task modes

## Context

The current repository already contains a DLC submission chain:

- `scripts/dlc/submit_batch.py`
- `scripts/dlc/launch_job.sh`
- `scripts/dlc/run_task.sh`
- `docs/dlc/README.md`
- `docs/dlc/TESTING.md`

However, review of the current scripts and comparison against the newer `usd-scene-physics-prep` DLC workflow identified three major problems:

1. The current submission chain has at least one real correctness bug.
   - `launch_job.sh` duplicates `chunk_id chunk_total` when constructing the container command.
   - That can break the default batch path by passing unexpected positional arguments into `main.py`.

2. The current DLC scripts are operationally thin.
   - There is no dedicated runtime wrapper.
   - There are no structured resource profiles.
   - `run_task.sh` mixes environment setup, dispatch, and runtime assumptions.

3. The current docs are script notes, not a full operator runbook.
   - They do not yet provide a clear preflight -> submit -> monitor -> validate -> recover workflow.

The newer `usd-scene-physics-prep` repository provides better DLC operational discipline, but it is an Isaac-Sim physics-prep project and should not be copied wholesale.

## Goals

1. Make the DLC submission chain correct and reliable for annotation workloads.
2. Preserve the repository's annotation-first task model.
3. Add a lightweight runtime wrapper that centralizes Python environment detection and preflight checks.
4. Add a small, explicit set of resource profiles instead of one hardcoded resource configuration.
5. Add a few stable submission wrappers for the most common operator workflows.
6. Upgrade `docs/dlc/*` into a current operator runbook.

## Non-Goals

- No Isaac-Sim runtime integration.
- No generic multi-domain task dispatcher like `usd-scene-physics-prep`.
- No category-loop or phase-based wrappers copied from unrelated pipelines.
- No real DLC job submission during implementation unless explicitly requested.
- No redesign of the annotation pipeline itself.

## Architecture Decision

### Chosen Approach

Implement a balanced DLC substrate for this repository with five layers:

1. batch submission layer
2. job launch layer
3. runtime wrapper layer
4. task dispatch layer
5. operator documentation layer

### Why This Approach

- It fixes the current broken/fragile parts without over-importing another project's complexity.
- It preserves the repository's current execution contract: `python -m auto_asset_annotator.main` remains the real worker entrypoint.
- It provides a clear seam for both `local_hf` and `openai_compatible` backends in DLC.

### Rejected Approaches

#### Minimal patch only

Rejected because it would leave the repository with weak operator ergonomics and fragile runtime behavior.

#### Full workflow transplant from `usd-scene-physics-prep`

Rejected because it would copy Isaac-Sim-specific structure and unrelated task modes into an annotation project.

## Findings To Design Around

### Current correctness bug

Current `launch_job.sh` sets:

```bash
COMMAND_ARGS=${5:-"$CHUNK_ID $CHUNK_TOTAL"}
```

and later submits:

```bash
--command="bash $CODE_ROOT/scripts/dlc/run_task.sh $CHUNK_ID $CHUNK_TOTAL ${COMMAND_ARGS}"
```

This duplicates the chunk pair in the default path.

### Current run-mode mismatch

`submit_batch.py --command_args` currently claims to override `run_task.sh` run mode, but the actual launcher always prefixes numeric chunk args first. That means many documented “override mode” cases are not truly supported.

### Current runtime ambiguity

`run_task.sh` exports `MODEL_PATH`, but `main.py` only changes models when configuration or CLI flags say so. This creates an operator trap where the shell environment appears to override the model but the worker does not actually consume it.

## Proposed File Structure

### Modify

- `scripts/dlc/submit_batch.py`
- `scripts/dlc/launch_job.sh`
- `scripts/dlc/run_task.sh`
- `docs/dlc/README.md`
- `docs/dlc/TESTING.md`
- `README.md`
- `CLAUDE.md`
- `docs/usage/cli_reference.md`

### Create

- `scripts/dlc/python_runtime.sh`
- `scripts/dlc/submit_annotate.sh`
- `scripts/dlc/submit_retry_failed.sh`
- `scripts/dlc/submit_retry_incomplete.sh`
- `scripts/dlc/submit_asset_list.sh`
- `docs/changes/2026-04-16_dlc_balanced_upgrade.md`

## Layer 1: Batch Submission Layer

### `scripts/dlc/submit_batch.py`

Keep the current Python batch submitter as the high-level loop.

Responsibilities after upgrade:

- validate chunk count
- optionally print a dry-run summary instead of submitting
- call `launch_job.sh` once per chunk
- pass data-source and additional main-program flags cleanly
- retry transient submission failures

### Design change

`--command_args` should be documented as extra `main.py` CLI flags appended after chunk arguments.

It should no longer claim to change `run_task.sh` mode.

Add:

- `--dry-run`

so operators can inspect the resolved calls before submitting real DLC jobs.

## Layer 2: Job Launch Layer

### `scripts/dlc/launch_job.sh`

This becomes the authoritative place for:

- resource-profile selection
- environment-variable overrides
- final `dlc submit pytorchjob` assembly

### Resource-profile design

Do not import the 1/2/4/8 GPU matrix from `usd-scene-physics-prep` directly.

Use three repository-specific profiles only:

- `api_light`
- `local_hf_default`
- `local_hf_heavy`

Each profile resolves:

- GPU count
- CPU count
- memory
- shared memory
- resource quota ID

Environment variables may still override any resolved value.

### Command construction rule

The launcher must use one unambiguous contract:

```text
run_task.sh <chunk_id> <chunk_total> [extra main.py flags...]
```

No duplicated chunk args.

### Logging rule

Before submission, print the fully resolved configuration:

- workspace ID
- resource ID
- image
- code root
- selected profile
- resolved CPU/GPU/memory settings
- final command payload

## Layer 3: Runtime Wrapper Layer

### `scripts/dlc/python_runtime.sh`

This new script provides a lightweight annotation-specific runtime wrapper.

It replaces the current pattern where `run_task.sh` is responsible for both environment setup and task dispatch.

Responsibilities:

- locate `.venv_dlc` or `.venv`
- fail clearly if neither exists
- export `PYTHONUNBUFFERED=1`
- export `PYTHONPATH=$CODE_ROOT`
- verify the Python interpreter exists
- verify the package imports
- run backend-specific preflight checks
- execute the final Python command

### Backend-specific preflight

For `openai_compatible` runs, verify:

- `--api_base_url` is present or resolved
- `--api_key_env` is present
- the referenced environment variable is non-empty

For `local_hf` runs, verify:

- the config or CLI resolves a model identifier/path

This preflight should improve DLC logs by failing before expensive work starts.

## Layer 4: Task Dispatch Layer

### `scripts/dlc/run_task.sh`

This script should stay annotation-focused.

Supported direct modes after upgrade:

- `annotate`
- `classify`
- `extract`
- `custom`
- default chunk mode: `<chunk_id> <chunk_total> [extra main.py args...]`

### Explicit rules

- no-argument invocation must exit non-zero
- default chunk mode remains the primary DLC path
- if environment-driven model override is supported, convert it into an explicit `--model_path` CLI flag
- if environment-driven backend/API overrides are supported, also convert them into explicit CLI flags

This keeps runtime behavior legible and avoids “exported but ignored” environment variables.

## Layer 5: Operator Documentation Layer

### `docs/dlc/README.md`

This should become the canonical operator runbook.

Required sections:

- current supported DLC workflows
- preflight checklist
- submission methods
- resource profiles
- monitoring and logs
- post-run validation
- recovery and rerun workflows
- backend-specific notes (`local_hf` vs `openai_compatible`)

### `docs/dlc/TESTING.md`

This should define a real smoke/probe standard.

Required sections:

- what a DLC smoke test covers
- minimum safe test scale
- required evidence to capture
- pass/fail criteria
- when to escalate to a larger run

### Historical docs separation

Keep the historical `docs/changes/*.md` files as records, but operators should not have to reconstruct today's workflow from them.

## Submission Wrapper Design

Add a small number of stable operator wrappers:

- `scripts/dlc/submit_annotate.sh`
- `scripts/dlc/submit_retry_failed.sh`
- `scripts/dlc/submit_retry_incomplete.sh`
- `scripts/dlc/submit_asset_list.sh`

Each wrapper should:

- use canonical argument patterns
- accept a run label/name override
- support `--dry-run`
- minimize hand-built `--command_args` usage by operators

These wrappers are intentionally few and repetitive because they encode the real high-frequency operations for this repository.

## What To Borrow From `usd-scene-physics-prep`

- resource-profile selection pattern
- runtime wrapper split pattern
- preflight checks with actionable logs
- operator/runbook discipline
- explicit operational decision documentation

## What Not To Borrow

- Isaac-Sim runtime logic
- broad multi-mode task dispatcher unrelated to annotation
- scene-prep-specific wrappers and phase naming
- Isaac-specific resource assumptions

## Validation Strategy

### Script-level verification

- dry-run submission output is correct and does not duplicate chunk args
- `run_task.sh` usage and chunk dispatch behave as documented
- wrapper scripts produce the expected canonical command shapes

### Runtime verification

- local wrapper finds the correct venv
- preflight fails clearly when API credentials are missing
- preflight fails clearly when config/runtime is inconsistent

### Documentation verification

- all operator examples match actual script behavior
- backend-specific notes are consistent with current `main.py` and API backend behavior

## Risks And Mitigations

### Risk 1: Over-generalizing the worker interface

Mitigation:

- keep task modes annotation-first
- do not add unrelated execution modes

### Risk 2: Hidden environment coupling remains

Mitigation:

- convert meaningful env overrides into explicit final CLI flags where possible
- centralize runtime setup in `python_runtime.sh`

### Risk 3: Docs lag behind new script semantics

Mitigation:

- update docs in the same implementation pass
- document the final supported workflows only

## Deliverable

This design should produce a DLC workflow that is:

- correct in its batch command construction
- easier to operate
- explicit about resource profiles and backend selection
- more diagnosable when jobs fail
- still specific to annotation rather than a generic cluster task runner

## Acceptance Criteria

This design is satisfied when:

- the default batch path no longer duplicates chunk arguments
- `submit_batch.py`, `launch_job.sh`, and `run_task.sh` implement one consistent argument contract
- the repository has a runtime wrapper that centralizes Python environment setup and preflight checks
- there are explicit DLC resource profiles suitable for annotation workloads
- there are stable wrapper scripts for the repository's common DLC operations
- `docs/dlc/*` reads as a current operator runbook rather than script notes
