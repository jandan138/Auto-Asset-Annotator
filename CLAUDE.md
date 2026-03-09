# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Important Constraints

**Do not run annotation commands** (commands that load and run the VLM) unless explicitly told to do so. The model is large (Qwen2.5-VL-7B-Instruct) and loading it is expensive.

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
# Basic run (uses config/config.yaml by default)
python -m auto_asset_annotator.main --input_dir /path/to/assets --output_dir /path/to/results

# Override prompt type
python -m auto_asset_annotator.main --prompt_type classify_object_category_prompt --input_dir /data/assets --output_dir /data/results

# Force re-annotation even if output already exists
python -m auto_asset_annotator.main --input_dir /data/assets --output_dir /data/results --force

# Re-annotate only assets with empty physical property fields
python -m auto_asset_annotator.main --input_dir /data/assets --output_dir /data/results --retry_incomplete

# Use a pre-built asset list file instead of scanning
python -m auto_asset_annotator.main --asset_list_file failed_assets.txt --output_dir ./output

# Distributed chunking (e.g., 4-machine parallel)
python -m auto_asset_annotator.main --num_chunks 4 --chunk_index 0  # machine 1
python -m auto_asset_annotator.main --num_chunks 4 --chunk_index 1  # machine 2
```

### Run tests
```bash
python -m pytest test_parser_robustness.py -v
# Or directly:
python test_parser_robustness.py
```

### Utility scripts
```bash
# Find successfully annotated assets (no "raw_output" field in JSON)
python scripts/find_success_assets.py --output_dir ./output --save_list success_assets.txt

# Find failed assets (has "raw_output" field indicating parse failure)
python scripts/find_failed_assets.py --output_dir ./output --save_list failed_assets.txt

# Find assets with incomplete/empty physical property fields
python scripts/find_incomplete_assets.py --output_dir ./output --save_list incomplete_assets.txt
python scripts/find_incomplete_assets.py --output_dir ./output --save_list incomplete_assets.txt --strict --stats

# Merge re-annotated results into existing annotations (selective field fill)
python scripts/merge_annotations.py --old_dir ./output --new_dir ./output_reannotate           # dry-run
python scripts/merge_annotations.py --old_dir ./output --new_dir ./output_reannotate --apply   # apply

# Fill empty physical properties with category-based defaults (material, mass, placement)
python scripts/fill_defaults.py --output_dir ./output --asset_list remaining_incomplete.txt           # dry-run
python scripts/fill_defaults.py --output_dir ./output --asset_list remaining_incomplete.txt --apply   # apply

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
# Submit 4 parallel workers for batch annotation
python scripts/dlc/submit_batch.py --total 4 --name my_annotation \
    --command_args "--input_dir /data/assets --output_dir /data/results"

# Submit with specific prompt type
python scripts/dlc/submit_batch.py --total 8 --name classify_task \
    --command_args "--input_dir /data/assets --output_dir /data/results --prompt_type classify_object_category_prompt"

# Retry failed assets with force flag
python scripts/dlc/submit_batch.py --total 4 --name retry_failed \
    --command_args "--input_dir /data/assets --output_dir /data/results --asset_list_file failed_assets.txt --force"

# Check DLC job status
./dlc get jobs
./dlc logs <job_id>
```

See [docs/dlc/README.md](docs/dlc/README.md) for complete DLC documentation.

## Architecture

The pipeline is a linear chain: **CLI → Config → ModelEngine → AnnotationPipeline → JSON output**.

```
src/auto_asset_annotator/
├── main.py              # Entry point: CLI parsing, asset listing, processing loop
├── config/
│   └── settings.py      # Dataclasses: Config, ModelConfig, DataConfig, ProcessingConfig, PromptConfig
├── core/
│   ├── model.py         # ModelEngine: loads Qwen2.5-VL via HuggingFace, runs inference
│   ├── pipeline.py      # AnnotationPipeline: orchestrates image discovery → prompt → inference → parsing
│   └── prompt.py        # PromptFactory: all prompt templates; SUPPORTED_PROMPT_TYPES list
└── utils/
    ├── file.py           # list_assets() scans dir tree; get_asset_images() resolves view patterns
    └── image.py          # Image loading and concatenation utilities
```

### Key data flow in `pipeline.py`

1. `get_asset_images()` resolves view patterns from `config.data.views` (e.g., `front: ["front.png", "0.png"]`), falling back to all sorted images in the asset directory if no named views are found.
2. `PromptFactory.compose_user_prompt()` selects the prompt template by `prompt_type`.
3. `ModelEngine.inference()` runs Qwen-VL with `process_vision_info()` from `qwen_vl_utils`.
4. For `extract_*` and `json`-named prompts, `parse_structured_text()` uses regex to extract key-value pairs (Category, Description, Material, Dimensions, Mass, Placement). On parse failure, `{"raw_output": <text>}` is saved.

### Retry behavior

In `main.py`, assets are automatically retried if:
- The output file doesn't exist
- The output file contains `"raw_output"` (indicating a previous parse failure)
- The `--force` flag is explicitly passed

This means you can re-run the same command to retry failed assets without needing to manually filter them.

### Output format

Each asset produces `{output_dir}/{category}/{asset_id}_annotation.json`:

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

`list_assets()` walks `input_dir` and returns relative paths of all leaf directories containing images.

## Configuration (`config/config.yaml`)

Key fields to know:
- `model.name`: absolute path to local model weights (current: `/cpfs/shared/simulation/zhuzihou/models/Qwen2.5-VL-7B-Instruct`)
- `model.attn_implementation`: `"eager"` (current, avoids flash-attn dependency) or `"flash_attention_2"` (faster)
- `model.max_new_tokens`: `2048` (current)
- `prompts.default_type`: `"extract_object_attributes_prompt"` (current default)
- `data.views`: maps logical view names to ordered lists of candidate filenames to try
- `data.asset_list_file`: optional path to a text file containing asset IDs to process (one per line)

## Adding a New Prompt Type

1. Register the name in `SUPPORTED_PROMPT_TYPES` list in `core/prompt.py`
2. Add an `elif` branch in `PromptFactory.compose_user_prompt()` returning the prompt string
3. If the new prompt returns structured text needing field extraction, name it with `extract` or `json` in the type name (triggers `parse_structured_text()` in pipeline)
4. Use via `--prompt_type my_new_prompt`

## Project Status

**Current State**: All annotations completed. Physical property defaults filled.

- **Total assets annotated**: 52,907 (50,091 original + 2,816 backfilled)
- **Parse success rate**: 100% (0 `raw_output` failures)
- **Description completion**: 100% (52,907/52,907)

Field completion rates (after default filling):
- description: 100%, material: 100%, mass: 100%, placement: 100%, dimensions: 96.4% (1,911 intentionally empty)

Dimensions are not filled with defaults because they are model-specific and cannot be generalized from category alone.

The annotation pipeline is stable and all output files in `/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/output` contain valid structured data without `raw_output` fields.

---

## Agent Team Documentation Rule (Mandatory)

**Every agent in a team MUST produce documentation for its work.** This is a hard requirement, not optional.

### What to document

Each agent must record the full lifecycle of its task:

1. **Research / Investigation** — what was explored, which files were read, what was discovered
2. **Design decisions** — why a particular approach was chosen, alternatives considered
3. **Code changes** — what was modified, added, or deleted, with file paths and brief rationale
4. **Testing** — what was tested, how it was tested, test commands run, and results
5. **Open issues** — known limitations, follow-up work needed, edge cases not covered

### Where to write

- Place docs under `docs/changes/YYYY-MM-DD_<topic>.md` for change logs
- Update `CLAUDE.md` if adding new commands or architectural changes
- Update relevant sections in existing docs

### How: agents with write permission

If the agent has file-write capability (Edit/Write tools), it **must write the documentation itself** before marking its task as completed.

### How: agents without write permission

If the agent is read-only (e.g., Explore, Plan agents), it **must send a message to the docs-writer agent** with:
- A structured summary of findings, decisions, and results
- Suggested file path and title for the documentation

### Enforcement

- Team leads must verify documentation exists before accepting a task as completed
- The version-commit-agent should check for corresponding documentation changes when committing code changes
