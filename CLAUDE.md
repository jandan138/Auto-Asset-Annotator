# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Shared Agent Rules

Read `AGENTS.md` for repository-wide agent rules, safety constraints, documentation requirements, and directory quick reference. Use `docs/index.md` for the maintained documentation map and `ANNOTATOR_RUNTIME_LOCK.md` for validated runtime-state boundaries. This file keeps Claude Code specific commands, architecture notes, and operational details.

## Important Constraints

**Do not run annotation commands** (commands that load and run the VLM) unless explicitly told to do so. The model is large (Qwen2.5-VL-7B-Instruct) and loading it is expensive.

The repository now also supports an `openai_compatible` multimodal API backend. Avoid running live API-backed annotation commands unless explicitly told to do so, because they consume remote quota and require a real API key in the environment.

## Commands

### Installation
```bash
pip install -r requirements.txt
pip install -e .
```

### Download model (first time setup)
```bash
python scripts/download_model.py
```

### Run annotation
```bash
# Basic run (uses checked-in local_hf config/config.yaml by default)
python -m auto_asset_annotator.main --input_dir /path/to/assets --output_dir /path/to/results

# API-backed example: requires both a real API base URL and NEWAPI_API_KEY
export NEWAPI_API_KEY="<your-api-key>"
python -m auto_asset_annotator.main \
    --model_backend openai_compatible \
    --model_path gemini-2.5-flash-image \
    --api_base_url https://your-openai-compatible-host \
    --api_key_env NEWAPI_API_KEY \
    --input_dir /path/to/assets --output_dir /path/to/results

# Override backend and API settings from CLI
python -m auto_asset_annotator.main \
    --model_backend openai_compatible \
    --model_path gemini-2.5-flash-image \
    --api_base_url https://your-openai-compatible-host \
    --api_key_env NEWAPI_API_KEY \
    --input_dir /path/to/assets --output_dir /path/to/results

# Exporting only NEWAPI_API_KEY is not enough if api_base_url is still a placeholder

# Override prompt type
python -m auto_asset_annotator.main --prompt_type classify_object_category_prompt --input_dir /data/assets --output_dir /data/results

# Force re-annotation even if output already exists
python -m auto_asset_annotator.main --input_dir /data/assets --output_dir /data/results --force

# Re-annotate only assets with empty physical property fields
python -m auto_asset_annotator.main --input_dir /data/assets --output_dir /data/results --retry_incomplete

# Use a pre-built asset list file instead of scanning
python -m auto_asset_annotator.main --input_dir /path/to/assets --asset_list_file archive/temp_lists/failed_assets.txt --output_dir ./output

# Distributed chunking (e.g., 4-machine parallel)
python -m auto_asset_annotator.main --num_chunks 4 --chunk_index 0  # machine 1
python -m auto_asset_annotator.main --num_chunks 4 --chunk_index 1  # machine 2
```

### Run tests
```bash
python -m pytest tests/test_parser_robustness.py -v
# Or directly:
python tests/test_parser_robustness.py
```

### Utility scripts
```bash
# Find successfully annotated assets (no "raw_output" field in JSON)
python scripts/find_success_assets.py --output_dir ./output --save_list success_assets.txt

# Find failed assets (has "raw_output" field indicating parse failure)
python scripts/find_failed_assets.py --output_dir ./output --save_list archive/temp_lists/failed_assets.txt

# Find assets with incomplete/empty physical property fields
python scripts/find_incomplete_assets.py --output_dir ./output --save_list archive/temp_lists/incomplete_assets.txt
python scripts/find_incomplete_assets.py --output_dir ./output --save_list archive/temp_lists/incomplete_assets.txt --strict --stats

# Merge re-annotated results into existing annotations (selective field fill)
python scripts/merge_annotations.py --old_dir ./output --new_dir ./output_reannotate           # dry-run
python scripts/merge_annotations.py --old_dir ./output --new_dir ./output_reannotate --apply   # apply

# Fill empty physical properties with category-based defaults (material, mass, placement)
python scripts/fill_defaults.py --output_dir ./output --asset_list archive/temp_lists/remaining_incomplete.txt           # dry-run
python scripts/fill_defaults.py --output_dir ./output --asset_list archive/temp_lists/remaining_incomplete.txt --apply   # apply

# Download model from hf-mirror.com (for China users)
python scripts/download_model.py
```

### Verify installation
```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); import auto_asset_annotator; print('Package loaded successfully')"
```

### DLC Remote Job Submission

For large-scale distributed annotation on Alibaba Cloud PAI-DLC:

```bash
# Preferred operator entrypoint: wrapper script around submit_batch.py
bash scripts/dlc/submit_annotate.sh --dry-run

# Tiny probe path: create or verify the small asset list first, then run with --dry-run.
printf 'category/asset_id\n' > archive/temp_lists/probe_assets.txt
MODEL_BACKEND=openai_compatible ASSET_LIST_FILE=archive/temp_lists/probe_assets.txt bash scripts/dlc/submit_probe.sh --dry-run

# Retry failed assets
bash scripts/dlc/submit_retry_failed.sh --dry-run

# Retry incomplete results
bash scripts/dlc/submit_retry_incomplete.sh --dry-run

# Explicit asset list workflow
bash scripts/dlc/submit_asset_list.sh --dry-run --asset_list_file archive/temp_lists/failed_assets.txt

# Raw submit_batch.py remains available for custom chunk-mode main.py flags
python scripts/dlc/submit_batch.py --total 8 --name classify_task \
    --command_args "--input_dir /data/assets --output_dir /data/results --prompt_type classify_object_category_prompt" \
    --dry-run

# Check DLC job status
./dlc get jobs
./dlc logs <job_id>
```

The upgraded chain is `submit_*.sh -> submit_batch.py -> launch_job.sh -> run_task.sh -> python_runtime.sh -> python -m auto_asset_annotator.main`.

The current launcher also follows the newer smartbot quota split:

- `1/2/4 GPU` -> `quota1r947pmazvk`
- `8 GPU` -> `quotaksvqq2oh2pg`

Semantic profiles (`api_light`, `local_hf_default`, `local_hf_heavy`) are still the preferred operator interface, but they now resolve through those canonical GPU-count templates.

Preferred operator entrypoints are the wrapper scripts in `scripts/dlc/`. Use raw `submit_batch.py` only for non-standard chunk-mode batches.

See [docs/dlc/README.md](docs/dlc/README.md) for the maintained DLC operator workflow.

## Architecture

The pipeline is a linear chain: **CLI → Config → ModelEngine → AnnotationPipeline → parsed JSON output**.

```
src/auto_asset_annotator/
├── main.py              # Entry point: CLI parsing, asset listing, processing loop
├── config/
│   └── settings.py      # Dataclasses: Config, ModelConfig, DataConfig, ProcessingConfig, PromptConfig
├── core/
│   ├── api_model.py     # OpenAI-compatible multimodal backend for remote chat completions
│   ├── model.py         # Backend factory + LocalHFEngine compatibility alias
│   ├── pipeline.py      # AnnotationPipeline: orchestrates image discovery → prompt → inference → parsing
│   └── prompt.py        # PromptFactory: all prompt templates; SUPPORTED_PROMPT_TYPES list
└── utils/
    ├── file.py           # list_assets() scans dir tree; get_asset_images() resolves view patterns
    └── image.py          # Image loading and concatenation utilities
```

### Key data flow in `pipeline.py`

1. `get_asset_images()` resolves view patterns from `config.data.views` (e.g., `front: ["front.png", "0.png"]`), falling back to all sorted images in the asset directory if no named views are found.
2. `PromptFactory.compose_user_prompt()` selects the prompt template by `prompt_type`.
3. `build_model_engine()` selects either the local Hugging Face engine or the `openai_compatible` API engine.
4. For `extract_*` and `json`-named prompts, the model is asked to return structured text. `parse_structured_text_enhanced()` then extracts key-value pairs (Category, Description, Material, Dimensions, Mass, Placement), and `main.py` writes the parsed result to a JSON file. On parse failure, `{"raw_output": <text>}` is saved.

For the `openai_compatible` backend, `core/api_model.py` converts local image paths to data URLs and POSTs them to `/v1/chat/completions`. `device_map`, `dtype`, and `attn_implementation` remain in `ModelConfig` for `local_hf` only and are ignored by the API path.

### Retry behavior

In `main.py`, assets are automatically retried if:
- The output file doesn't exist
- The output file contains `"raw_output"` (indicating a previous parse failure)
- The `--retry_incomplete` flag is passed and one of `material`, `dimensions`, `mass`, or `placement` is empty
- The `--force` flag is explicitly passed

This means you can re-run the same command to retry failed assets without needing to manually filter them.

### Output format

Each asset produces `{output_dir}/{category}/{asset_id}_annotation.json` after the pipeline parses the model's structured text output:

**Success format:**
```json
{
  "category/asset_id": {
    "category": "bowl",
    "description": "...",
    "material": "...",
    "dimensions": "0.2 * 0.2 * 0.08",
    "mass": "0.5",
    "placement": "OnTable, OnObject"
  }
}
```

**Failure format (will be retried on next run):**
```json
{
  "category/asset_id": {
    "raw_output": "unparsed model output text..."
  }
}
```

### Asset directory structure expected

```
input_dir/
  category/
    asset_uuid/
      front.png (or 0.png)
      left.png  (or 1.png)
      back.png  (or 2.png)
      right.png (or 3.png)
```

`list_assets()` walks `input_dir` recursively, records any directory that contains images as an asset, and stops descending further into that matched branch.

## Configuration (`config/config.yaml`)

Key fields to know:
- `model.backend`: `"local_hf"` for on-box inference or `"openai_compatible"` for remote Chat Completions
- `model.name`: local model path for `local_hf`, or remote model name such as `gemini-2.5-flash-image` for `openai_compatible`
- `model.api_base_url` / `model.api_key_env`: required for `openai_compatible`
- `model.attn_implementation`: the checked-in `config/config.yaml` currently uses `"eager"` (avoids flash-attn dependency); `settings.py` still keeps `"flash_attention_2"` as the code-level fallback for `local_hf`
- `model.max_new_tokens`: the checked-in `config/config.yaml` currently uses `2048`; `settings.py` still keeps `512` as the code-level fallback
- `prompts.default_type`: `"extract_object_attributes_prompt"` (current default)
- `data.views`: maps logical view names to ordered lists of candidate filenames to try
- `--asset_list_file`: supported as a CLI override, not as a declared `data` config field. The file should contain one relative asset path per line, typically `category/asset_id`.

## Adding a New Prompt Type

1. Register the name in `SUPPORTED_PROMPT_TYPES` list in `core/prompt.py`
2. Add an `elif` branch in `PromptFactory.compose_user_prompt()` returning the prompt string
3. If the new prompt returns structured text needing field extraction, name it with `extract` or `json` in the type name (triggers `parse_structured_text_enhanced()` in the pipeline parsing branch)
4. Use via `--prompt_type my_new_prompt`

## Project Status

**Current State**: All annotations completed. Physical property defaults filled.

- **Total assets annotated**: 52,907 (50,091 original + 2,816 backfilled)
- **Parse success rate**: 100% (0 `raw_output` failures)
- **Description completion**: 100% (52,907/52,907)

Field completion rates (after default filling):
- description: 100%, material: 100%, mass: 100%, placement: 100%, dimensions: 100%

All 5 fields are 100% complete. Dimensions were filled using per-category median values from existing annotations.

The annotation pipeline is stable and all output files in `/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/output` contain valid parsed JSON data without `raw_output` fields.

---

## Agent Team Documentation Rule

Repository-wide agent documentation requirements live in `AGENTS.md`. In short: every behavior, command, runtime assumption, or operational status change must update the relevant maintained docs or a dated record under `docs/records/` using the filename pattern YYYY-MM-DD-topic.md before the task is treated as complete. Historical records under `docs/changes/` remain at their existing paths.
