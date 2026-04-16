# Repo Cleanup And Doc Governance Execution

## Task 1: Inventory and move root historical list files

### Research / Investigation

- Checked the main workspace root and confirmed the five historical list files existed there: `failed_assets.txt`, `incomplete_assets.txt`, `remaining_incomplete.txt`, `verify_remaining.txt`, and `final_remaining.txt`.
- Checked `archive/` and confirmed `archive/temp_lists/` already existed in the main workspace.
- Confirmed Task 1 includes the `.gitignore` update for `.worktrees/`; that entry originated from the controller-approved worktree setup prerequisite and is part of the final workspace diff for this task.
- Confirmed this task needed to execute in the main workspace rather than the git worktree because these runtime artifact files are ignored/untracked and therefore were not present in the worktree.

### Design decisions

- Kept the change minimal: include the controller-approved `.worktrees/` `.gitignore` safety entry in the Task 1 change set, add path-specific unignore rules only for the five canonical archived files, and move only the specified runtime artifact files.
- Used the existing `archive/temp_lists/` destination instead of creating any new archive layout.
- Wrote the task record into the shared execution log file required by repository policy.

### Code changes

- Moved `failed_assets.txt` to `archive/temp_lists/failed_assets.txt`.
- Moved `incomplete_assets.txt` to `archive/temp_lists/incomplete_assets.txt`.
- Moved `remaining_incomplete.txt` to `archive/temp_lists/remaining_incomplete.txt`.
- Moved `verify_remaining.txt` to `archive/temp_lists/verify_remaining.txt`.
- Moved `final_remaining.txt` to `archive/temp_lists/final_remaining.txt`.
- Updated `.gitignore` to keep `.worktrees/` ignored and to explicitly unignore only these five canonical archived files so they can be versioned:
  `archive/temp_lists/failed_assets.txt`, `archive/temp_lists/incomplete_assets.txt`, `archive/temp_lists/remaining_incomplete.txt`, `archive/temp_lists/verify_remaining.txt`, and `archive/temp_lists/final_remaining.txt`.
- Added this shared execution log file at `docs/changes/2026-04-15_repo-cleanup-and-doc-governance-execution.md`.

### Testing / verification commands and results

- `ls`
  Result: confirmed the five source files were present at the repository root before the move.
- `ls archive && ls archive/temp_lists`
  Result: confirmed `archive/temp_lists/` existed before the move.
- `ls archive/temp_lists/failed_assets.txt archive/temp_lists/incomplete_assets.txt archive/temp_lists/remaining_incomplete.txt archive/temp_lists/verify_remaining.txt archive/temp_lists/final_remaining.txt`
  Result: command example now reflects the canonical archived locations for the five moved list files.
- `mv "failed_assets.txt" "archive/temp_lists/failed_assets.txt" && mv "incomplete_assets.txt" "archive/temp_lists/incomplete_assets.txt" && mv "remaining_incomplete.txt" "archive/temp_lists/remaining_incomplete.txt" && mv "verify_remaining.txt" "archive/temp_lists/verify_remaining.txt" && mv "final_remaining.txt" "archive/temp_lists/final_remaining.txt"`
  Result: completed successfully.
- `ls archive/temp_lists/failed_assets.txt archive/temp_lists/incomplete_assets.txt archive/temp_lists/remaining_incomplete.txt archive/temp_lists/verify_remaining.txt archive/temp_lists/final_remaining.txt`
  Result: confirmed all five files existed in the archive destination after the move.
- `ls README.md CLAUDE.md pyproject.toml requirements.txt setup.py uv.lock`
  Result: confirmed the stable root files remained in place.
- `ls archive/temp_lists/failed_assets.txt archive/temp_lists/incomplete_assets.txt archive/temp_lists/remaining_incomplete.txt archive/temp_lists/verify_remaining.txt archive/temp_lists/final_remaining.txt`
  Result: confirmed all five canonical archived paths resolve after the move.
- `git check-ignore -v archive/temp_lists/failed_assets.txt archive/temp_lists/incomplete_assets.txt archive/temp_lists/remaining_incomplete.txt archive/temp_lists/verify_remaining.txt archive/temp_lists/final_remaining.txt`
  Result: before the `.gitignore` fix, all five canonical archived files still matched ignore patterns; after the fix, they are no longer ignored.
- `git check-ignore -v archive/temp_lists/still_failed_assets.txt archive/temp_lists/stubborn_assets.txt archive/temp_lists/success_assets_temp.txt`
  Result: unrelated historical archive files still match the existing ignore patterns and remain ignored.

### Open issues

- None for Task 1 after the `.gitignore` fix.

## Task 2: Rewrite repository-wide references to the moved list files

### Research / Investigation

- Searched `README.md`, `CLAUDE.md`, `docs`, and `scripts` for references to `failed_assets.txt`, `incomplete_assets.txt`, `remaining_incomplete.txt`, `verify_remaining.txt`, and `final_remaining.txt`.
- Confirmed `README.md` had no matching references.
- Confirmed the operational and historical path updates were needed in `CLAUDE.md`, `docs/changes/2026-03-09_fill-dimensions-category-medians.md`, `docs/changes/2026-03-09_fill-default-physical-properties.md`, `docs/changes/2026-03-09_backfill-incomplete-physical-properties.md`, `docs/changes/2026-03-05_failed_annotations_summary.md`, `docs/changes/2026-03-05_reannotation_script.md`, `scripts/fill_defaults.py`, `scripts/find_incomplete_assets.py`, `scripts/reannotate_failures.py`, and `scripts/find_failed_assets.py`.
- Confirmed the search also hit `docs/superpowers/**` planning/spec files and this shared execution log; per task instructions, the planning/spec files were left untouched, and the execution log needed follow-up cleanup so surfaced command examples also use the canonical archived paths.
- Confirmed unrelated paths such as `archive/temp_lists/still_failed_assets.txt`, `archive/temp_lists/stubborn_assets.txt`, and `scripts/missing_assets_20260309.txt` were not part of the replacement set.

### Design decisions

- Kept the task path-rewrite-only: updated only the surfaced non-plan files and only the references for the five moved canonical list files.
- Updated both documentation examples and script-level default/help/example strings where those references still pointed to the repository root, so current usage now matches the archived layout.
- Kept historical narrative context where needed, but rewrote surfaced command examples in this execution log to use the canonical archived paths.

### Code changes

- Updated `CLAUDE.md` command examples to use `archive/temp_lists/failed_assets.txt`, `archive/temp_lists/incomplete_assets.txt`, and `archive/temp_lists/remaining_incomplete.txt`.
- Updated `docs/changes/2026-03-09_fill-dimensions-category-medians.md` to use `archive/temp_lists/final_remaining.txt` in the recorded `fill_defaults.py` command.
- Updated `docs/changes/2026-03-09_fill-default-physical-properties.md` to use `archive/temp_lists/remaining_incomplete.txt` in both `fill_defaults.py` examples.
- Updated `docs/changes/2026-03-09_backfill-incomplete-physical-properties.md` to use `archive/temp_lists/incomplete_assets.txt` in the DLC submission example.
- Updated `docs/changes/2026-03-05_failed_annotations_summary.md` and `docs/changes/2026-03-05_reannotation_script.md` to use `archive/temp_lists/failed_assets.txt` in retry-list examples.
- Updated `scripts/fill_defaults.py` docstring usage examples to use `archive/temp_lists/remaining_incomplete.txt`.
- Updated `scripts/find_incomplete_assets.py` default `--save_list` value and help text to `archive/temp_lists/incomplete_assets.txt`.
- Updated `scripts/reannotate_failures.py` usage examples and printed follow-up command to use `archive/temp_lists/failed_assets.txt`.
- Updated `scripts/find_failed_assets.py` default `--save_list` value to `archive/temp_lists/failed_assets.txt`.
- Updated this execution log so surfaced command examples use `archive/temp_lists/` paths instead of root-level paths.

### Testing / verification commands and results

- `rg -n "failed_assets\.txt|incomplete_assets\.txt|remaining_incomplete\.txt|verify_remaining\.txt|final_remaining\.txt" "README.md" "CLAUDE.md" "docs" "scripts"`
  Result: initial search surfaced the expected task files plus `docs/superpowers/**` plan/spec records and historical Task 1 entries in this execution log.
- `rg -n "failed_assets\.txt|incomplete_assets\.txt|remaining_incomplete\.txt|verify_remaining\.txt|final_remaining\.txt" "README.md" "CLAUDE.md" "docs" "scripts"`
  Result: after the edits, remaining matches in the task scope were either `archive/temp_lists/...` paths or non-command historical references; no stale root-path command examples remained in the edited files.
- `git diff --stat`
  Result: confirmed the workspace diff includes the expected Task 2 documentation/script path rewrites along with the pre-existing Task 1 file-move changes; no commit was created.

### Open issues

- None for Task 2.

## Task 3: Refresh root entry docs

### Research / Investigation

- Read the Task 3 section in `docs/superpowers/plans/2026-04-15-repo-cleanup-and-doc-governance.md` and confirmed the scope is limited to `README.md`, `CLAUDE.md`, and this shared execution log.
- Read `src/auto_asset_annotator/main.py` and confirmed the CLI supports `--asset_list_file`, `--force`, `--retry_incomplete`, `--num_chunks`, and `--chunk_index`, and that `main.py` writes JSON files after `AnnotationPipeline.process_asset()` returns parsed results.
- Read `src/auto_asset_annotator/core/pipeline.py` and confirmed `extract_*` prompts are handled as structured text that is parsed by `parse_structured_text_enhanced()`, normalized, and returned as dictionaries; parse failures are saved as `raw_output`.
- Read `src/auto_asset_annotator/core/prompt.py` and confirmed `extract_object_attributes_prompt` explicitly asks the model to return structured text with headers and to avoid JSON formatting.
- Read `config/config.yaml` and confirmed the default prompt is `extract_object_attributes_prompt` and the current model path/config values reflect the Qwen2.5-VL setup.
- Read `pyproject.toml` and confirmed the package metadata still points at `README.md` and requires Python `>=3.10`.
- Read the existing `README.md` and confirmed it still contained a dead `README_EN.md` link and did not describe the current completed project state or the structured-text-to-JSON pipeline behavior.
- Read the existing `CLAUDE.md` and confirmed its operational constraints were still valid, but the entry wording needed to be refreshed so the docs describe parsed structured text output rather than implying direct JSON generation.

### Design decisions

- Kept the change set narrow: only refreshed the two root entry docs plus this execution log, as required.
- Rewrote `README.md` into a concise current-state entry document instead of preserving the older index-style landing page, because Task 3 explicitly called for a current-state entry doc.
- Preserved the repository-specific operational warning in `CLAUDE.md` not to run annotation/model-loading commands unless explicitly asked.
- Updated behavior wording to match the code precisely: the model is prompted for structured text, the pipeline parses it, and `main.py` writes JSON files.

### Code changes

- Rewrote `README.md` to remove the dead `README_EN.md` link, add the completed-project status (`52,907` assets and 100% field completion), provide quick-start install/run commands, and describe the structured-text parsing flow and output layout.
- Updated `README.md` usage examples to use the canonical archived list path `archive/temp_lists/failed_assets.txt` and to surface the supported `--retry_incomplete` flag.
- Removed the unsupported `## License` / `MIT` claim from `README.md` because the repository currently has no `LICENSE` file and the package metadata does not declare a license.
- Updated `CLAUDE.md` architecture and output wording so it now describes parsed JSON output and explicitly states that `main.py` writes JSON after `parse_structured_text_enhanced()` processes model output.
- Updated `CLAUDE.md` retry behavior to include the current `--retry_incomplete` path through `main.py`.
- Fixed the missing closing code fence in the `CLAUDE.md` failure-output example while keeping the surrounding operational guidance intact.

### Testing / verification commands and results

- `ls "LICENSE"`
  Result: confirmed there is no repository `LICENSE` file, so the old README license claim was not backed by a tracked file.
- `git grep -n -E 'README_EN|failed_assets\.txt|incomplete_assets\.txt|remaining_incomplete\.txt|verify_remaining\.txt|final_remaining\.txt' -- README.md CLAUDE.md`
  Result: after the edits, `README_EN` no longer appears, and every remaining moved-list reference in the entry docs uses `archive/temp_lists/...`.
- `git grep -n -E 'structured text|JSON' -- README.md CLAUDE.md`
  Result: both entry docs now describe the current behavior as structured text from the model followed by JSON output written by the pipeline/main flow.
- `git grep -n -E '^## License$|^MIT$' -- README.md`
  Result: confirmed the unsupported README license claim has been removed.
- `ls "docs/introduction/overview.md" "docs/installation/linux_deployment.md" "docs/usage/quick_start.md" "docs/usage/cli_reference.md" "docs/development/project_structure.md" "docs/troubleshooting/common_issues.md" "docs/dlc/README.md"`
  Result: confirmed the important root-level doc targets referenced from the refreshed entry docs still exist.
- `git diff -- "README.md" "CLAUDE.md" "docs/changes/2026-04-15_repo-cleanup-and-doc-governance-execution.md"`
  Result: confirmed the diff is limited to the two entry docs plus the Task 3 execution-log append; no commit was created.

### Open issues

- None for Task 3.

## Task 4: Refresh current user-facing operational docs

### Research / Investigation

- Read the Task 4 scope in `docs/superpowers/plans/2026-04-15-repo-cleanup-and-doc-governance.md` and confirmed the edit set is limited to eight operational docs plus this shared execution log.
- Read `pyproject.toml` and confirmed the package requires Python `>=3.10` and currently declares these install-surface dependencies: `transformers`, `torch`, `torchvision`, `pillow`, `natsort`, `tqdm`, `qwen-vl-utils`, `pyyaml`, and `accelerate`.
- Read `src/auto_asset_annotator/main.py` and confirmed the active CLI includes `--asset_list_file`, `--force`, `--retry_incomplete`, `--num_chunks`, and `--chunk_index`, and that output files are written by `main.py` after pipeline processing.
- Read `src/auto_asset_annotator/core/pipeline.py` and confirmed attribute extraction works by parsing model-returned structured text in code via `parse_structured_text_enhanced()` rather than trusting direct JSON from the model.
- Read `src/auto_asset_annotator/core/prompt.py` and confirmed `SUPPORTED_PROMPT_TYPES` currently lists nine prompt-type names, while `extract_object_attributes_prompt` explicitly instructs the model to avoid JSON and return structured text with headers.
- Follow-up review identified that `docs/introduction/features.md` still read too strongly for several registry-listed background/polish/QA prompt names. Re-checking `PromptFactory.compose_user_prompt()` confirmed the main concrete branches are `find_canonical_front_view_prompt`, `is_symmetric_object_prompt`, `classify_object_category_prompt`, `extract_object_attributes_prompt`, `describe_object_prompt_MMScan`, and one specialized `classify_object_category_with_background_prompt` path; the other listed names should not be presented as equally mature end-to-end features.
- Read `src/auto_asset_annotator/utils/file.py` and confirmed the expected input shape is category directories containing asset leaf directories with image files, with a fallback that scans all `.png`, `.jpg`, and `.jpeg` files when named views are not found.
- Read `config/config.yaml` and confirmed the current model, data, processing, and prompt defaults that the docs needed to reflect.
- Read the existing eight target docs and confirmed they contained stale claims about strict model JSON output, outdated install requirements, incomplete CLI coverage, and incomplete data-layout/configuration details.

### Design decisions

- Kept the change set narrowly scoped to the eight requested operational docs plus this shared execution log.
- Rewrote the operational pages to reflect current behavior exactly as implemented in `main.py`, `pipeline.py`, `prompt.py`, `utils/file.py`, and `config/config.yaml`, rather than preserving older wording.
- Standardized the attribute-extraction wording across the docs to describe the real flow: model returns structured text, pipeline parses it, then `main.py` writes JSON.
- Kept `docs/introduction/features.md` aligned to the current `SUPPORTED_PROMPT_TYPES` list while avoiding stronger claims than the source files support for the background/polish/QA prompt families.
- Applied a minimal follow-up correction in `docs/introduction/features.md`: preserve registry coverage for all listed names, but split the page between primary usable prompts and registry-only or partial paths so the document no longer overclaims end-to-end support.
- Separated standard package installation from model download and environment-variable setup in the Linux deployment doc so the base install path stays lightweight and current.

### Code changes

- Updated `docs/introduction/overview.md` to describe the pipeline as `CLI -> Config -> ModelEngine -> AnnotationPipeline -> JSON output` and to state explicitly that parsing happens in code rather than by trusting direct JSON from the model.
- Updated `docs/introduction/features.md` so attribute extraction is described as structured-text-to-JSON parsing and the prompt-type coverage matches the current `SUPPORTED_PROMPT_TYPES` list.
- Tightened `docs/introduction/features.md` so `classify_object_category_with_background_prompt`, `describe_object_with_background_prompt`, `polish_description_prompt_MMScan`, and `object_cognition_QA_with_background_prompt` are now explicitly marked as registry-only or non-primary paths rather than presented as fully usable end-to-end features.
- Updated `docs/installation/requirements.md` to reflect Python `>=3.10` and the current dependency/install surface from `pyproject.toml`.
- Updated `docs/installation/linux_deployment.md` to show `pip install -r requirements.txt` and `pip install -e .`, while keeping model download and environment notes in separate sections.
- Updated `docs/usage/quick_start.md` to show the default annotation command and explain that output JSON is produced by parsing structured text.
- Updated `docs/usage/data_preparation.md` to document the expected asset directory shape and the output layout `{output_dir}/{category}/{asset_id}_annotation.json`.
- Updated `docs/usage/configuration.md` to document `model.name`, `device_map`, `dtype`, `attn_implementation`, `temperature`, `max_new_tokens`, `data.views`, `use_thumbnails_dir`, `thumbnails_dir_name`, and `prompts.default_type`.
- Updated `docs/usage/cli_reference.md` to include `--asset_list_file`, `--force`, `--retry_incomplete`, `--num_chunks`, and `--chunk_index`, and to align retry/output behavior wording with the current code.

### Testing / verification commands and results

- `git grep -n -E 'CLI -> Config -> ModelEngine -> AnnotationPipeline -> JSON output|structured text|raw_output' -- "docs/introduction/overview.md" "docs/usage/quick_start.md" "docs/usage/cli_reference.md"`
  Result: confirmed the overview, quick start, and CLI reference now describe the parsed structured-text flow and the `raw_output` fallback.
- `git grep -n -E 'find_canonical_front_view_prompt|is_symmetric_object_prompt|classify_object_category_prompt|classify_object_category_with_background_prompt|describe_object_prompt_MMScan|describe_object_with_background_prompt|polish_description_prompt_MMScan|extract_object_attributes_prompt|object_cognition_QA_with_background_prompt' -- "docs/introduction/features.md"`
  Result: confirmed `docs/introduction/features.md` now covers all names currently listed in `SUPPORTED_PROMPT_TYPES`.
- `git grep -n -E '主要可用|注册表已列出但不应视为当前主要端到端能力的路径|不应把它表述为已完整实现并文档化的主功能|不应把它表述为当前默认或主要的端到端运行路径' -- "docs/introduction/features.md"`
  Result: confirmed the follow-up correction distinguishes the primary implemented prompts from registry-only or partial prompt paths.
- `git grep -n -E '>=3.10|transformers|torchvision|qwen-vl-utils|pip install -r requirements.txt|pip install -e \.' -- "docs/installation/requirements.md" "docs/installation/linux_deployment.md"`
  Result: confirmed the requirements page reflects Python `>=3.10` and the installation pages include the standard install commands and current dependency names.
- `git grep -n -E '\{output_dir\}/\{category\}/\{asset_id\}_annotation\.json|model\.name|device_map|dtype|attn_implementation|temperature|max_new_tokens|use_thumbnails_dir|thumbnails_dir_name|default_type|asset_list_file|retry_incomplete|num_chunks|chunk_index|--force' -- "docs/usage/data_preparation.md" "docs/usage/configuration.md" "docs/usage/cli_reference.md"`
  Result: confirmed the usage docs include the required output layout, configuration fields, and CLI flags.

### Open issues

- `SUPPORTED_PROMPT_TYPES` still includes names for prompt families that are not documented as primary operational paths. The page now marks them conservatively; fuller documentation should wait until those paths are implemented and exercised end-to-end.

## Task 5: Refresh development, guidebook, troubleshooting, DLC, and auto_caption docs

### Research / Investigation

- Read the Task 5 requirements from `docs/superpowers/plans/2026-04-15-repo-cleanup-and-doc-governance.md` and confirmed the scope is limited to the listed documentation files plus this shared execution log.
- Read `src/auto_asset_annotator/main.py` and confirmed the current CLI surface, retry rules, output path construction, and that JSON is written after pipeline processing rather than emitted directly by the model interface.
- Read `src/auto_asset_annotator/core/pipeline.py` and confirmed the current parsing rule: prompt names containing `extract` or `json` trigger `parse_structured_text_enhanced()`, with `raw_output` as the fallback on parse failure.
- Read `src/auto_asset_annotator/core/prompt.py` and confirmed the exact `SUPPORTED_PROMPT_TYPES` list and that `extract_object_attributes_prompt` explicitly asks for structured text with headers rather than JSON.
- Read `src/auto_asset_annotator/core/model.py` and confirmed the real model-loading order is Qwen2.5-VL-first, then `AutoModelForCausalLM`, with an additional Qwen3 branch only when the model name indicates it.
- Read `src/auto_asset_annotator/utils/file.py` and confirmed asset discovery, view matching, thumbnails fallback behavior, and the leaf-directory listing logic used by the main pipeline.
- Read `src/auto_asset_annotator/config/settings.py`, `config/config.yaml`, `pyproject.toml`, and `CLAUDE.md` to cross-check current config fields, dependency surface, and repository-level operating constraints.
- Read the existing target docs and confirmed repeated drift in three areas: they still described direct JSON-from-model behavior, several pages still sounded like the system was mid-build, and the DLC/repair docs mixed current usage with historical remediation flows.
- Read `scripts/dlc/submit_batch.py`, `scripts/dlc/launch_job.sh`, and `scripts/dlc/run_task.sh` to align the DLC docs to the scripts that actually exist and to the current environment/argument flow.
- Read `scripts/auto_caption/gr100_object_caption_by_Qwen3VL.py` and `scripts/auto_caption/qwen_utils.py` to verify that `scripts/auto_caption/` is a separate Qwen3-oriented utility area and should not be documented as the primary maintained pipeline entrypoint.

### Design decisions

- Kept the guidebook tone and metaphor style, but rewrote sections that implied the project was still being built so the narrative now reflects an already completed large-scale annotation outcome.
- Standardized the docs around the real pipeline contract: the model returns structured text for extraction prompts, the pipeline parses it, and `main.py` writes JSON.
- Documented model extension conservatively: Qwen2.5-VL is the primary supported path, generic fallback exists, and Qwen3 handling is described as a limited branch rather than a broad compatibility claim.
- Split troubleshooting guidance into daily operational issues versus historical repair workflows so the current supported flags and archive list paths are easier to follow.
- Refocused the DLC docs away from migration narrative and toward the current submission chain `submit_batch.py -> launch_job.sh -> run_task.sh -> auto_asset_annotator.main`.
- Clarified that `scripts/auto_caption/` remains available as a separate utility area, but is not the production entrypoint for the maintained pipeline.

### Code changes

- Rewrote `docs/development/project_structure.md` so it matches the current `src/auto_asset_annotator/` layout and accurately describes module responsibilities.
- Rewrote `docs/development/extending_models.md` to document the actual `core/model.py` loading path, including Qwen2.5-VL-first behavior, generic fallback notes, and conservative extension guidance.
- Rewrote `docs/development/custom_prompts.md` to include the exact current `SUPPORTED_PROMPT_TYPES` list and to state that `extract` / `json` prompt names trigger parsing in the pipeline.
- Refreshed `docs/guidebook/00_prologue.md` through `05_mass_production.md` to preserve the guidebook voice while aligning the narrative to the current code and the completed 52,907-asset production state.
- Rewrote `docs/guidebook/10_architecture_deep_dive.md`, `11_code_walkthrough.md`, and `12_prompt_engineering_mechanics.md` so the architecture and prompt-engineering explanations now match the real structured-text -> parser -> JSON flow.
- Rewrote `docs/troubleshooting/common_issues.md` so it reflects the current retry flags (`--retry_incomplete`, `--force`), the archive list paths under `archive/temp_lists/`, and a cleaner separation between everyday usage problems and historical repair commands.
- Rewrote `docs/dlc/README.md` to stay focused on the current DLC submission flow and current path conventions.
- Rewrote `docs/dlc/TESTING.md` to emphasize lightweight verification, current local/DLC script usage, and small-scope smoke testing instead of historical one-off migration details.
- Rewrote `scripts/auto_caption/README.md` to clarify that the directory is a separate utility area and that the primary maintained annotation flow lives under `src/auto_asset_annotator/`.
- Appended this Task 5 record to the shared execution log.

### Testing / verification commands and results

- `python -m compileall src`
  Result: confirmed the tracked source package still compiles after the documentation refresh; no code changes were introduced by mistake.
- `git grep -n -E 'SUPPORTED_PROMPT_TYPES|extract.*json|structured text|raw_output|52,907|archive/temp_lists/failed_assets.txt|--retry_incomplete' -- "docs/development" "docs/guidebook" "docs/troubleshooting/common_issues.md" "docs/dlc/README.md" "docs/dlc/TESTING.md" "scripts/auto_caption/README.md"`
  Result: confirmed the edited docs now reference the current prompt registry, parsing behavior, completed project state, archive-list paths, and current retry flag.
- `git grep -n -E 'Qwen2_5_VLForConditionalGeneration|AutoModelForCausalLM|Qwen3VLMoeForConditionalGeneration|process_vision_info|apply_chat_template' -- "docs/development/extending_models.md" "docs/guidebook/10_architecture_deep_dive.md" "docs/guidebook/11_code_walkthrough.md"`
  Result: confirmed the development and architecture docs now match the real model-loading and inference path in `core/model.py`.
- `git diff -- docs/development/project_structure.md docs/development/extending_models.md docs/development/custom_prompts.md docs/guidebook/00_prologue.md docs/guidebook/01_the_workshop.md docs/guidebook/02_raw_materials.md docs/guidebook/03_first_spell.md docs/guidebook/04_alchemy.md docs/guidebook/05_mass_production.md docs/guidebook/10_architecture_deep_dive.md docs/guidebook/11_code_walkthrough.md docs/guidebook/12_prompt_engineering_mechanics.md docs/troubleshooting/common_issues.md docs/dlc/README.md docs/dlc/TESTING.md scripts/auto_caption/README.md docs/changes/2026-04-15_repo-cleanup-and-doc-governance-execution.md`
  Result: reviewed that the diff is limited to the requested Task 5 documentation files plus the shared execution log; no commit was created.

### Open issues

- Some prompt names remain listed in `SUPPORTED_PROMPT_TYPES` even though only a subset are fully documented as primary operational paths; the refreshed docs now describe that conservatively, but the underlying prompt registry remains broader than the primary maintained runtime paths.

### Follow-up clarifications after review

- Tightened `docs/dlc/README.md` so it no longer implies that exporting `MODEL_PATH` automatically changes the model used by `auto_asset_annotator.main`; the doc now states explicitly that the effective model is controlled by `config` or `--model_path` in the main execution path.
- Tightened `docs/dlc/TESTING.md` so model-selection guidance now tells readers to pass `--model_path` or update `config/config.yaml`, and clarifies that the `MODEL_PATH` environment variable shown by `run_task.sh` is not by itself a direct override for `main.py`.
- Clarified `docs/dlc/README.md` to distinguish the maintained batch-submit chain `submit_batch.py -> launch_job.sh -> run_task.sh -> main` from the direct/manual `run_task.sh` modes such as `annotate`, `classify`, `extract`, and `custom`.
- Clarified `docs/development/custom_prompts.md` that some `SUPPORTED_PROMPT_TYPES` names are registry entries or special-case paths and should not all be read as equally direct, stable `--prompt_type` entrypoints for the current main pipeline.

## Task 6: Normalize historical change docs

### Research / Investigation

- Read the Task 6 scope in `docs/superpowers/plans/2026-04-15-repo-cleanup-and-doc-governance.md` and confirmed the work is limited to the listed `docs/changes/*.md` historical records plus this shared execution log.
- Reviewed every scoped historical document to identify two things: stale references to the five moved list files and places where the text still read like current operational guidance instead of a dated record.
- Verified that the already-updated moved-list references in the scoped 2026-03-05 and 2026-03-09 docs now point at `archive/temp_lists/...`.
- Verified that unrelated historical paths such as `scripts/missing_assets_20260309.txt`, `still_failed_assets.txt`, and `stubborn_assets.txt` are outside the replacement set for this task and should remain unchanged.
- Confirmed several milestone and status-heavy docs needed present-day framing because their original conclusions were phase-correct but later superseded by follow-up work on 2026-03-06 and 2026-03-09.

### Design decisions

- Kept all edits additive and minimal: preserve original dates, counts, outcomes, commands, and chronology, while adding short historical/context notes instead of rewriting the documents into new summaries.
- Used a consistent framing pattern near the top of each file to mark it as a historical record and to explain its current relevance.
- Left historical statements intact when they were true at the time; where later work changed the bigger picture, added current-relevance notes instead of modernizing away the original claim.
- Limited path rewrites to the five moved list files only, leaving unrelated list paths untouched as required.

### Code changes

- Added historical-record and current-relevance framing to `docs/changes/PROJECT_PROGRESS.md` so the milestone rollup reads clearly as a 2026-03-09 snapshot rather than an active runbook.
- Added equivalent framing to all scoped 2026-03-09 execution and validation reports so their role as dated project-history documents is explicit.
- Added equivalent framing to all scoped 2026-03-06 verification, rerun, and manual-completion reports, with special notes for intermediate/planned-state documents whose outcomes were later captured elsewhere the same day.
- Added equivalent framing to all scoped 2026-03-05 investigation, parser, migration, validation, data-analysis, execution, and commit-summary records.
- Corrected `docs/changes/2026-03-05_failed_annotations_summary.md` so the subset-specific `--filter_type image_only` workflow continues to use the historical `stubborn_assets.txt` retry-list name, while canonical all-failures `failed_assets.txt` references remain on `archive/temp_lists/failed_assets.txt` where appropriate.
- Appended this Task 6 record to the shared execution log.

### Testing / verification commands and results

- `rg -n "failed_assets\.txt|incomplete_assets\.txt|remaining_incomplete\.txt|verify_remaining\.txt|final_remaining\.txt" docs/changes -g "*.md"`
  Result: scoped historical docs now only show canonical `archive/temp_lists/...` references for the five moved files; remaining non-archive matches are historical mentions in this execution log and unrelated `still_failed_assets.txt` references that were intentionally preserved.
- `git diff --stat -- "docs/changes/PROJECT_PROGRESS.md" "docs/changes/2026-03-09_fill-dimensions-category-medians.md" "docs/changes/2026-03-09_fill-default-physical-properties.md" "docs/changes/2026-03-09_backfill-incomplete-physical-properties.md" "docs/changes/2026-03-09_annotation-validation-report.md" "docs/changes/2026-03-09_fix-42-null-descriptions.md" "docs/changes/2026-03-09_backfill-2816-missing-annotations.md" "docs/changes/2026-03-06_final_verification_report.md" "docs/changes/2026-03-06_stubborn_15_manual_completion.md" "docs/changes/2026-03-06_stubborn_assets_final_report.md" "docs/changes/2026-03-06_stubborn_15_final_report.md" "docs/changes/2026-03-06_stubborn_assets_rerun.md" "docs/changes/2026-03-05_dlc_migration.md" "docs/changes/2026-03-05_failed_annotations_summary.md" "docs/changes/2026-03-05_reannotation_script.md" "docs/changes/2026-03-05_parser_implementation.md" "docs/changes/2026-03-05_failed_annotations_analysis.md" "docs/changes/2026-03-05_rawoutput_patterns.md" "docs/changes/2026-03-05_pipeline_failure_analysis.md" "docs/changes/2026-03-05_batch_fix_execution.md" "docs/changes/2026-03-05_commit_summary.md" "docs/changes/2026-03-05_test_validation.md" "docs/changes/2026-03-05_data_analysis.md"`
  Result: confirmed Task 6 changed only the intended historical docs in scope before appending this execution-log entry.

### Open issues

- None for Task 6. A few scoped documents intentionally remain historically "in-progress" in tone because they capture intermediate states; the added framing now makes that explicit.

## Task 7: Final repository-wide verification and handoff evidence

### Research / Investigation

- Re-read the Task 7 requirements and kept the scope limited to repository-wide verification plus shared-log handoff evidence, with no new feature work.
- Verified from the main workspace root that the five historical root list files no longer exist: `failed_assets.txt`, `incomplete_assets.txt`, `remaining_incomplete.txt`, `verify_remaining.txt`, and `final_remaining.txt`.
- Verified the canonical archived copies exist at `archive/temp_lists/failed_assets.txt`, `archive/temp_lists/incomplete_assets.txt`, `archive/temp_lists/remaining_incomplete.txt`, `archive/temp_lists/verify_remaining.txt`, and `archive/temp_lists/final_remaining.txt`.
- Reviewed `README.md`, `docs/introduction/overview.md`, `docs/usage/quick_start.md`, `docs/development/project_structure.md`, and `docs/dlc/README.md` for internal markdown links and referenced markdown doc paths. The checked files currently contain no inline markdown links that resolve to local docs beyond the README surface; the markdown doc paths surfaced from `README.md` all resolve to existing files.
- Re-checked the structured-text parsing contract against current docs and source: `src/auto_asset_annotator/core/pipeline.py`, `src/auto_asset_annotator/main.py`, and `src/auto_asset_annotator/core/prompt.py` still implement the flow where extraction prompts request structured text, the pipeline parses it, and `main.py` writes JSON.
- Reviewed the full current change set with `git diff --stat` and `git diff` to capture handoff evidence suitable for user review.

### Design decisions

- Preferred verification commands and targeted reads over further edits, per task instructions.
- Treated `.gitignore` root-name ignore patterns as intentional repository hygiene rather than stale usage references; the canonical runtime/user-facing paths remain under `archive/temp_lists/`.
- Made one minimal documentation consistency fix after verification exposed a wording mismatch: `docs/introduction/overview.md` now says `parsed JSON output` in the top-level flow line so it matches the surrounding docs and the actual parser-mediated pipeline.

### Code changes

- Updated `docs/introduction/overview.md` to change the summary chain from `JSON output` to `parsed JSON output` for consistency with the structured-text -> parser -> JSON flow described elsewhere.
- Appended this Task 7 verification and handoff record to the shared execution log.

### Testing / verification commands and results

- `ls -1 "failed_assets.txt" "incomplete_assets.txt" "remaining_incomplete.txt" "verify_remaining.txt" "final_remaining.txt"`
  Result: each path returned `No such file or directory`, confirming the five historical list files are absent from the repository root.
- `ls -1 "archive/temp_lists/failed_assets.txt" "archive/temp_lists/incomplete_assets.txt" "archive/temp_lists/remaining_incomplete.txt" "archive/temp_lists/verify_remaining.txt" "archive/temp_lists/final_remaining.txt"`
  Result: all five canonical archived list files resolve successfully.
- `python - <<'PY' ...` (markdown-link resolver over `README.md`, `docs/introduction/overview.md`, `docs/usage/quick_start.md`, `docs/development/project_structure.md`, and `docs/dlc/README.md`)
  Result: no broken inline markdown links were found in the checked files.
- `python - <<'PY' ...` (markdown-doc-path resolver over the same files, extracting backticked `*.md` paths)
  Result: the README-referenced markdown docs all resolve to existing files: `docs/introduction/overview.md`, `docs/installation/linux_deployment.md`, `docs/usage/quick_start.md`, `docs/usage/cli_reference.md`, `docs/development/project_structure.md`, and `docs/troubleshooting/common_issues.md`.
- `git grep -n -P '(?<!archive/temp_lists/)\b(?:failed_assets|incomplete_assets|remaining_incomplete|verify_remaining|final_remaining)\.txt\b' -- . ':(exclude).worktrees/**'`
  Result: only `.gitignore` matched, via intentional root-name ignore rules for generated files; no stale tracked usage/docs references to root-level paths were found.
- `git grep -n -E 'structured text|parse_structured_text_enhanced|raw_output|JSON output|parsed JSON output' -- README.md docs/introduction/overview.md docs/usage/quick_start.md docs/development/project_structure.md docs/dlc/README.md CLAUDE.md`
  Result: the checked current docs in that pass described the structured-text -> parser -> JSON flow, with the one overview wording mismatch corrected in this task. A later Task 7 follow-up also corrected one stale parser-reference line in `CLAUDE.md`.
- `git diff --stat`
  Result: current repository-wide diff shows 52 changed files, 1,818 insertions, and 1,028 deletions across the cleanup/doc-governance work; this provides the high-level review footprint.
- `git diff`
  Result: reviewed the full textual diff for user handoff; the diff shows the expected cleanup/doc-governance edits plus the small Task 7 wording/log updates, and no commit was created.

### Open issues

- No blocking repository issue was found in Task 7 verification.
- `git grep` still surfaces the moved filenames in `.gitignore`, but only as deliberate ignore rules for generated root-level artifacts; this is expected and not a stale path-consistency problem.

## Task 7 Review: Spec compliance verification

### Research / Investigation

- Reviewed the Task 7 checklist in `docs/superpowers/plans/2026-04-15-repo-cleanup-and-doc-governance.md` and limited this pass to spec verification only.
- Re-checked the five moved list filenames at the repository root and under `archive/temp_lists/`.
- Re-read the key current docs in scope: `README.md`, `CLAUDE.md`, `docs/introduction/overview.md`, `docs/usage/quick_start.md`, `docs/development/project_structure.md`, `docs/development/custom_prompts.md`, and `docs/dlc/README.md`.
- Re-read `src/auto_asset_annotator/main.py` and `src/auto_asset_annotator/core/pipeline.py` to confirm the documented structured-text -> parser -> JSON flow still matches the implementation.
- Reviewed `git diff --stat`, `git diff`, and the targeted script diffs to confirm the full change set remains within the cleanup/doc-governance task family.

### Design decisions

- Treated `docs/superpowers/**` as out of scope for the review, per instructions.
- Evaluated the remaining root-name matches in `.gitignore` as intentional ignore rules rather than stale operational path references.
- Kept the follow-up fix minimal: correct the remaining stale `parse_structured_text()` references in `CLAUDE.md` and `docs/development/custom_prompts.md`, then update this Task 7 record to match the corrected state.

### Code changes

- Corrected the stale parser-reference line in `CLAUDE.md` to point readers at `parse_structured_text_enhanced()`.
- Corrected the stale parser-reference line in `docs/development/custom_prompts.md` to point readers at `parse_structured_text_enhanced()` and its underlying parsing logic.
- Updated this Task 7 review record so its verification wording matches the corrected documentation state.

### Testing / verification commands and results

- `ls -1 "failed_assets.txt" "incomplete_assets.txt" "remaining_incomplete.txt" "verify_remaining.txt" "final_remaining.txt"`
  Result: all five lookups failed with `No such file or directory`, confirming the repo root no longer contains the moved files.
- `ls -1 "archive/temp_lists/failed_assets.txt" "archive/temp_lists/incomplete_assets.txt" "archive/temp_lists/remaining_incomplete.txt" "archive/temp_lists/verify_remaining.txt" "archive/temp_lists/final_remaining.txt"`
  Result: all five archived canonical files exist.
- `ls "docs/introduction/overview.md" "docs/introduction/features.md" "docs/installation/linux_deployment.md" "docs/usage/quick_start.md" "docs/usage/data_preparation.md" "docs/usage/configuration.md" "docs/usage/cli_reference.md" "docs/development/project_structure.md" "docs/development/custom_prompts.md" "docs/development/extending_models.md" "docs/troubleshooting/common_issues.md"`
  Result: all README-surfaced internal doc targets exist.
- `git grep -n -P '(?<!archive/temp_lists/)\b(?:failed_assets|incomplete_assets|remaining_incomplete|verify_remaining|final_remaining)\.txt\b' -- . ':(exclude)docs/superpowers/**' ':(exclude).worktrees/**'`
  Result: only `.gitignore` matched via intentional ignore rules for generated root-level artifacts; no stale tracked usage references were found outside out-of-scope files.
- `git grep -n -E 'structured text|parse_structured_text_enhanced|raw_output|JSON output|parsed JSON output|writes? JSON' -- README.md CLAUDE.md docs/introduction docs/usage docs/development docs/guidebook docs/dlc/README.md`
  Result: after the follow-up fix, the checked current docs consistently describe the model returning structured text, `parse_structured_text_enhanced()` handling the current parser path for extraction prompts, and JSON being written afterward.
- `git diff --stat`
  Result: the repository-wide change summary remains the expected cleanup/doc-governance diff footprint, with no commit created.
- `git diff`
  Result: full diff reviewed for user handoff evidence; no additional spec blocker was found.

### Open issues

- None for Task 7 spec compliance review.
