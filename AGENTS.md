# AGENTS.md - AI Agent Rules for Auto-Asset-Annotator

## Project Context

Auto-Asset-Annotator is a Qwen2.5-VL based 3D asset annotation pipeline. The maintained runtime chain is:

```text
CLI -> Config -> ModelEngine -> AnnotationPipeline -> parsed JSON output
```

The current project records 52,907 annotated assets with complete `description`, `material`, `dimensions`, `mass`, and `placement` fields. Treat `output/` as the stable structured result set unless a task explicitly says otherwise.

## Key Rules

1. Do not run local VLM annotation commands unless explicitly instructed; they can load large model weights.
2. Do not run API-backed annotation commands unless explicitly instructed; they can consume remote quota and require real secrets.
3. Do not submit real DLC jobs unless explicitly instructed; dry-run first and record the command.
4. Never commit API keys, credentials, `.env` files, model weights, checkpoints, or large generated outputs.
5. Keep `config/config.yaml` as the checked-in default configuration; use CLI flags or environment variables for run-specific overrides.
6. Treat model output as structured text that is parsed into JSON by the pipeline, not as trusted direct JSON.
7. New work must update the relevant docs when behavior, commands, runtime assumptions, or operational status changes.
8. New dated execution records go under `docs/records/` using the filename pattern YYYY-MM-DD-topic.md; older records remain under `docs/changes/`.

## Documentation Entrypoints

- Project overview: `README.md`
- Documentation index: `docs/index.md`
- Runtime lock: `ANNOTATOR_RUNTIME_LOCK.md`
- DLC runbook: `docs/dlc/README.md`
- New dated records: `docs/records/`
- Historical March/April records: `docs/changes/`
- Superpowers design and plans: `docs/superpowers/`

## Commands

```bash
pip install -r requirements.txt
pip install -e .
python -m auto_asset_annotator.main --input_dir /path/to/assets --output_dir /path/to/results
python -m pytest tests/test_parser_robustness.py -v
bash scripts/dlc/submit_annotate.sh --dry-run
```

## Safety Notes

README examples and DLC examples are operational commands, not smoke tests. Use `--dry-run` for DLC wrappers before any real submission. For `openai_compatible`, set a real `api_base_url` and API key environment variable outside tracked files. For `local_hf`, confirm the model path exists in the runtime environment before running annotation.

## Directory Quick Reference

- Source: `src/auto_asset_annotator/`
- Config: `config/config.yaml`
- DLC wrappers: `scripts/dlc/`
- Utility scripts: `scripts/`
- Current docs: `docs/`
- Historical and maintained script list inputs: `archive/temp_lists/`
- Stable output set: `output/`
