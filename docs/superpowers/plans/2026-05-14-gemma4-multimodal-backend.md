# Gemma4 Multimodal Backend Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a tested `local_gemma4_multimodal` backend, materialize the Gemma4 base model to a stable CPFS release path, and make tiny DLC probes aware of the backend.

**Architecture:** Keep `AnnotationPipeline` unchanged and add a separate Gemma4 engine that translates the existing message format into Hugging Face Gemma4 multimodal blocks. Preserve `local_hf` and `openai_compatible` behavior while adding targeted DLC validation for the new backend.

**Tech Stack:** Python 3.10+, `unittest`, dataclasses, Hugging Face `AutoProcessor`/`AutoModelForImageTextToText`, shell scripts, CPFS model storage, `apply_patch` for edits.

---

## File Structure Map

### Create

- `src/auto_asset_annotator/core/gemma4_model.py`
  - Gemma4-specific local multimodal engine.
- `docs/changes/2026-05-14_gemma4_multimodal_backend.md`
  - Change record, storage record, verification log, and remaining smoke-test gate.

### Modify

- `src/auto_asset_annotator/core/model.py`
  - Add `local_gemma4_multimodal` factory branch.
- `tests/test_model_backends.py`
  - Add fake processor/model tests for the new backend.
- `scripts/dlc/submit_probe.sh`
  - Accept `MODEL_BACKEND=local_gemma4_multimodal`.
- `scripts/dlc/python_runtime.sh`
  - Validate local model paths for `local_gemma4_multimodal`.
- `tests/test_dlc_scripts.py`
  - Add script tests for the new backend.
- `config/config.yaml`
  - Document Gemma4 local backend example.
- `docs/development/extending_models.md`
  - Document why Gemma4 is separate from Qwen `local_hf`.
- `CLAUDE.md`
  - Record constraints and usage examples.

### External Paths

- Source HF snapshot:
  `/cpfs/user/zhuzihou/.cache/huggingface/hub/models--unsloth--gemma-4-E4B-it-unsloth-bnb-4bit/snapshots/9746c23553347b443ebdc1caba1d41b52223d0c8`
- Target release path:
  `/cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8`
- Target adapter path:
  `/cpfs/user/zhuzihou/models/gemma4/adapters/genesis-llm-fullscale-v0-gpu2-seed42-epoch3`

## Task 1: Materialize Gemma4 Base Model

**Files:**
- External: `/cpfs/user/zhuzihou/models/gemma4/releases/...`
- External: `/cpfs/user/zhuzihou/models/gemma4/current`

- [ ] **Step 1: Create model release directories**

Run:

```bash
mkdir -p /cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8
mkdir -p /cpfs/user/zhuzihou/models/gemma4/adapters
```

- [ ] **Step 2: Copy the HF snapshot with symlink dereference**

Run:

```bash
rsync -aL --info=progress2 \
  /cpfs/user/zhuzihou/.cache/huggingface/hub/models--unsloth--gemma-4-E4B-it-unsloth-bnb-4bit/snapshots/9746c23553347b443ebdc1caba1d41b52223d0c8/ \
  /cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8/
```

Expected: the target contains real files, not symlinks.

- [ ] **Step 3: Write source metadata and checksums**

Run:

```bash
mkdir -p /cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8/_meta
```

Create `_meta/SOURCE.json` with the repo id, revision, source snapshot, target path, and copy date. Create `_meta/SHA256SUMS` with checksums for regular files.

- [ ] **Step 4: Update current symlink**

Run:

```bash
ln -sfn releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8 /cpfs/user/zhuzihou/models/gemma4/current
```

- [ ] **Step 5: Verify materialization**

Run:

```bash
find /cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8 -type l -print
du -sh /cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8
```

Expected: no symlink output under the release path and size around 11G.

## Task 2: Add Gemma4 Backend Tests

**Files:**
- Modify: `tests/test_model_backends.py`

- [ ] **Step 1: Add failing factory test**

Add a test that patches `LocalGemma4MultimodalEngine`, calls `build_model_engine(ModelConfig(name="gemma", backend="local_gemma4_multimodal"))`, and asserts the factory returns that object.

- [ ] **Step 2: Add failing message conversion test**

Add a fake engine instance without running `__init__`, call `_convert_messages_for_gemma4(...)`, and assert:

```python
[
    {"type": "image", "image": "/tmp/front.png"},
    {"type": "image", "image": "/tmp/left.png"},
    {"type": "text", "text": "Describe it."},
]
```

Images must appear before text.

- [ ] **Step 3: Add failing inference test with fake processor and model**

Patch `torch` and `transformers` in `sys.modules` before constructing the engine. The fake processor must record that `apply_chat_template()` is called with:

```python
tokenize=True
return_dict=True
return_tensors="pt"
add_generation_prompt=True
```

The fake model must receive `max_new_tokens` and the decoded output must be only the generated suffix.

- [ ] **Step 4: Run red tests**

Run:

```bash
PYTHONPATH=. .venv/bin/python -m pytest tests/test_model_backends.py -q
```

Expected: the new tests fail because the backend does not exist.

## Task 3: Implement Gemma4 Backend

**Files:**
- Create: `src/auto_asset_annotator/core/gemma4_model.py`
- Modify: `src/auto_asset_annotator/core/model.py`

- [ ] **Step 1: Implement `LocalGemma4MultimodalEngine`**

The implementation must:

- lazy import heavy dependencies
- load model with `AutoModelForImageTextToText` when available
- fall back to `Gemma4ForConditionalGeneration` when available
- raise a clear `ValueError` when neither class is available
- load `AutoProcessor`
- convert pipeline messages from `image_url` to Gemma4 `image`
- preserve pipeline content order while converting image blocks in place
- call processor tokenized chat template
- trim prompt tokens before decoding generated text

- [ ] **Step 2: Add factory branch**

In `build_model_engine()`:

```python
if config.backend == "local_gemma4_multimodal":
    from .gemma4_model import LocalGemma4MultimodalEngine
    return LocalGemma4MultimodalEngine(config)
```

- [ ] **Step 3: Run green tests**

Run:

```bash
PYTHONPATH=. .venv/bin/python -m pytest tests/test_model_backends.py -q
```

Expected: all model backend tests pass.

## Task 4: Add DLC Probe Support

**Files:**
- Modify: `scripts/dlc/submit_probe.sh`
- Modify: `scripts/dlc/python_runtime.sh`
- Modify: `tests/test_dlc_scripts.py`

- [ ] **Step 1: Add failing DLC tests**

Add tests that verify:

- `submit_probe.sh` accepts `MODEL_BACKEND=local_gemma4_multimodal`
- `python_runtime.sh` rejects a missing local Gemma4 `MODEL_PATH`

- [ ] **Step 2: Run red DLC tests**

Run:

```bash
PYTHONPATH=. .venv/bin/python -m pytest tests/test_dlc_scripts.py -q
```

Expected: the new tests fail before shell changes.

- [ ] **Step 3: Update scripts**

Change `submit_probe.sh` to map `local_gemma4_multimodal` to `local_hf_default`. Change `python_runtime.sh` so local model path validation applies to both `local_hf` and `local_gemma4_multimodal`.

- [ ] **Step 4: Run green DLC tests**

Run:

```bash
PYTHONPATH=. .venv/bin/python -m pytest tests/test_dlc_scripts.py -q
```

Expected: DLC tests pass.

## Task 5: Update Docs And Config Examples

**Files:**
- Modify: `config/config.yaml`
- Modify: `docs/development/extending_models.md`
- Modify: `CLAUDE.md`
- Create: `docs/changes/2026-05-14_gemma4_multimodal_backend.md`

- [ ] **Step 1: Document Gemma4 example config**

Add a commented `local_gemma4_multimodal` example under `model:` in `config/config.yaml`.

- [ ] **Step 2: Update development docs**

Record that Gemma4 uses a separate backend because the Qwen local path is not generic.

- [ ] **Step 3: Update operator guidance**

Add CLAUDE.md guidance that Gemma4 model-loading and annotation commands are heavy and should not be run unless explicitly requested.

- [ ] **Step 4: Write change record**

Document the design, storage path, no-live-inference constraint, tests run, and remaining smoke probe.

## Task 6: Review, Verify, Commit, Push

**Files:**
- All changed files

- [ ] **Step 1: Run targeted tests**

Run:

```bash
PYTHONPATH=. .venv/bin/python -m pytest tests/test_model_backends.py tests/test_dlc_scripts.py -q
```

- [ ] **Step 2: Run broader lightweight tests**

Run:

```bash
PYTHONPATH=. .venv/bin/python -m pytest tests -q
```

- [ ] **Step 3: Request multi-agent review**

Dispatch reviewers for:

- Gemma4 engine contract and model-loading risks
- DLC/script safety
- docs/config/operator clarity

- [ ] **Step 4: Apply required review fixes**

Fix Critical and Important review findings, then rerun targeted tests.

- [ ] **Step 5: Commit and push**

Run:

```bash
git status --short
git add docs/superpowers/specs/2026-05-14-gemma4-multimodal-backend-design.md docs/superpowers/plans/2026-05-14-gemma4-multimodal-backend.md
git commit -m "docs: plan gemma4 multimodal backend"
git add src/auto_asset_annotator/core/model.py src/auto_asset_annotator/core/gemma4_model.py tests/test_model_backends.py scripts/dlc/submit_probe.sh scripts/dlc/python_runtime.sh tests/test_dlc_scripts.py config/config.yaml docs/development/extending_models.md CLAUDE.md docs/changes/2026-05-14_gemma4_multimodal_backend.md
git commit -m "feat: add gemma4 multimodal backend"
git push
git status --short --branch
```

Expected: branch is pushed and working tree is clean.
