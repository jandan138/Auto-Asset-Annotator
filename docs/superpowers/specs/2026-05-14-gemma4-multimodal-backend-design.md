# Gemma4 Multimodal Backend Design

## Summary

This design adds Gemma4 as a separate local multimodal backend for asset annotation. The backend must not reuse the existing `local_hf` inference path because that path is Qwen-oriented and depends on `qwen_vl_utils.process_vision_info()`.

The first production candidate is the base `unsloth/gemma-4-E4B-it-unsloth-bnb-4bit` instruction checkpoint. Genesis-LLM LoRA adapters stay disabled by default until they win a direct probe against the base model.

## Context

The current annotator has two supported inference modes:

- `local_hf`: local Hugging Face Qwen-VL style inference
- `openai_compatible`: remote multimodal chat completions, currently used for Gemini-compatible gateways

`AnnotationPipeline` emits one user message with content shaped like:

```python
{"type": "text", "text": user_prompt}
{"type": "image_url", "image": "/path/to/view.png"}
```

The existing `local_hf` engine then uses Qwen-specific preprocessing. Gemma4 expects Hugging Face multimodal chat content blocks using `{"type": "image", "image": ...}` and processor-owned token/media alignment.

Genesis-LLM confirms that the local Gemma4 checkpoint family is multimodal through its processor metadata, but its current runtime wrapper uses text-only generation. That wrapper is not the right integration point for image-based asset annotation.

## Goals

1. Add a tested `local_gemma4_multimodal` backend without changing the existing Qwen or API behavior.
2. Convert annotator messages to Gemma4/Hugging Face multimodal messages inside the Gemma4 engine.
3. Materialize the Gemma4 base checkpoint under a stable CPFS model path instead of relying on the Hugging Face cache.
4. Make DLC probe scripts aware of the new backend so tiny real probes can be submitted explicitly.
5. Document the model path, backend contract, probe gates, and Genesis LoRA policy.

## Non-Goals

- No full annotation run.
- No live heavy model inference in this implementation pass.
- No parser rewrite.
- No generic "all local multimodal Transformers models" claim.
- No default use of Genesis-LLM adapters.
- No deletion of the Hugging Face cache until a later real DLC smoke/probe succeeds.

## Architecture Decision

### Chosen Approach

Add a new concrete backend named `local_gemma4_multimodal`.

The backend keeps the existing engine contract:

```python
class BaseModelEngine(Protocol):
    def inference(self, inputs_messages: List[Dict[str, Any]]) -> str:
        ...
```

The pipeline remains unchanged. Only the Gemma4 engine translates the pipeline message shape into Gemma4/HF multimodal blocks.

### Rejected Approach: Reuse `local_hf`

Reusing `local_hf` would look smaller but is unsafe. It would route Gemma4 images through Qwen preprocessing, which can silently drop image tokens or produce text-only prompts.

### Rejected Approach: Generic `local_transformers_multimodal`

A generic backend would overstate support. Gemma4 has specific processor, chat-template, and dependency requirements. The public backend name should match what is tested.

## Backend Design

Create `src/auto_asset_annotator/core/gemma4_model.py`.

Responsibilities:

- lazily import `torch` and `transformers` only when the backend is instantiated
- load the processor through `AutoProcessor.from_pretrained(...)`
- load a multimodal generation class, preferring `AutoModelForImageTextToText` when available
- convert `image_url` blocks to `image` blocks
- preserve the pipeline content order while converting image blocks in place
- call `processor.apply_chat_template(..., tokenize=True, return_dict=True, return_tensors="pt", add_generation_prompt=True)`
- call `model.generate(...)`
- decode only newly generated tokens and return plain text

The implementation should use tests with fake processor/model objects. Real model loading is intentionally left to an explicit later smoke probe.

Gemma4 requires a Transformers build with Gemma4 multimodal classes. The project dependency floor is `transformers>=5.5.0`, and the backend error should include the installed Transformers version when the required classes are unavailable.

## Configuration Design

No required new `ModelConfig` fields are needed for the first pass.

The minimal config is:

```yaml
model:
  backend: "local_gemma4_multimodal"
  name: "/cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8"
  device_map: "auto"
  dtype: "bfloat16"
  attn_implementation: "eager"
  temperature: 0.1
  max_new_tokens: 2048
```

If a smoke run later proves Gemma4 needs processor-specific padding control, add a narrow field then. Do not add broad catch-all kwargs now.

## Model Storage Design

Materialize the base model outside the repo:

```text
/cpfs/user/zhuzihou/models/gemma4/
  releases/
    unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/
      9746c23553347b443ebdc1caba1d41b52223d0c8/
        _meta/
          SOURCE.json
          SHA256SUMS
  adapters/
    genesis-llm-fullscale-v0-gpu2-seed42-epoch3/
  current -> releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8
```

The copy must dereference Hugging Face cache symlinks using `rsync -aL` or equivalent. Production jobs should pin the immutable release path, not `current`.

## DLC Design

`submit_probe.sh` should accept `local_gemma4_multimodal` and map it to a local-model profile. `python_runtime.sh` should validate `MODEL_PATH` for both `local_hf` and `local_gemma4_multimodal`.

Operators still need an explicit `MODEL_BACKEND` and explicit asset list for probes.

## Quality Gate

Gemma4 should not be enabled by parse success alone. A later probe must save raw text for every asset and compare:

- Qwen local baseline
- Gemini/OpenAI-compatible API baseline, if quota is available
- Gemma4 base
- Gemma4 plus Genesis LoRA only after the base path is stable

Minimum gates:

- raw-output rate no worse than Qwen baseline
- all structured fields present in at least 99% of parsed outputs
- dimensions, mass, and placement formats valid
- prompt leakage and cross-field contamination below 0.5%
- human blind review shows Gemma4 win/tie against Qwen on at least 95% of reviewed assets

## Risks

- The installed Transformers version may not support Gemma4. The backend must fail with a clear backend-specific error.
- DLC workers may not see `/cpfs/user/zhuzihou`. The first real probe must confirm path visibility.
- The Genesis LoRA may reduce visual annotation quality because it was trained through a text-only wrapper.
- Gemma4 may produce plausible but generic physical attributes, so raw-output inspection remains required.

## Approval State

The user approved the recommended direction on 2026-05-14 and explicitly asked to continue without blocking on further questions.
