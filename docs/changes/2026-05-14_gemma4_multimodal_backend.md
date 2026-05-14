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
- Added a skipped-by-default processor-only smoke test gated by `RUN_GEMMA4_PROCESSOR_SMOKE=1`.
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

- No live Gemma4 model load or annotation was run in this change.
- The Gemma4 runtime environment still needs a tiny explicit smoke probe to verify Transformers/Gemma4 dependency compatibility and DLC visibility of `/cpfs/user/zhuzihou`.
- A processor-only smoke can be run without model weights loaded by setting `RUN_GEMMA4_PROCESSOR_SMOKE=1` and optionally `GEMMA4_MODEL_PATH=<path>` for `tests/test_model_backends.py::TestGemma4MultimodalEngine::test_gemma4_processor_smoke_includes_image_tensors`.
- Production jobs should pin the immutable release path, not `current`.
- The Genesis adapter should only be evaluated after Gemma4 base passes the live smoke probe.
