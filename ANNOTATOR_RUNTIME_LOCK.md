# Auto-Asset-Annotator Runtime Lock

Validation status: ANNOTATION_OUTPUT_COMPLETE_2026_03_09_AND_DLC_WORKFLOW_REFRESHED_2026_04_16

Validation dates:

- Annotation completion evidence: 2026-03-09
- DLC workflow refresh evidence: 2026-04-16
- Documentation governance lock created: 2026-05-13

## Runtime Chain

```text
CLI -> Config -> ModelEngine -> AnnotationPipeline -> parsed JSON output
```

## Default Local Runtime

- Package entrypoint: `python -m auto_asset_annotator.main`
- Default config: `config/config.yaml`
- Default backend: `local_hf`
- Default local model path: `/cpfs/shared/simulation/zhuzihou/models/Qwen2.5-VL-7B-Instruct`
- Default prompt type: `extract_object_attributes_prompt`
- Default output behavior: model returns structured text; pipeline parses and normalizes fields; `main.py` writes JSON.

Config source: checked-in `config/config.yaml` and current root docs as of this lock update.

## Supported Backends

- `local_hf`: local Hugging Face/Qwen-VL inference.
- `openai_compatible`: remote multimodal chat-completions-compatible inference using data URL images.

## Output State

Validated from historical records, not re-counted during this documentation pass:

- Total annotated assets: 52,907
- Original assets: 50,091
- Backfilled assets: 2,816
- Complete fields: `description`, `material`, `dimensions`, `mass`, `placement`
- Stable structured result directory: `output/`

## DLC Runtime State

- Maintained chain: `submit_*.sh -> submit_batch.py -> launch_job.sh -> run_task.sh -> python_runtime.sh -> python -m auto_asset_annotator.main`
- Maintained runbook: `docs/dlc/README.md`
- Current smartbot quota mapping:
  - `1/2/4 GPU` -> `quota1r947pmazvk`
  - `8 GPU` -> `quotaksvqq2oh2pg`

## Evidence Records

- Project completion overview: `docs/changes/PROJECT_PROGRESS.md`
- DLC balanced upgrade: `docs/changes/2026-04-16_dlc_balanced_upgrade.md`
- DLC quota alignment and probe: `docs/changes/2026-04-16_dlc_quota_alignment_and_probe.md`
- Documentation cleanup record: `docs/changes/2026-04-15_repo-cleanup-and-doc-governance-execution.md`

## Boundaries

- This lock records documented project state; it does not prove a fresh model run.
- This lock does not validate a live API endpoint.
- This lock does not validate a fresh real DLC submission.
- This lock does not contain secrets, API keys, model weights, or credentials.

## Update Checklist

- Update this file when default backend, model path, prompt type, output state, DLC quota mapping, or validation evidence changes.
- Record the evidence file before promoting a new validation status.
- Do not record secrets or API keys in this file.
