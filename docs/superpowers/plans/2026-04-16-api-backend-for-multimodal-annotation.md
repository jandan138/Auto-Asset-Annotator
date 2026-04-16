# API Backend For Multimodal Annotation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a backend abstraction that keeps local Hugging Face inference working while enabling remote OpenAI-compatible multimodal inference for annotation, starting with `gemini-2.5-flash-image`.

**Architecture:** Keep `AnnotationPipeline` dependent on one engine contract: `inference(messages) -> str`. Split the current local model logic into `LocalHFEngine`, add `OpenAICompatibleAPIEngine` for remote requests, and select between them through `ModelConfig` plus a small factory. Preserve the existing prompt and parser pipeline, and convert local image paths to OpenAI-compatible data URLs inside the API backend.

**Tech Stack:** Python 3.10+, dataclasses, standard-library HTTP/JSON/base64 tooling, Pillow, existing parser tests, `apply_patch` for edits.

---

## File Structure Map

### Create

- `src/auto_asset_annotator/core/api_model.py`
  - New OpenAI-compatible backend and message/image conversion helpers.
- `tests/test_model_backends.py`
  - Unit tests for backend selection, API config validation, payload conversion, and response extraction.

### Modify

- `src/auto_asset_annotator/config/settings.py`
  - Extend `ModelConfig` with backend/API settings.
- `src/auto_asset_annotator/core/model.py`
  - Introduce a backend interface and factory, rename current engine into the local implementation, preserve a compatibility alias if needed.
- `src/auto_asset_annotator/core/pipeline.py`
  - Update imports/type hints only as needed for the engine interface.
- `src/auto_asset_annotator/main.py`
  - Instantiate engines through the backend factory and add CLI overrides for API backends.
- `config/config.yaml`
  - Add documented fields for the first API backend configuration.
- `README.md`
  - Document API-backend usage and environment variable setup.
- `CLAUDE.md`
  - Record the new API backend behavior and constraints.
- `docs/usage/configuration.md`
  - Document new backend/API settings.
- `docs/usage/quick_start.md`
  - Document a minimal API-backed run example.
- `docs/development/project_structure.md`
  - Reflect the new backend file and architecture seam.
- `docs/changes/2026-04-16_api-backend-for-multimodal-annotation.md`
  - Record research, design decisions, code changes, verification, and open issues for this implementation.

### Read As Source Of Truth

- `src/auto_asset_annotator/core/model.py`
- `src/auto_asset_annotator/core/pipeline.py`
- `src/auto_asset_annotator/config/settings.py`
- `src/auto_asset_annotator/main.py`
- `config/config.yaml`
- `docs/superpowers/specs/2026-04-16-api-backend-for-multimodal-annotation-design.md`

## Task 1: Add Backend-Aware Model Configuration And Engine Factory

**Files:**
- Modify: `src/auto_asset_annotator/config/settings.py`
- Modify: `src/auto_asset_annotator/core/model.py`
- Test: `tests/test_model_backends.py`

- [ ] **Step 1: Write failing tests for backend selection and config defaults**

Create `tests/test_model_backends.py` with these initial tests:

```python
import unittest

from src.auto_asset_annotator.config.settings import ModelConfig
from src.auto_asset_annotator.core.model import build_model_engine


class TestModelBackendFactory(unittest.TestCase):
    def test_model_config_defaults_to_local_backend(self):
        cfg = ModelConfig(name="local-model")
        self.assertEqual(cfg.backend, "local_hf")
        self.assertIsNone(cfg.api_base_url)
        self.assertIsNone(cfg.api_key_env)

    def test_unknown_backend_raises(self):
        cfg = ModelConfig(name="model", backend="unknown")
        with self.assertRaises(ValueError):
            build_model_engine(cfg)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the new tests to verify they fail before implementation**

Run:

```bash
PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_model_backends
```

Expected: FAIL because `backend` and `build_model_engine` do not exist yet.

- [ ] **Step 3: Extend `ModelConfig` with backend/API fields**

Update `src/auto_asset_annotator/config/settings.py` so `ModelConfig` includes:

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

Keep all existing local-HF fields intact.

- [ ] **Step 4: Refactor `core/model.py` into local backend + factory**

Implement this structure in `src/auto_asset_annotator/core/model.py`:

```python
from typing import Any, Dict, List, Protocol

from ..config.settings import ModelConfig


class BaseModelEngine(Protocol):
    def inference(self, inputs_messages: List[Dict[str, Any]]) -> str:
        ...


class LocalHFEngine:
    def __init__(self, config: ModelConfig):
        ...  # current ModelEngine logic moved here

    def inference(self, inputs_messages: List[Dict[str, Any]]) -> str:
        ...


def build_model_engine(config: ModelConfig) -> BaseModelEngine:
    if config.backend == "local_hf":
        return LocalHFEngine(config)
    if config.backend == "openai_compatible":
        from .api_model import OpenAICompatibleAPIEngine
        return OpenAICompatibleAPIEngine(config)
    raise ValueError(f"Unsupported model backend: {config.backend}")


ModelEngine = LocalHFEngine
```

Preserve the old `ModelEngine` name as a compatibility alias so existing imports outside the factory path do not break immediately.

- [ ] **Step 5: Re-run the factory tests to verify they pass**

Run:

```bash
PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_model_backends
```

Expected: PASS for the new config/factory tests.

- [ ] **Step 6: Stop for a review checkpoint without committing**

Run:

```bash
git diff -- src/auto_asset_annotator/config/settings.py src/auto_asset_annotator/core/model.py tests/test_model_backends.py
```

Expected: the diff only adds backend-aware config/factory scaffolding. Do not create a commit unless the user explicitly asks.

## Task 2: Implement The OpenAI-Compatible API Backend

**Files:**
- Create: `src/auto_asset_annotator/core/api_model.py`
- Modify: `tests/test_model_backends.py`

- [ ] **Step 1: Extend the tests to cover API config validation and payload translation**

Add these tests to `tests/test_model_backends.py`:

```python
import base64
import os
import tempfile
from io import BytesIO
from unittest import mock

from PIL import Image

from src.auto_asset_annotator.core.api_model import OpenAICompatibleAPIEngine


class TestOpenAICompatibleAPIEngine(unittest.TestCase):
    def make_png(self, color):
        img = Image.new("RGB", (8, 8), color)
        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        img.save(path, format="PNG")
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        return path

    def test_missing_api_key_env_raises(self):
        cfg = ModelConfig(
            name="gemini-2.5-flash-image",
            backend="openai_compatible",
            api_base_url="http://example.com",
            api_key_env="MISSING_KEY",
        )
        with self.assertRaises(ValueError):
            OpenAICompatibleAPIEngine(cfg)

    def test_message_conversion_turns_local_path_into_data_url(self):
        path = self.make_png((255, 0, 0))
        cfg = ModelConfig(
            name="gemini-2.5-flash-image",
            backend="openai_compatible",
            api_base_url="http://example.com",
            api_key_env="TEST_API_KEY",
        )
        with mock.patch.dict(os.environ, {"TEST_API_KEY": "secret"}):
            engine = OpenAICompatibleAPIEngine(cfg)
        payload = engine._build_payload([
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe it."},
                    {"type": "image_url", "image": path},
                ],
            }
        ])
        item = payload["messages"][0]["content"][1]
        self.assertEqual(item["type"], "image_url")
        self.assertTrue(item["image_url"]["url"].startswith("data:image/png;base64,"))

    def test_response_extraction_reads_chat_completion_text(self):
        cfg = ModelConfig(
            name="gemini-2.5-flash-image",
            backend="openai_compatible",
            api_base_url="http://example.com",
            api_key_env="TEST_API_KEY",
        )
        with mock.patch.dict(os.environ, {"TEST_API_KEY": "secret"}):
            engine = OpenAICompatibleAPIEngine(cfg)
        text = engine._extract_text({
            "choices": [
                {"message": {"content": "Category: cup"}}
            ]
        })
        self.assertEqual(text, "Category: cup")
```

- [ ] **Step 2: Run the tests to verify they fail before the backend exists**

Run:

```bash
PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_model_backends
```

Expected: FAIL because `core/api_model.py` and its methods do not exist yet.

- [ ] **Step 3: Implement `OpenAICompatibleAPIEngine`**

Create `src/auto_asset_annotator/core/api_model.py` with the following structure:

```python
import base64
import json
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, List
from urllib import error, request

from ..config.settings import ModelConfig


class OpenAICompatibleAPIEngine:
    def __init__(self, config: ModelConfig):
        self.config = config
        if not config.api_base_url:
            raise ValueError("api_base_url is required for openai_compatible backend")
        if not config.api_key_env:
            raise ValueError("api_key_env is required for openai_compatible backend")
        self.api_key = os.environ.get(config.api_key_env)
        if not self.api_key:
            raise ValueError(f"Environment variable {config.api_key_env} is not set")

    def _encode_image_as_data_url(self, image_path: str) -> str:
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "application/octet-stream"
        data = Path(image_path).read_bytes()
        encoded = base64.b64encode(data).decode("ascii")
        return f"data:{mime_type};base64,{encoded}"

    def _build_payload(self, inputs_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        converted_messages = []
        for message in inputs_messages:
            converted_content = []
            for item in message["content"]:
                if item["type"] == "text":
                    converted_content.append({"type": "text", "text": item["text"]})
                elif item["type"] == "image_url":
                    source = item.get("image") or item.get("image_url", {}).get("url")
                    converted_content.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": self._encode_image_as_data_url(source)},
                        }
                    )
            converted_messages.append({"role": message["role"], "content": converted_content})
        return {
            "model": self.config.name,
            "messages": converted_messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_new_tokens,
        }

    def _extract_text(self, response_data: Dict[str, Any]) -> str:
        return response_data["choices"][0]["message"]["content"]

    def inference(self, inputs_messages: List[Dict[str, Any]]) -> str:
        payload = self._build_payload(inputs_messages)
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.config.api_base_url.rstrip('/')}/v1/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.config.api_timeout_seconds) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"API request failed with HTTP {exc.code}: {body}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"API request failed: {exc.reason}") from exc
        return self._extract_text(data)
```

Keep the implementation small. Do not add retries yet in this task.

- [ ] **Step 4: Run the tests to verify the backend helpers pass**

Run:

```bash
PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_model_backends
```

Expected: PASS for factory/config/backend-helper tests.

- [ ] **Step 5: Stop for a review checkpoint without committing**

Run:

```bash
git diff -- src/auto_asset_annotator/core/api_model.py tests/test_model_backends.py src/auto_asset_annotator/core/model.py src/auto_asset_annotator/config/settings.py
```

Expected: the diff introduces a generic OpenAI-compatible backend without touching parser logic.

## Task 3: Wire The API Backend Into Main And Preserve Local Behavior

**Files:**
- Modify: `src/auto_asset_annotator/main.py`
- Modify: `src/auto_asset_annotator/core/pipeline.py`
- Modify: `tests/test_model_backends.py`

- [ ] **Step 1: Add a backend-selection test that exercises the factory through `main.py` configuration semantics**

Add this focused test to `tests/test_model_backends.py`:

```python
from src.auto_asset_annotator.core.model import LocalHFEngine


class TestFactorySelection(unittest.TestCase):
    def test_local_backend_factory_returns_local_engine(self):
        cfg = ModelConfig(name="local-model", backend="local_hf")
        engine = build_model_engine(cfg)
        self.assertIsInstance(engine, LocalHFEngine)
```

- [ ] **Step 2: Run the tests to verify the current wiring state before editing `main.py`**

Run:

```bash
PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_model_backends
```

Expected: PASS. This establishes a baseline before changing `main.py` and pipeline imports.

- [ ] **Step 3: Update `main.py` to use the backend factory and API CLI overrides**

Apply these exact changes in `src/auto_asset_annotator/main.py`:

```python
from .core.model import build_model_engine
```

Add CLI args:

```python
parser.add_argument("--model_backend", help="Override model backend")
parser.add_argument("--api_base_url", help="Override API base URL")
parser.add_argument("--api_key_env", help="Override API key environment variable name")
```

Apply overrides:

```python
if args.model_backend:
    cfg.model.backend = args.model_backend
if args.api_base_url:
    cfg.model.api_base_url = args.api_base_url
if args.api_key_env:
    cfg.model.api_key_env = args.api_key_env
```

Instantiate the engine with:

```python
engine = build_model_engine(cfg.model)
```

Keep `--model_path` behavior unchanged for now so it still overrides `cfg.model.name`.

- [ ] **Step 4: Update pipeline typing/imports only as needed**

If `src/auto_asset_annotator/core/pipeline.py` still imports the old concrete `ModelEngine` only for type hints, replace that dependency with the shared engine contract or a looser type that avoids coupling to one backend class.

Keep `_prepare_messages()` unchanged in this task.

- [ ] **Step 5: Re-run backend tests and parser tests to verify nothing regressed**

Run:

```bash
PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_model_backends tests.test_parser_robustness
```

Expected: PASS.

- [ ] **Step 6: Stop for a review checkpoint without committing**

Run:

```bash
git diff -- src/auto_asset_annotator/main.py src/auto_asset_annotator/core/pipeline.py tests/test_model_backends.py
```

Expected: the main entry point now supports both backends without changing parser flow.

## Task 4: Add API Configuration Defaults, Docs, And Lightweight Verification

**Files:**
- Modify: `config/config.yaml`
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `docs/usage/configuration.md`
- Modify: `docs/usage/quick_start.md`
- Modify: `docs/development/project_structure.md`
- Create: `docs/changes/2026-04-16_api-backend-for-multimodal-annotation.md`

- [ ] **Step 1: Update the sample config to document both local and API fields**

Update `config/config.yaml` so the model section can express either backend. The first documented API example should look like this:

```yaml
model:
  name: gemini-2.5-flash-image
  backend: openai_compatible
  api_base_url: http://35.220.164.252:3888
  api_key_env: NEWAPI_API_KEY
  api_timeout_seconds: 120
  api_max_retries: 2
  device_map: auto
  dtype: bfloat16
  attn_implementation: flash_attention_2
  temperature: 0.1
  max_new_tokens: 512
```

Document clearly that `device_map`, `dtype`, and `attn_implementation` are local-backend settings and ignored by the API backend.

- [ ] **Step 2: Update user-facing docs with one API-backed run path**

Apply these exact doc updates:

```markdown
README.md
- explain that inference can run either locally or through an OpenAI-compatible API backend
- show `NEWAPI_API_KEY=...` as an environment variable example, not an inline secret in YAML

docs/usage/configuration.md
- document `backend`, `api_base_url`, `api_key_env`, `api_timeout_seconds`, `api_max_retries`

docs/usage/quick_start.md
- add one API-backed example command using `--model_backend openai_compatible`

docs/development/project_structure.md
- add `core/api_model.py` and note that `core/model.py` now owns backend selection and local HF behavior

CLAUDE.md
- add a short note that API-backed annotation is supported through the backend abstraction and that heavy VLM local loading rules still apply only to local-HF runs
```

- [ ] **Step 3: Write the implementation change log**

Create `docs/changes/2026-04-16_api-backend-for-multimodal-annotation.md` with these sections:

```markdown
## Research / Investigation
## Design Decisions
## Code Changes
## Testing
## Open Issues
```

Record:

- why `gemini-2.5-flash-image` was chosen as the first target
- why the first API backend uses OpenAI-compatible `chat/completions`
- what was kept unchanged in the parser/pipeline

- [ ] **Step 4: Run lightweight verification commands**

Run:

```bash
PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_model_backends tests.test_parser_robustness
PYTHONPATH=. .venv_dlc/bin/python tests/test_normalization.py
.venv_dlc/bin/python -m compileall src
```

Expected:

- backend tests pass
- parser tests pass
- normalization script passes
- source compiles without syntax errors

- [ ] **Step 5: Run one manual API smoke command with environment variable-based auth**

Run:

```bash
export NEWAPI_API_KEY="<redacted>"
python -m auto_asset_annotator.main \
  --config config/config.yaml \
  --model_backend openai_compatible \
  --api_base_url http://35.220.164.252:3888 \
  --api_key_env NEWAPI_API_KEY \
  --model_path gemini-2.5-flash-image \
  --input_dir /path/to/test-assets \
  --output_dir /tmp/auto-asset-annotator-smoke
```

Expected: only run this if a small disposable test asset directory is available and the user still wants live verification. If no test assets are available, explicitly skip and document the reason.

- [ ] **Step 6: Stop for final review without committing**

Run:

```bash
git diff --stat
git diff
```

Expected: the final diff should show one coherent backend-abstraction change with docs and tests. Do not create a commit unless the user explicitly asks.

## Self-Review Checklist

- [ ] Spec coverage check: Task 1 covers config/backend abstraction; Task 2 covers the OpenAI-compatible API backend; Task 3 covers runtime wiring; Task 4 covers config/docs/verification.
- [ ] Draft-marker scan: search this plan for banned drafting markers and remove any accidental match before execution.
- [ ] Consistency check: keep `backend` values limited to `local_hf` and `openai_compatible`; keep the first remote target as `gemini-2.5-flash-image`; keep the engine contract as `inference(messages) -> str`.

## Notes For The Implementer

- Use `apply_patch` for manual edits.
- Do not store raw API keys in tracked files.
- Do not remove or rewrite the parser fallback behavior.
- Do not create a git commit unless the user explicitly asks for one.
