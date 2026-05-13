# Auto-Asset-Annotator Documentation

Last updated: 2026-05-13

## Quick Navigation

- Root agent rules: `../AGENTS.md`
- Runtime lock: `../ANNOTATOR_RUNTIME_LOCK.md`
- User quick start: `usage/quick_start.md`
- CLI reference: `usage/cli_reference.md`
- Configuration: `usage/configuration.md`
- DLC runbook: `dlc/README.md`
- Troubleshooting: `troubleshooting/common_issues.md`
- Historical records: `docs/changes/`
- Superpowers specs and plans: `superpowers/`

## Project Overview

Auto-Asset-Annotator annotates 3D assets with structured physical and semantic fields. The maintained chain is:

```text
CLI -> Config -> ModelEngine -> AnnotationPipeline -> parsed JSON output
```

## Current Status

- Historical records report 52,907 assets with complete structured annotations; this documentation pass did not re-count the output set.
- `output/` is the stable structured result set.
- The default prompt is `extract_object_attributes_prompt`.
- The model returns structured text for extraction prompts; the pipeline parses it into JSON.

## Documentation Map

- `design/` - long-lived design indexes and future stable designs.
- `operations/` - maintained runbook index.
- `records/` - new dated execution records.
- `reference/` - stable reference index.
- `docs/changes/` - historical March and April 2026 records retained at original paths.
- `superpowers/` - agent design specs and implementation plans.

## Writing Policy

Use current docs for current behavior. Use dated records for work history. When changing commands, runtime assumptions, DLC behavior, output contracts, or validation status, update the relevant docs and link evidence from `../ANNOTATOR_RUNTIME_LOCK.md` when the validated state changes.
