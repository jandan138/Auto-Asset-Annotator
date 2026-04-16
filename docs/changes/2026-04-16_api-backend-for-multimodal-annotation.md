# API Backend For Multimodal Annotation

## Research / Investigation

- Reviewed `docs/superpowers/plans/2026-04-16-api-backend-for-multimodal-annotation.md` and aligned this change log with the full backend-abstraction implementation that shipped.
- Read `config/config.yaml`, `README.md`, `CLAUDE.md`, `docs/usage/configuration.md`, `docs/usage/quick_start.md`, and `docs/development/project_structure.md` to identify current user-facing gaps.
- Read `src/auto_asset_annotator/config/settings.py`, `src/auto_asset_annotator/core/model.py`, `src/auto_asset_annotator/core/api_model.py`, `src/auto_asset_annotator/main.py`, and `src/auto_asset_annotator/core/pipeline.py` so the documentation matched the shipped implementation rather than the plan alone.
- Confirmed the implemented API path is `openai_compatible`, the example remote model is `gemini-2.5-flash-image`, requests are sent to `/v1/chat/completions`, local image paths are converted to data URLs, and local-only fields such as `device_map`, `dtype`, and `attn_implementation` are ignored by the API backend.

## Design Decisions

- Kept documentation specific to the currently implemented `openai_compatible` backend instead of describing hypothetical future providers.
- Kept `config/config.yaml` checked in with a runnable `local_hf` default, and documented the first API target separately as an explicit example path.
- Repeated the local-only field caveat in multiple user entry points (`README.md`, usage docs, and developer docs) because that distinction affects both runtime behavior and troubleshooting.
- Documented environment-variable based API key handling only; no tracked file stores a raw API key.

## Code Changes

- Updated `config/config.yaml` to document `backend`, `api_base_url`, `api_key_env`, `api_timeout_seconds`, and `api_max_retries`, while restoring `local_hf` as the checked-in default and keeping `gemini-2.5-flash-image` as the documented API example target.
- Updated `README.md` with API-backed quick start guidance, environment variable setup, CLI override examples, and backend behavior notes.
- Updated `CLAUDE.md` to capture the new API backend constraint, API run examples, architecture notes, and config field semantics.
- Updated `docs/usage/configuration.md` to explain backend-aware model settings, API-specific fields, and which model fields are ignored by the API backend.
- Updated `docs/usage/quick_start.md` to show API-backed startup flow and clarify how to switch between API and local execution.
- Updated `docs/development/project_structure.md` to reflect `core/api_model.py`, the backend factory seam, and the unchanged parser pipeline.

## Testing

- Ran `PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_model_backends tests.test_parser_robustness` and it passed: 19 tests, 0 failures.
- Ran `PYTHONPATH=. .venv_dlc/bin/python tests/test_normalization.py` and it passed: 18/18 checks.
- Ran `.venv_dlc/bin/python -m compileall src` and it completed successfully.
- Ran an end-to-end API-backed smoke command against a disposable synthetic asset directory. The CLI completed, wrote an annotation JSON file, and the pipeline correctly fell back to `raw_output` because the synthetic red/blue test images did not contain a recognizable object.

## Open Issues

- API examples require both a real `api_base_url` and a populated `NEWAPI_API_KEY` environment variable. Using only one of them is insufficient.
- The docs describe the currently implemented `openai_compatible` backend only. If more remote providers are added later, the docs should be expanded deliberately rather than generalized prematurely.
