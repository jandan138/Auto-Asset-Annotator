# API Backend For Multimodal Annotation Design

## Summary

This design introduces a backend abstraction for model inference so the annotation pipeline can run against either:

- local Hugging Face vision-language models, or
- remote OpenAI-compatible multimodal APIs.

The first remote backend target is the verified `New API` OpenAI-compatible endpoint using `gemini-2.5-flash-image`.

The goal is to preserve the current pipeline, prompt, parser, and JSON output flow while replacing only the model execution backend and its configuration surface.

## Context

The current implementation is tightly coupled to a local Hugging Face Qwen-VL stack:

- `src/auto_asset_annotator/core/model.py` loads weights with `from_pretrained(...)`
- `AnnotationPipeline` prepares Qwen-style multimodal messages and calls `engine.inference(messages)`
- the engine returns plain text, which the pipeline parses into structured JSON output

Recent API probing established the following facts:

- `gemini-2.0-flash` is not a reliable first migration target for this repository
- `gemini-2.5-flash-image` successfully handles:
  - native Gemini text requests
  - native Gemini multimodal requests
  - OpenAI-compatible text requests
  - OpenAI-compatible multimodal requests
  - OpenAI-compatible multi-image requests

That makes `gemini-2.5-flash-image` the correct first remote backend target.

## Goals

1. Preserve the current `AnnotationPipeline -> inference -> text -> parser -> JSON` architecture.
2. Add a backend abstraction that supports both local and remote inference.
3. Make the first API backend OpenAI-compatible so it can also support other gateways later.
4. Keep the current parser contract intact by continuing to request structured plain-text output.
5. Minimize changes outside the model/configuration layer.

## Non-Goals

- No parser rewrite.
- No prompt-system redesign.
- No bulk retry or dataset re-annotation changes.
- No provider-specific plugin system beyond what is needed for the first API backend.
- No direct Gemini-native backend in the first implementation pass.

## Architecture Decision

### Chosen Approach

Implement a small engine abstraction with two concrete backends:

- `LocalHFEngine` for the existing Hugging Face flow
- `OpenAICompatibleAPIEngine` for remote multimodal APIs

Select the backend through model configuration.

### Why This Approach

- It preserves the existing pipeline contract.
- It avoids baking `gemini-2.5-flash-image` directly into the current `ModelEngine`.
- It creates a clean seam for future OpenAI-compatible providers without overbuilding a full plugin system.

### Explicitly Rejected Approach

Hard-replacing the current engine with a Gemini-specific API client was rejected because it would:

- mix provider logic into the current local-model implementation
- make future model swaps harder
- require another refactor when adding OpenAI, Claude, or another compatible gateway later

## Proposed File Structure

### Modify

- `src/auto_asset_annotator/config/settings.py`
  - expand `ModelConfig` to support backend selection and API settings
- `src/auto_asset_annotator/core/model.py`
  - keep this as the model-engine entry point and local backend implementation
- `src/auto_asset_annotator/core/pipeline.py`
  - update typing/imports only as needed for the new engine interface
- `src/auto_asset_annotator/main.py`
  - instantiate the engine through a backend-aware factory
- `config/config.yaml`
  - document the first API backend configuration

### Create

- `src/auto_asset_annotator/core/api_model.py`
  - implement the OpenAI-compatible API backend and message conversion helpers

### Update Documentation

- `README.md`
- `CLAUDE.md`
- relevant usage/development docs after implementation

## Engine Interface Design

The pipeline should continue to rely on one minimal contract:

```python
class BaseModelEngine(Protocol):
    def inference(self, inputs_messages: List[Dict[str, Any]]) -> str:
        ...
```

The pipeline does not need to know whether inference is local or remote.

## Backend Design

### LocalHFEngine

This backend is the current implementation moved behind the shared interface.

Responsibilities:

- load local Hugging Face weights and processor
- convert the existing pipeline message structure into model tensors
- call `generate(...)`
- decode the generated output into plain text

This preserves the current local-Qwen behavior.

### OpenAICompatibleAPIEngine

Responsibilities:

- accept the existing pipeline message structure
- convert local image paths into OpenAI-compatible `image_url.url = data:image/...;base64,...`
- send `POST {api_base_url}/v1/chat/completions`
- return `choices[0].message.content` as plain text

This backend must be generic to any OpenAI-compatible multimodal gateway.

It must not hardcode New API behavior except through configuration defaults.

## Message Conversion Strategy

The current pipeline emits one `user` message with content items shaped like:

```python
{"type": "text", "text": user_prompt}
{"type": "image_url", "image": "/local/path/to/image.png"}
```

The first implementation should preserve this pipeline shape to avoid unnecessary parser/pipeline churn.

The API engine should translate those items into OpenAI-compatible content blocks:

```json
{
  "type": "text",
  "text": "..."
}
```

```json
{
  "type": "image_url",
  "image_url": {
    "url": "data:image/png;base64,..."
  }
}
```

### Why Convert Local Paths Inside The API Engine

- It keeps `AnnotationPipeline` unchanged.
- It avoids forcing local and remote backends to share one provider-specific content schema.
- It centralizes file reading, MIME detection, and base64 encoding in the remote backend only.

## Configuration Design

`ModelConfig` should be extended to include backend-aware settings.

### Proposed Fields

```python
@dataclass
class ModelConfig:
    name: str
    backend: str = "local_hf"
    api_base_url: Optional[str] = None
    api_key_env: Optional[str] = None
    api_timeout_seconds: int = 120
    api_max_retries: int = 2
    device_map: str = "auto"
    dtype: str = "bfloat16"
    attn_implementation: str = "flash_attention_2"
    temperature: float = 0.8
    max_new_tokens: int = 512
```

### Field Semantics

- `name`
  - local backend: Hugging Face model path/name
  - API backend: remote model ID, e.g. `gemini-2.5-flash-image`
- `backend`
  - `local_hf`
  - `openai_compatible`
- `api_base_url`
  - base URL without path suffix, e.g. `http://35.220.164.252:3888`
- `api_key_env`
  - environment variable name holding the API key, e.g. `NEWAPI_API_KEY`

### Why Keep `name`

Keeping `name` avoids broader config churn. The meaning becomes “model identifier” rather than strictly “local path”.

That is the smallest compatible change.

## Engine Factory Design

`main.py` should stop directly instantiating one concrete engine class.

Instead it should call a small factory function such as:

```python
engine = build_model_engine(cfg.model)
```

Factory behavior:

- `backend == "local_hf"` -> return `LocalHFEngine`
- `backend == "openai_compatible"` -> return `OpenAICompatibleAPIEngine`
- anything else -> raise a clear configuration error

## API Request Design

### Endpoint

```text
POST {api_base_url}/v1/chat/completions
```

### Headers

```text
Authorization: Bearer <api-key>
Content-Type: application/json
```

### Payload

```json
{
  "model": "gemini-2.5-flash-image",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "...prompt..."},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
      ]
    }
  ],
  "temperature": 0.8,
  "max_tokens": 512
}
```

### Response Extraction

Read:

```text
choices[0].message.content
```

and return it as a string to the existing parser.

## Error Handling Design

### Configuration Errors

Fail early with clear messages when:

- `backend=openai_compatible` but `api_base_url` is missing
- `backend=openai_compatible` but `api_key_env` is missing
- the configured environment variable is unset

### HTTP Errors

The API backend should raise concise exceptions that include:

- HTTP status code
- short error message body if present
- model name
- endpoint path used

### Retry Strategy

Use minimal retry behavior only for transient failures:

- network timeouts
- 429
- 5xx

Do not retry 4xx request-shape or auth errors.

## Dependency Strategy

The first implementation should avoid adding a new dependency if possible.

Preferred first pass:

- use standard-library HTTP (`urllib.request`) or another already-available mechanism

Reasoning:

- keeps the dependency surface minimal
- avoids unrelated packaging churn

If implementation becomes too awkward, adding one small HTTP client dependency is acceptable in a later pass, but not required for the first version.

## Backward Compatibility

The design preserves backward compatibility for local runs by default:

- `backend` defaults to `local_hf`
- existing local model configs continue to work
- parser behavior stays unchanged
- prompt behavior stays unchanged

The only semantic shift is that `model.name` now means “model identifier” rather than strictly “local path”.

## Testing Strategy

### Unit-Level Tests

Add tests for:

- engine factory backend selection
- local-path image conversion to `data:image/...;base64,...`
- OpenAI-compatible payload construction from pipeline messages
- API response extraction into plain text
- configuration validation for missing API settings

### Lightweight Verification

After implementation, verify:

- existing parser tests still pass
- package still imports
- local backend still constructs successfully without changing current configs

Network integration tests against the live API should be treated as optional/manual verification because they require external credentials.

## Future Extension Path

Once this design is in place, future expansion is straightforward:

- add `GeminiNativeAPIEngine` behind the same interface if needed
- add another OpenAI-compatible provider by config only
- add provider-specific adapters later without changing the pipeline contract

This means the first API backend is not a dead-end implementation.

## Risks And Mitigations

### Risk 1: Pipeline Message Shape Drift

If the pipeline later changes its internal message schema, the API engine converter could break.

Mitigation:

- keep the converter small and well-tested
- support both the current `image` field and future `image_url.url` style if necessary

### Risk 2: Remote Model Output Drift

Remote models may be less stable than the current local Qwen prompt path.

Mitigation:

- keep prompt wording strict
- continue using the existing parser and fallback-to-raw-output behavior
- prefer `temperature=0` or low temperature for structured extraction tasks if needed

### Risk 3: Credential Handling Mistakes

Putting raw API keys into config files would create a security problem.

Mitigation:

- only store the environment variable name in config
- resolve the actual secret at runtime

## Deliverable

The first implementation based on this design should produce:

- one backend-aware engine factory
- one local backend preserving current behavior
- one OpenAI-compatible multimodal backend using `gemini-2.5-flash-image`
- zero required changes to parser logic
- minimal required changes to pipeline logic

## Acceptance Criteria

This design is satisfied when:

- the repository can run with `backend=local_hf` exactly as before
- the repository can also run with `backend=openai_compatible`
- the remote backend accepts multiple local image paths and converts them to API-compatible payloads
- the API engine returns plain text to the existing parser
- the first remote target is `gemini-2.5-flash-image`
- the architecture remains generic enough to support additional OpenAI-compatible providers later
