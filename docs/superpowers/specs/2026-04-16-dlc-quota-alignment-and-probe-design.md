# DLC Quota Alignment And Probe Design

## Summary

This design is a second-round DLC upgrade for `Auto-Asset-Annotator`.

The first DLC upgrade established:

- a corrected submission contract
- a runtime wrapper
- stable wrapper scripts
- an operator runbook

This second round addresses the remaining operational gaps:

1. align resource templates and quota selection with the newer `usd-scene-physics-prep` DLC configuration
2. add fail-fast validation for risky submission/runtime states
3. add a standard probe workflow and recorded probe evidence path

## Context

Current `Auto-Asset-Annotator` DLC status is improved but still not fully aligned with the newer smartbot sub-quota model.

What remains outdated:

- `scripts/dlc/launch_job.sh` still uses the old resource quota `quotalplclkpgjgv`
- profile resource shapes do not match the canonical new less-gpu / more-gpu template envelopes
- wrapper-level input validation is still too permissive
- runtime preflight can be stricter for backend-specific requirements
- there is no canonical `submit_probe.sh` workflow or fresh probe record

Reference behavior from `usd-scene-physics-prep` shows the new intended DLC resource mapping:

- `1/2/4 GPU` -> `quota1r947pmazvk`
- `8 GPU` -> `quotaksvqq2oh2pg`

This reflects the less-gpu / more-gpu split.

## Goals

1. Replace the old resource quota usage with the newer less-gpu / more-gpu mapping.
2. Align CPU/memory templates with the newer GPU-count-based envelopes.
3. Preserve this repository’s annotation-first semantic profiles.
4. Add fail-fast validation for chunk arguments, asset-list wrappers, and backend-specific runtime needs.
5. Add a standard probe wrapper so operators can safely submit tiny validation jobs.
6. Record a maintained probe workflow in docs and change logs.

## Non-Goals

- No full transplant to GPU-count-only UX.
- No real large-scale DLC production run in this implementation pass.
- No Isaac Sim runtime logic.
- No redesign of batch chunking semantics.

## Architecture Decision

### Chosen Approach

Keep semantic profiles in `Auto-Asset-Annotator`, but back them with canonical GPU-count templates and quota routing.

That means:

- operators still choose workload intent through profile names
- the launcher resolves those profiles to GPU count
- GPU count then resolves to canonical CPU/memory/resource templates

### Why This Approach

- It preserves the cleaner operator UX already added in the first DLC upgrade.
- It avoids forcing annotation operators to think directly in terms of GPU-count-only templates.
- It aligns resource behavior with the current real cluster policy.

### Rejected Approach

Replace profiles entirely with `DLC_GPU_COUNT`-only UX.

Rejected because:

- it discards the annotation workload intent encoded by `api_light`, `local_hf_default`, and `local_hf_heavy`
- it makes common workflows less self-describing

## Proposed Resource Model

### Semantic profiles remain

- `api_light`
- `local_hf_default`
- `local_hf_heavy`

### Profile-to-template mapping

Recommended mapping for this repository:

- `api_light` -> `GPU_COUNT=1`
- `local_hf_default` -> `GPU_COUNT=1`
- `local_hf_heavy` -> `GPU_COUNT=4`

Rationale:

- `api_light` does remote inference and should stay small
- `local_hf_default` remains the normal single-GPU local path
- `local_hf_heavy` should represent a truly heavier local profile instead of another custom 1-GPU shape

### Canonical GPU-count templates

Use the newer reference values:

- `1 GPU` -> `14 CPU`, `100Gi`, `quota1r947pmazvk`
- `2 GPU` -> `28 CPU`, `200Gi`, `quota1r947pmazvk`
- `4 GPU` -> `56 CPU`, `400Gi`, `quota1r947pmazvk`
- `8 GPU` -> `128 CPU`, `960Gi`, `quotaksvqq2oh2pg`

These become the base templates before environment-variable overrides.

## Validation Rules To Add

### Launch layer validation

`launch_job.sh` should validate:

- `CHUNK_ID` is a non-negative integer
- `CHUNK_TOTAL` is a positive integer
- `CHUNK_ID < CHUNK_TOTAL`
- profile name is supported
- effective GPU count is one of `1, 2, 4, 8`

If any of these fail, the script should exit before DLC submission.

### Wrapper validation

The following wrappers should fail early if required files are missing:

- `submit_retry_failed.sh`
- `submit_asset_list.sh`

### Runtime validation

`python_runtime.sh` should become stricter:

For `openai_compatible`:

- require `--api_base_url`
- require `--api_key_env`
- require the referenced environment variable to be non-empty

For `local_hf`:

- if `--model_path` is explicitly provided as a local path, verify it exists

## Probe Workflow Design

### New wrapper

Add:

- `scripts/dlc/submit_probe.sh`

Purpose:

- provide one tiny, explicit, safe real-submit path
- default to `TOTAL=1`
- require explicit backend/profile choices where relevant
- encourage tiny input scope

### Probe guidance

The probe workflow should distinguish:

- dry-run proof: submission chain assembly only
- fake-launcher proof: resolved launcher config without a real DLC job
- real probe: tiny real DLC submission with minimal scope and a recorded result

## Documentation Changes

### `docs/dlc/README.md`

Add/adjust:

- canonical resource/quota mapping
- explanation that profiles are semantic, but templates are GPU-count aligned
- probe workflow overview

### `docs/dlc/TESTING.md`

Add/adjust:

- dry-run vs fake-launcher vs real-probe distinctions
- one exact probe recipe for `local_hf`
- one exact probe recipe for `openai_compatible`

### Change log

Add a second DLC change log documenting:

- quota migration
- resource template alignment
- validation additions
- new probe wrapper

## Acceptance Criteria

This design is satisfied when:

- the old resource quota is no longer the default in `launch_job.sh`
- profiles resolve through canonical `1/2/4/8 GPU` templates and correct less-gpu / more-gpu quotas
- invalid chunk arguments fail before submission
- wrappers fail early when required asset-list inputs are missing
- runtime preflight catches missing API backend requirements before execution
- a `submit_probe.sh` wrapper exists and is documented
- the operator docs explain the new quota/profile/probe model clearly
