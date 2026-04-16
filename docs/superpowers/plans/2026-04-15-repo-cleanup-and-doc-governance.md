# Repository Cleanup And Documentation Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Clean the repository root by archiving historical run-list files and refresh all current and historical documentation so it matches the current codebase, directory layout, and project state.

**Architecture:** Execute the work in five passes: move root historical list files, rewrite all references to the new archive paths, refresh current operational docs, normalize historical change docs, and finish with repository-wide consistency checks. Treat `src/auto_asset_annotator/*.py` and `config/config.yaml` as the implementation source of truth, and use lightweight search/file checks instead of any model-loading annotation command.

**Tech Stack:** Markdown, Bash (`ls`, `mv`, `rg`, `git diff`), repository Python source as truth, `apply_patch` for edits.

---

## File Structure Map

### Files To Move

- `failed_assets.txt` -> `archive/temp_lists/failed_assets.txt`
- `incomplete_assets.txt` -> `archive/temp_lists/incomplete_assets.txt`
- `remaining_incomplete.txt` -> `archive/temp_lists/remaining_incomplete.txt`
- `verify_remaining.txt` -> `archive/temp_lists/verify_remaining.txt`
- `final_remaining.txt` -> `archive/temp_lists/final_remaining.txt`

### Root And Entry Docs To Modify

- `README.md` - top-level project entry doc; remove dead links and align the quick-start/current-status narrative with the current implementation.
- `CLAUDE.md` - repository workflow and architecture guidance; update command paths, current status, and behavior descriptions.

### Current Operational Docs To Modify

- `docs/introduction/overview.md`
- `docs/introduction/features.md`
- `docs/installation/requirements.md`
- `docs/installation/linux_deployment.md`
- `docs/usage/quick_start.md`
- `docs/usage/data_preparation.md`
- `docs/usage/configuration.md`
- `docs/usage/cli_reference.md`
- `docs/development/project_structure.md`
- `docs/development/extending_models.md`
- `docs/development/custom_prompts.md`
- `docs/guidebook/00_prologue.md`
- `docs/guidebook/01_the_workshop.md`
- `docs/guidebook/02_raw_materials.md`
- `docs/guidebook/03_first_spell.md`
- `docs/guidebook/04_alchemy.md`
- `docs/guidebook/05_mass_production.md`
- `docs/guidebook/10_architecture_deep_dive.md`
- `docs/guidebook/11_code_walkthrough.md`
- `docs/guidebook/12_prompt_engineering_mechanics.md`
- `docs/troubleshooting/common_issues.md`
- `docs/dlc/README.md`
- `docs/dlc/TESTING.md`
- `scripts/auto_caption/README.md`

### Historical Change Docs To Modify

- `docs/changes/PROJECT_PROGRESS.md`
- `docs/changes/2026-03-09_fill-dimensions-category-medians.md`
- `docs/changes/2026-03-09_fill-default-physical-properties.md`
- `docs/changes/2026-03-09_backfill-incomplete-physical-properties.md`
- `docs/changes/2026-03-09_annotation-validation-report.md`
- `docs/changes/2026-03-09_fix-42-null-descriptions.md`
- `docs/changes/2026-03-09_backfill-2816-missing-annotations.md`
- `docs/changes/2026-03-06_final_verification_report.md`
- `docs/changes/2026-03-06_stubborn_15_manual_completion.md`
- `docs/changes/2026-03-06_stubborn_assets_final_report.md`
- `docs/changes/2026-03-06_stubborn_15_final_report.md`
- `docs/changes/2026-03-06_stubborn_assets_rerun.md`
- `docs/changes/2026-03-05_dlc_migration.md`
- `docs/changes/2026-03-05_failed_annotations_summary.md`
- `docs/changes/2026-03-05_reannotation_script.md`
- `docs/changes/2026-03-05_parser_implementation.md`
- `docs/changes/2026-03-05_failed_annotations_analysis.md`
- `docs/changes/2026-03-05_rawoutput_patterns.md`
- `docs/changes/2026-03-05_pipeline_failure_analysis.md`
- `docs/changes/2026-03-05_batch_fix_execution.md`
- `docs/changes/2026-03-05_commit_summary.md`
- `docs/changes/2026-03-05_test_validation.md`
- `docs/changes/2026-03-05_data_analysis.md`

### Source-Of-Truth Files To Read While Editing Docs

- `src/auto_asset_annotator/main.py`
- `src/auto_asset_annotator/core/pipeline.py`
- `src/auto_asset_annotator/core/prompt.py`
- `src/auto_asset_annotator/core/model.py`
- `src/auto_asset_annotator/utils/file.py`
- `config/config.yaml`
- `pyproject.toml`

## Task 1: Inventory And Move Root Historical List Files

**Files:**
- Move: `failed_assets.txt`
- Move: `incomplete_assets.txt`
- Move: `remaining_incomplete.txt`
- Move: `verify_remaining.txt`
- Move: `final_remaining.txt`
- Verify destination exists: `archive/temp_lists/`
- Test: repository root inventory and archive contents checks

- [ ] **Step 1: Record the baseline root inventory**

Run:

```bash
ls "failed_assets.txt" "incomplete_assets.txt" "remaining_incomplete.txt" "verify_remaining.txt" "final_remaining.txt"
```

Expected: all five files are listed from the repository root.

- [ ] **Step 2: Record the baseline archive inventory**

Run:

```bash
ls "archive/temp_lists"
```

Expected: the directory already exists and contains older archived list files such as `stubborn_assets.txt` and `still_failed_assets.txt`.

- [ ] **Step 3: Move the five root list files into the archive directory**

Run:

```bash
mv "failed_assets.txt" "archive/temp_lists/failed_assets.txt"
mv "incomplete_assets.txt" "archive/temp_lists/incomplete_assets.txt"
mv "remaining_incomplete.txt" "archive/temp_lists/remaining_incomplete.txt"
mv "verify_remaining.txt" "archive/temp_lists/verify_remaining.txt"
mv "final_remaining.txt" "archive/temp_lists/final_remaining.txt"
```

Expected: each command succeeds without creating any new directory outside `archive/temp_lists/`.

- [ ] **Step 4: Verify the root is clean and the archive now contains the canonical copies**

Run:

```bash
ls "archive/temp_lists/failed_assets.txt" "archive/temp_lists/incomplete_assets.txt" "archive/temp_lists/remaining_incomplete.txt" "archive/temp_lists/verify_remaining.txt" "archive/temp_lists/final_remaining.txt"
```

Expected: all five archived files are listed from `archive/temp_lists/`.

- [ ] **Step 5: Verify that no stable root files were accidentally treated as cleanup targets**

Run:

```bash
ls "README.md" "CLAUDE.md" "pyproject.toml" "requirements.txt" "setup.py" "uv.lock"
```

Expected: all stable root files still exist at the repository root.

- [ ] **Step 6: Capture a review checkpoint without committing**

Run:

```bash
git diff --stat
```

Expected: only the five file moves appear at this stage. Do not create a commit unless the user explicitly asks for one.

### Task 2: Rewrite Repository-Wide References To The Moved List Files

**Files:**
- Modify: `CLAUDE.md`
- Modify: `docs/changes/2026-03-09_fill-dimensions-category-medians.md`
- Modify: `docs/changes/2026-03-09_fill-default-physical-properties.md`
- Modify: `docs/changes/2026-03-09_backfill-incomplete-physical-properties.md`
- Modify: `docs/changes/2026-03-05_failed_annotations_summary.md`
- Modify: `docs/changes/2026-03-05_reannotation_script.md`
- Modify: any additional file surfaced by the repository-wide search in Step 1
- Test: repository-wide grep checks for old root-path references

- [ ] **Step 1: Generate the exact hit list of old root-path references**

Run:

```bash
rg -n "failed_assets\.txt|incomplete_assets\.txt|remaining_incomplete\.txt|verify_remaining\.txt|final_remaining\.txt" "README.md" "CLAUDE.md" "docs" "scripts"
```

Expected: matches appear in `CLAUDE.md` and several `docs/changes/*.md` files.

- [ ] **Step 2: Apply the canonical path replacement map in every hit file**

Use this exact replacement map while editing:

```text
failed_assets.txt -> archive/temp_lists/failed_assets.txt
incomplete_assets.txt -> archive/temp_lists/incomplete_assets.txt
remaining_incomplete.txt -> archive/temp_lists/remaining_incomplete.txt
verify_remaining.txt -> archive/temp_lists/verify_remaining.txt
final_remaining.txt -> archive/temp_lists/final_remaining.txt
```

Expected: every operational or historical command example now points at the archived location instead of the repository root.

- [ ] **Step 3: Keep unrelated list files unchanged**

Do not rewrite references to list files that were not moved in Task 1. Preserve paths such as:

```text
scripts/missing_assets_20260309.txt
archive/temp_lists/still_failed_assets.txt
archive/temp_lists/stubborn_assets.txt
```

Expected: only the five canonical moved files change path.

- [ ] **Step 4: Re-run the repository-wide search and inspect the remaining matches**

Run:

```bash
rg -n "failed_assets\.txt|incomplete_assets\.txt|remaining_incomplete\.txt|verify_remaining\.txt|final_remaining\.txt" "README.md" "CLAUDE.md" "docs" "scripts"
```

Expected: every remaining match includes `archive/temp_lists/` in the same line, or the line is clearly discussing the filename as a historical artifact rather than showing a stale path.

- [ ] **Step 5: Capture a review checkpoint without committing**

Run:

```bash
git diff --stat
```

Expected: the diff now includes the file moves plus path updates in `CLAUDE.md` and `docs/changes/*.md`. Do not create a commit unless the user explicitly asks for one.

### Task 3: Refresh Root Entry Docs (`README.md` And `CLAUDE.md`)

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Read for truth: `src/auto_asset_annotator/main.py`
- Read for truth: `src/auto_asset_annotator/core/pipeline.py`
- Read for truth: `src/auto_asset_annotator/core/prompt.py`
- Read for truth: `config/config.yaml`
- Test: targeted grep checks for dead links and behavior terms

- [ ] **Step 1: Capture the mismatches that must be fixed in the entry docs**

Run:

```bash
rg -n "README_EN|JSON|structured text|asset_list_file|retry_incomplete|failed_assets\.txt|remaining_incomplete\.txt" "README.md" "CLAUDE.md"
```

Expected: `README.md` shows the missing `README_EN.md` link, and `CLAUDE.md` shows path references that now need the archive location.

- [ ] **Step 2: Rewrite `README.md` as a current-state entry document**

Ensure `README.md` contains these exact ideas after editing:

````markdown
## Current Status
- Total assets annotated: 52,907
- Structured annotation fields are complete at 100%
- `output/` contains the stable structured results

## Quick Start
```bash
pip install -r requirements.txt
pip install -e .
python -m auto_asset_annotator.main --input_dir /path/to/assets --output_dir /path/to/results
```

## Output Behavior
The attribute-extraction prompt asks the model for structured text.
`AnnotationPipeline` parses that structured text and writes JSON files to the output directory.
````

Also remove the dead `README_EN.md` link unless you create that file in the same task. Since this plan does not create `README_EN.md`, the correct action is to remove the dead link.

- [ ] **Step 3: Rewrite `CLAUDE.md` so it matches the current code and archive paths**

Ensure `CLAUDE.md` reflects all of the following after editing:

```markdown
- Do not run annotation commands unless explicitly asked.
- `--asset_list_file` examples use `archive/temp_lists/...` for the five moved lists.
- The pipeline saves JSON output after parsing structured text from the model.
- `--retry_incomplete` is documented as a current supported flag.
- The current project status is the completed 52,907-asset state.
```

Keep the existing repository-specific operational constraints intact while updating only the stale paths, stale status framing, and stale output-format wording.

- [ ] **Step 4: Verify the entry docs no longer contain important dead links or stale path references**

Run:

```bash
rg -n "README_EN|failed_assets\.txt|incomplete_assets\.txt|remaining_incomplete\.txt|verify_remaining\.txt|final_remaining\.txt" "README.md" "CLAUDE.md"
```

Expected: `README_EN` no longer appears in `README.md`, and any moved list reference in either file includes `archive/temp_lists/`.

- [ ] **Step 5: Verify the entry docs describe the current behavior rather than outdated JSON-generation language**

Run:

```bash
rg -n "structured text|JSON" "README.md" "CLAUDE.md"
```

Expected: `README.md` and `CLAUDE.md` describe the flow as “model returns structured text, pipeline writes JSON after parsing.”

- [ ] **Step 6: Capture a review checkpoint without committing**

Run:

```bash
git diff -- "README.md" "CLAUDE.md"
```

Expected: the diff is limited to entry-doc refreshes, dead-link cleanup, and archive-path updates. Do not create a commit unless the user explicitly asks for one.

### Task 4: Refresh Current User-Facing Operational Docs

**Files:**
- Modify: `docs/introduction/overview.md`
- Modify: `docs/introduction/features.md`
- Modify: `docs/installation/requirements.md`
- Modify: `docs/installation/linux_deployment.md`
- Modify: `docs/usage/quick_start.md`
- Modify: `docs/usage/data_preparation.md`
- Modify: `docs/usage/configuration.md`
- Modify: `docs/usage/cli_reference.md`
- Read for truth: `pyproject.toml`
- Read for truth: `src/auto_asset_annotator/main.py`
- Read for truth: `src/auto_asset_annotator/core/pipeline.py`
- Read for truth: `src/auto_asset_annotator/core/prompt.py`
- Read for truth: `src/auto_asset_annotator/utils/file.py`
- Read for truth: `config/config.yaml`
- Test: grep checks for current flags, prompt behavior, and output wording

- [ ] **Step 1: Re-read the source-of-truth files for user-facing behavior**

Read these files before editing any user-facing docs:

```text
pyproject.toml
src/auto_asset_annotator/main.py
src/auto_asset_annotator/core/pipeline.py
src/auto_asset_annotator/core/prompt.py
src/auto_asset_annotator/utils/file.py
config/config.yaml
```

Expected: you have exact confirmation of Python version, supported flags, prompt behavior, output layout, and asset discovery logic.

- [ ] **Step 2: Rewrite the introduction docs to match the current pipeline and output behavior**

Apply these exact corrections:

```markdown
docs/introduction/overview.md
- describe the pipeline as CLI -> Config -> ModelEngine -> AnnotationPipeline -> JSON output
- state that parsing happens in code, not by trusting direct JSON from the model

docs/introduction/features.md
- change extract-object-attributes wording from "model outputs strict JSON" to "model returns structured text that the pipeline parses into JSON"
- keep prompt-type coverage aligned with `SUPPORTED_PROMPT_TYPES`
```

- [ ] **Step 3: Rewrite the installation docs to reflect the current install surface**

Apply these exact corrections:

```markdown
docs/installation/requirements.md
- Python requirement: >=3.10
- dependencies should match `pyproject.toml` and `requirements.txt`

docs/installation/linux_deployment.md
- show `pip install -r requirements.txt`
- show `pip install -e .`
- keep model download and environment notes separate from standard install
```

- [ ] **Step 4: Rewrite the usage docs to match the current CLI and path conventions**

Apply these exact corrections:

```markdown
docs/usage/quick_start.md
- default annotation command
- note that output JSON is produced by parsing structured text

docs/usage/data_preparation.md
- document the expected asset directory shape
- document the output layout `{output_dir}/{category}/{asset_id}_annotation.json`

docs/usage/configuration.md
- document `model.name`, `device_map`, `dtype`, `attn_implementation`, `temperature`, `max_new_tokens`
- document `data.views`, `use_thumbnails_dir`, `thumbnails_dir_name`
- document `prompts.default_type`

docs/usage/cli_reference.md
- include `--asset_list_file`
- include `--force`
- include `--retry_incomplete`
- include `--num_chunks` and `--chunk_index`
```

- [ ] **Step 5: Verify that the user-facing docs now mention the current supported flags and output behavior**

Run:

```bash
rg -n "asset_list_file|retry_incomplete|force|structured text|JSON output|chunk_index|num_chunks" "docs/introduction" "docs/installation" "docs/usage"
```

Expected: the results show current flag coverage and the “structured text parsed into JSON output” wording across the user-facing docs.

- [ ] **Step 6: Capture a review checkpoint without committing**

Run:

```bash
git diff -- "docs/introduction" "docs/installation" "docs/usage"
```

Expected: the diff is limited to content refreshes that align those docs with current code behavior. Do not create a commit unless the user explicitly asks for one.

### Task 5: Refresh Developer, Guidebook, Troubleshooting, And DLC Docs

**Files:**
- Modify: `docs/development/project_structure.md`
- Modify: `docs/development/extending_models.md`
- Modify: `docs/development/custom_prompts.md`
- Modify: `docs/guidebook/00_prologue.md`
- Modify: `docs/guidebook/01_the_workshop.md`
- Modify: `docs/guidebook/02_raw_materials.md`
- Modify: `docs/guidebook/03_first_spell.md`
- Modify: `docs/guidebook/04_alchemy.md`
- Modify: `docs/guidebook/05_mass_production.md`
- Modify: `docs/guidebook/10_architecture_deep_dive.md`
- Modify: `docs/guidebook/11_code_walkthrough.md`
- Modify: `docs/guidebook/12_prompt_engineering_mechanics.md`
- Modify: `docs/troubleshooting/common_issues.md`
- Modify: `docs/dlc/README.md`
- Modify: `docs/dlc/TESTING.md`
- Modify: `scripts/auto_caption/README.md`
- Read for truth: `src/auto_asset_annotator/main.py`
- Read for truth: `src/auto_asset_annotator/core/pipeline.py`
- Read for truth: `src/auto_asset_annotator/core/prompt.py`
- Read for truth: `src/auto_asset_annotator/core/model.py`
- Read for truth: `config/config.yaml`
- Test: grep checks for stale output wording and moved archive paths

- [ ] **Step 1: Refresh the development docs against the current source layout and pipeline responsibilities**

Apply these exact corrections:

```markdown
docs/development/project_structure.md
- match the current files under `src/auto_asset_annotator/`
- describe `main.py`, `core/pipeline.py`, `core/model.py`, `core/prompt.py`, `utils/file.py`, `utils/image.py`

docs/development/extending_models.md
- explain how model loading currently works in `core/model.py`
- distinguish Qwen2.5-VL-first behavior from optional fallback paths

docs/development/custom_prompts.md
- document `SUPPORTED_PROMPT_TYPES`
- document that `extract`/`json`-named prompts trigger parsing in the pipeline
```

- [ ] **Step 2: Refresh the guidebook docs so the narrative still matches the current repository state**

Apply these exact corrections:

```markdown
- keep the existing guidebook tone
- remove or rewrite any wording that implies the project is still mid-build
- align architecture descriptions with the current code
- align production-scale notes with the completed 52,907-asset outcome
- align prompt/output explanations with the structured-text -> parser -> JSON flow
```

- [ ] **Step 3: Refresh troubleshooting and DLC docs to use current commands and archived list paths**

Apply these exact corrections:

```markdown
docs/troubleshooting/common_issues.md
- reflect the current retry flags and archive list paths
- separate normal usage issues from historical repair workflows

docs/dlc/README.md
- keep `docs/dlc/README.md` focused on current DLC submission flow
- update any moved list path examples to `archive/temp_lists/...`
- preserve the chunking explanation that maps to `--num_chunks` and `--chunk_index`

docs/dlc/TESTING.md
- align local/DLC testing notes with the current scripts and paths
```

- [ ] **Step 4: Clarify the role of `scripts/auto_caption/README.md` relative to the main pipeline**

After editing, that README must make this distinction explicit:

```markdown
- `scripts/auto_caption/` is a separate utility area
- the primary maintained annotation flow lives under `src/auto_asset_annotator/`
- readers should not confuse the auto-caption scripts with the main production pipeline entrypoint
```

- [ ] **Step 5: Verify the developer/operator docs no longer use stale wording or stale list paths**

Run:

```bash
rg -n "failed_assets\.txt|incomplete_assets\.txt|remaining_incomplete\.txt|verify_remaining\.txt|final_remaining\.txt|strict JSON|structured text" "docs/development" "docs/guidebook" "docs/troubleshooting" "docs/dlc" "scripts/auto_caption/README.md"
```

Expected: any moved-list reference now includes `archive/temp_lists/`, and output-format wording matches the structured-text parsing flow.

- [ ] **Step 6: Capture a review checkpoint without committing**

Run:

```bash
git diff -- "docs/development" "docs/guidebook" "docs/troubleshooting" "docs/dlc" "scripts/auto_caption/README.md"
```

Expected: the diff shows content alignment work only. Do not create a commit unless the user explicitly asks for one.

### Task 6: Normalize Historical Change Docs Into Clean Historical Records

**Files:**
- Modify: `docs/changes/PROJECT_PROGRESS.md`
- Modify: `docs/changes/2026-03-09_fill-dimensions-category-medians.md`
- Modify: `docs/changes/2026-03-09_fill-default-physical-properties.md`
- Modify: `docs/changes/2026-03-09_backfill-incomplete-physical-properties.md`
- Modify: `docs/changes/2026-03-09_annotation-validation-report.md`
- Modify: `docs/changes/2026-03-09_fix-42-null-descriptions.md`
- Modify: `docs/changes/2026-03-09_backfill-2816-missing-annotations.md`
- Modify: `docs/changes/2026-03-06_final_verification_report.md`
- Modify: `docs/changes/2026-03-06_stubborn_15_manual_completion.md`
- Modify: `docs/changes/2026-03-06_stubborn_assets_final_report.md`
- Modify: `docs/changes/2026-03-06_stubborn_15_final_report.md`
- Modify: `docs/changes/2026-03-06_stubborn_assets_rerun.md`
- Modify: `docs/changes/2026-03-05_dlc_migration.md`
- Modify: `docs/changes/2026-03-05_failed_annotations_summary.md`
- Modify: `docs/changes/2026-03-05_reannotation_script.md`
- Modify: `docs/changes/2026-03-05_parser_implementation.md`
- Modify: `docs/changes/2026-03-05_failed_annotations_analysis.md`
- Modify: `docs/changes/2026-03-05_rawoutput_patterns.md`
- Modify: `docs/changes/2026-03-05_pipeline_failure_analysis.md`
- Modify: `docs/changes/2026-03-05_batch_fix_execution.md`
- Modify: `docs/changes/2026-03-05_commit_summary.md`
- Modify: `docs/changes/2026-03-05_test_validation.md`
- Modify: `docs/changes/2026-03-05_data_analysis.md`
- Test: repository-wide grep checks limited to `docs/changes`

- [ ] **Step 1: Apply a single historical-document structure to every change log file**

Use this exact section pattern wherever it improves the document without erasing dated facts:

```markdown
## Date / Phase
## Context
## What Changed
## Result
## Current Relevance
```

Expected: every historical doc clearly reads as a dated record rather than as current operational guidance.

- [ ] **Step 2: Preserve dated facts while correcting stale paths and command examples**

Apply these exact rules while editing every file in `docs/changes/`:

```markdown
- keep original dates
- keep original counts, outcomes, and event chronology
- replace the five moved root-list paths with `archive/temp_lists/...`
- keep `scripts/missing_assets_20260309.txt` unchanged because it was not moved
- keep archived historical list paths under `archive/temp_lists/` unchanged when already correct
```

- [ ] **Step 3: Add current-relevance framing to the progress and milestone documents**

Ensure these files explicitly distinguish history from present-day status:

```markdown
docs/changes/PROJECT_PROGRESS.md
docs/changes/2026-03-06_final_verification_report.md
docs/changes/2026-03-09_annotation-validation-report.md
```

Each of those files should end with a short current-relevance note that explains whether the document is still operational guidance or a historical record only.

- [ ] **Step 4: Verify that the historical docs no longer contain stale root-path references**

Run:

```bash
rg -n "failed_assets\.txt|incomplete_assets\.txt|remaining_incomplete\.txt|verify_remaining\.txt|final_remaining\.txt" "docs/changes"
```

Expected: any remaining match in `docs/changes` includes `archive/temp_lists/` on the same line, or is part of an explicit filename discussion rather than an outdated command path.

- [ ] **Step 5: Capture a review checkpoint without committing**

Run:

```bash
git diff -- "docs/changes"
```

Expected: the diff preserves historical meaning while making structure, path references, and current-relevance framing cleaner. Do not create a commit unless the user explicitly asks for one.

### Task 7: Run Final Repository-Wide Verification And Prepare Handoff

**Files:**
- Verify: `README.md`
- Verify: `CLAUDE.md`
- Verify: `docs/introduction/overview.md`
- Verify: `docs/usage/quick_start.md`
- Verify: `docs/development/project_structure.md`
- Verify: `docs/dlc/README.md`
- Verify: `docs/changes/PROJECT_PROGRESS.md`
- Verify archived files: `archive/temp_lists/*.txt`
- Test: repository-wide grep, file existence, and diff review commands

- [ ] **Step 1: Verify the five target list files no longer exist at the repository root**

Run:

```bash
ls "failed_assets.txt" "incomplete_assets.txt" "remaining_incomplete.txt" "verify_remaining.txt" "final_remaining.txt"
```

Expected: the command fails with “No such file or directory” for each file because they were moved to `archive/temp_lists/`.

- [ ] **Step 2: Verify the archived canonical copies exist**

Run:

```bash
ls "archive/temp_lists/failed_assets.txt" "archive/temp_lists/incomplete_assets.txt" "archive/temp_lists/remaining_incomplete.txt" "archive/temp_lists/verify_remaining.txt" "archive/temp_lists/final_remaining.txt"
```

Expected: all five files exist under `archive/temp_lists/`.

- [ ] **Step 3: Verify there are no important dead internal markdown links left in the key entry docs**

Run:

```bash
rg -n "\]\(([^)#]+)\)" "README.md" "docs/introduction/overview.md" "docs/usage/quick_start.md" "docs/development/project_structure.md" "docs/dlc/README.md"
```

Then manually verify that each target from those five docs exists in the repository. At minimum, these paths must exist:

```bash
ls "docs/introduction/overview.md" "docs/introduction/features.md" "docs/installation/linux_deployment.md" "docs/usage/quick_start.md" "docs/usage/data_preparation.md" "docs/usage/configuration.md" "docs/usage/cli_reference.md" "docs/development/project_structure.md" "docs/development/custom_prompts.md" "docs/development/extending_models.md" "docs/troubleshooting/common_issues.md"
```

Expected: no key entry doc points at a missing repository file.

- [ ] **Step 4: Verify repository-wide path consistency for the moved list files**

Run:

```bash
rg -n "failed_assets\.txt|incomplete_assets\.txt|remaining_incomplete\.txt|verify_remaining\.txt|final_remaining\.txt" "README.md" "CLAUDE.md" "docs" "scripts"
```

Expected: every operational path reference uses `archive/temp_lists/...`.

- [ ] **Step 5: Verify the current docs agree on the structured-text parsing flow**

Run:

```bash
rg -n "structured text|JSON output|parses.*JSON|writes JSON" "README.md" "CLAUDE.md" "docs/introduction" "docs/usage" "docs/development" "docs/guidebook"
```

Expected: the current docs consistently describe the flow as “model returns structured text; pipeline parses it and writes JSON output.”

- [ ] **Step 6: Review the full change set and stop for user review**

Run:

```bash
git diff --stat
git diff
```

Expected: the final diff shows only root file moves and documentation changes. Stop here and ask the user whether they want any revisions before any commit-related action.

## Self-Review Checklist

- [ ] Spec coverage check: Tasks 1-2 cover root cleanup and moved-path updates; Tasks 3-5 cover all current operational docs named in the spec; Task 6 covers every `docs/changes/*.md` file; Task 7 covers verification, dead links, and acceptance checks.
- [ ] Draft-marker scan: search this plan for banned drafting markers and remove any accidental match before execution.
- [ ] Consistency check: keep the five moved canonical paths identical in every task; preserve `scripts/missing_assets_20260309.txt` as an unchanged path; do not treat `requirements.txt` as a cleanup candidate.

## Notes For The Implementer

- Use `apply_patch` for all manual markdown edits.
- Do not run `python -m auto_asset_annotator.main` or any other command that would load the VLM unless the user explicitly asks.
- Do not create a git commit unless the user explicitly asks for one.
