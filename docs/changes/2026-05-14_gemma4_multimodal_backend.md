# Gemma4 Multimodal Backend

## Research / Investigation

- Reviewed the current backend split: `local_hf` for Qwen-style local inference and `openai_compatible` for remote multimodal chat completions.
- Confirmed the existing local path is not generic because `LocalHFEngine.inference()` depends on `qwen_vl_utils.process_vision_info()`.
- Reviewed Genesis-LLM's Gemma4 wrapper and checkpoint metadata. The checkpoint family is multimodal, but the current Genesis runtime wrapper is text-only and tokenizes `text=prompts`.
- Reviewed local model storage and found the Gemma4 Hugging Face snapshot is a symlink forest. The base checkpoint is around 11G when dereferenced; the Genesis adapter is around 345M after materialization.

## Design Decisions

- Added `local_gemma4_multimodal` as a separate backend instead of extending `local_hf`.
- Kept `AnnotationPipeline` unchanged so API and Qwen behavior are not disturbed.
- Converted pipeline `image_url` blocks to Gemma4/Hugging Face `image` blocks inside the Gemma4 engine.
- Preserved pipeline content order while converting `image_url` blocks to Gemma4 `image` blocks.
- Raised the Transformers dependency floor to `transformers>=5.5.0` and made Gemma4 backend errors include the installed Transformers version when required classes are unavailable.
- Used fake processor/model unit tests instead of live model loading.
- Kept Genesis-LLM LoRA disabled by default; it is stored only as a future A/B candidate.

## Model Storage

Base model release path:

```text
/cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8
```

Convenience symlink:

```text
/cpfs/user/zhuzihou/models/gemma4/current
```

Genesis adapter path:

```text
/cpfs/user/zhuzihou/models/gemma4/adapters/genesis-llm-fullscale-v0-gpu2-seed42-epoch3
```

Materialization evidence:

- `rsync -aL` copied the HF snapshot with symlink dereference.
- `find <release-path> -type l -print` returned no symlinks under the release path.
- `du -sh <release-path>` reported 11G.
- `_meta/SOURCE.json` records repo id, revision, source snapshot, and target path.
- `_meta/SHA256SUMS` records checksums for 13 regular files.

## Code Changes

- Created `src/auto_asset_annotator/core/gemma4_model.py` with `LocalGemma4MultimodalEngine`.
- Updated `build_model_engine()` to support `backend="local_gemma4_multimodal"`.
- Added unit tests for:
  - factory selection
  - message conversion from `image_url` to Gemma4 `image`
  - processor-owned tokenized chat templating
  - missing Gemma4 Transformers classes with versioned errors
  - prompt-token trimming before decode
  - Unsloth Gemma4 4-bit runtime patch requirement
  - Unsloth compile-cache placement outside the repository working tree
- Added a skipped-by-default processor-only smoke test gated by `RUN_GEMMA4_PROCESSOR_SMOKE=1`.
- Added Unsloth runtime preparation for Unsloth Gemma4 checkpoint paths and local 4-bit bitsandbytes configs. The backend imports Unsloth before Transformers and defaults `UNSLOTH_COMPILE_LOCATION` to an absolute path outside the current working tree so Unsloth does not create `unsloth_compiled_cache/` in the repository root. Operators can override `UNSLOTH_COMPILE_LOCATION` to a run-local cache directory.
- Updated DLC probe scripts so `local_gemma4_multimodal` can be selected explicitly.
- Updated `submit_probe.sh` so model/API environment settings are converted into explicit `main.py` CLI flags for the resolved launcher command.
- Made `submit_probe.sh` require `MODEL_PATH` for `local_gemma4_multimodal` and append enforced model flags after operator-provided `EXTRA_MAIN_ARGS`.
- Updated DLC runtime preflight so Gemma4 local model paths are existence-checked.
- Updated `python_runtime.sh` to merge CLI-provided `--model_backend`, `--model_path`, `--api_base_url`, and `--api_key_env` with environment-derived values before validation.
- Updated config examples and user/developer documentation.

## Testing

Red/green tests run during implementation:

```text
PYTHONPATH=. python -m pytest tests/test_model_backends.py -q
```

The initial red run failed on the new Gemma4 tests because the backend did not exist. After implementation it passed.

```text
PYTHONPATH=. python -m pytest tests/test_dlc_scripts.py -q
```

The initial red run failed on the new DLC tests because `submit_probe.sh` rejected Gemma4 and `python_runtime.sh` did not validate Gemma4 paths. A later review-driven red run also caught CLI-only `--model_path` validation and missing `MODEL_PATH` on Gemma4 probes. After implementation, the DLC tests passed.

## Open Issues / Next Gate

- Live single-asset Gemma4 base smoke was run after the initial implementation using `/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python`.
- The checked `.venv_dlc` runtime has `transformers 5.2.0` and is not sufficient for Gemma4 multimodal input: processor-only smoke loaded a tokenizer-style processor and produced no image tensor keys.
- DLC `run_task.sh` can use a worker-side `DLC_PYTHON_RUNTIME`, but the current submit wrappers do not embed that variable into the submitted worker command. Gemma4 real DLC submission remains blocked until the worker log proves it is using a Gemma4-capable Python runtime.
- The Genesis-LLM QLoRA environment has `transformers 5.8.0.dev0`, `Gemma4ForConditionalGeneration`, Torch `2.10.0+cu128`, bitsandbytes, and Unsloth. Local precheck on this node reported `torch.cuda.is_available() == True`; the Genesis-LLM Gate0 QLoRA run record itself should still be treated as dependency/plumbing evidence, not full CUDA capability evidence.
- Processor-only smoke on the real GRScenes asset produced `Gemma4Processor` inputs with `pixel_values` and `image_position_ids`.
- A normal Gemma4 CLI run without Unsloth patch failed in the vision branch with bitsandbytes `FP4 quantization state not initialized` / `AssertionError` inside the Gemma4 vision tower.
- The fixed-backend live smoke succeeded for `/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets/basket/6c68230d67112b1dfd2bd7fa9322c756`.
- Smoke artifacts were kept outside the repository under `/cpfs/user/zhuzihou/tmp/auto_asset_annotator_smoke/20260514T024226Z_grscenes_basket_6c68230d_gemma4/`.
- Fresh post-fix local verification: `PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_model_backends tests.test_dlc_scripts` passed with 58 tests, 1 skipped.
- Fresh Genesis-env regression verification: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. /cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python -m pytest -p no:cacheprovider tests/test_model_backends.py::TestGemma4MultimodalEngine::test_unsloth_checkpoint_requires_unsloth_patch_with_clear_error -q` passed.
- Fresh symlink/default-cache live regression used `/cpfs/user/zhuzihou/models/gemma4/current` with no caller-provided `UNSLOTH_COMPILE_LOCATION`; the backend set `/tmp/auto_asset_annotator_unsloth_compiled_cache`, generated text from the real asset images, and left no `unsloth_compiled_cache/` under the repository root.
- A processor-only smoke can be run without model weights loaded by setting `RUN_GEMMA4_PROCESSOR_SMOKE=1` and optionally `GEMMA4_MODEL_PATH=<path>` for `tests/test_model_backends.py::TestGemma4MultimodalEngine::test_gemma4_processor_smoke_includes_image_tensors`.
- Production jobs should pin the immutable release path, not `current`.
- The Genesis adapter should only be evaluated after Gemma4 base passes the live smoke probe.

## Documentation Follow-up

After the live smoke, the docs were expanded so the operational path is not buried in the change record:

- `docs/usage/gemma4_local_smoke.md`: canonical local Gemma4 smoke runbook with environment choice, model paths, output isolation, processor-only smoke, real CLI smoke, Unsloth patch rationale, failure modes, and production gates.
- `docs/usage/output_schema.md`: canonical output schema reference explaining Auto-Asset JSON style, failure `raw_output`, and why it must not be directly overwritten onto GRScenes original metadata.
- `README.md`, `docs/usage/quick_start.md`, `docs/usage/configuration.md`, `docs/usage/cli_reference.md`, `docs/usage/data_preparation.md`, `docs/introduction/overview.md`, `docs/development/extending_models.md`, `docs/dlc/README.md`, `docs/dlc/TESTING.md`, and `docs/troubleshooting/common_issues.md` now link or summarize the Gemma4 smoke and schema constraints.
