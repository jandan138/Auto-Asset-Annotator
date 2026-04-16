# Repository Cleanup And Documentation Governance Design

## Summary

This design defines a repository-wide cleanup and documentation governance pass for `Auto-Asset-Annotator`.

The work has two linked goals:

1. Clean the repository root by moving scattered historical run-list files into `archive/temp_lists/`.
2. Refresh and normalize repository documentation so it matches the current code, current directory layout, and current project status.

This is a repository hygiene and documentation project. It does not change model inference behavior, annotation logic, parsing logic, or runtime data outputs.

## Context

The current repository contains a mix of long-lived project entry files and historical run artifacts at the root level. Root-level `.txt` files such as `failed_assets.txt` and `remaining_incomplete.txt` are historical processing lists, not stable project entrypoints.

Documentation is also partially out of sync with the current implementation:

- Some docs still describe behavior in earlier project phases rather than the current stabilized state.
- Some docs imply JSON is returned directly by the model, while the current implementation asks the model for structured text and parses it in code.
- Some docs and examples reference root-level list files that should be archived.
- Historical change documents under `docs/changes/` contain useful project history, but they need consistent structure, corrected paths, and clear separation between historical context and current applicability.

## Goals

### Goal 1: Root Cleanup

Leave the repository root as a stable entry layer for source, configuration, documentation, scripts, and explicit data directories.

### Goal 2: Documentation Accuracy

Make the documentation consistent with the current codebase, including CLI options, prompt/output behavior, retry logic, directory structure, DLC workflow, and project status.

### Goal 3: Documentation Normalization

Make repository documentation easier to read and maintain by using consistent structure, terminology, path style, and status framing.

### Goal 4: History Preservation

Preserve historical change records while updating them into clean, accurate historical documents that do not mislead current readers.

## Non-Goals

- No model execution.
- No annotation job submission.
- No refactor of core runtime logic.
- No deletion of historical information.
- No broad directory reshuffle of `docs/` itself.
- No modification of output datasets in `output/` or `output_reannotate/`.
- No git commit unless explicitly requested by the user.

## Scope

### File Cleanup Scope

The cleanup scope includes the following root-level historical list files:

- `failed_assets.txt`
- `incomplete_assets.txt`
- `remaining_incomplete.txt`
- `verify_remaining.txt`
- `final_remaining.txt`

Files are cleanup candidates because of their role as historical run lists, not because they happen to use the `.txt` extension. Stable project files such as `requirements.txt` remain at the repository root.

These files will be moved to:

- `archive/temp_lists/failed_assets.txt`
- `archive/temp_lists/incomplete_assets.txt`
- `archive/temp_lists/remaining_incomplete.txt`
- `archive/temp_lists/verify_remaining.txt`
- `archive/temp_lists/final_remaining.txt`

If implementation uncovers additional root-level `.txt` files that clearly serve the same role as historical run lists or verification lists, they should also be moved into `archive/temp_lists/`, with all references updated in the same change.

### Documentation Scope

The documentation scope covers all current repository documentation surfaces that describe the project, its workflows, or its history:

- `README.md`
- `CLAUDE.md`
- `docs/**/*.md` except `docs/superpowers/**/*.md`
- `scripts/auto_caption/README.md`

Repository-internal agent profile files under `.claude/agents/*.md` are out of scope unless they contain repository paths or workflow instructions that become invalid because of this cleanup. They are tooling metadata, not the primary project documentation set.

## Retained Root Structure

The following classes of files and directories remain at the root:

- Project entry docs and metadata: `README.md`, `CLAUDE.md`, `pyproject.toml`, `requirements.txt`, `setup.py`, `uv.lock`
- Source and tests: `src/`, `tests/`
- Runtime/config/tooling directories: `config/`, `scripts/`, `docs/`, `archive/`, `dlc`
- Explicit data/output directories: `output/`, `output_reannotate/`

The cleanup should make the root read like a stable project entrypoint, not a mixed work area.

## Design Decisions

### Decision 1: Use Existing Archive Convention

Historical list files will be moved into the already-existing `archive/temp_lists/` directory rather than creating a new top-level archive taxonomy.

Rationale:

- It matches the repository's current organization style.
- It minimizes structural churn.
- It reduces the number of new naming decisions.

### Decision 2: Update Both Current Docs And Historical Docs

The work will not stop at current usage docs. `docs/changes/*.md` will also be updated.

Rationale:

- The user explicitly requested full-documentation cleanup.
- Historical docs currently contain paths and commands that may mislead future readers.
- Preserving history does not require preserving stale references.

### Decision 3: Normalize Without Rebuilding The Entire Docs Tree

Documentation files will be updated in place, with structure and wording normalized, but the overall `docs/` hierarchy will remain intact.

Rationale:

- Existing links and user expectations remain valid.
- The repository already has a meaningful docs taxonomy.
- The immediate problem is drift and inconsistency, not taxonomy failure.

## Documentation Normalization Rules

The updated documentation set should follow these rules.

### Rule 1: Current-State Framing For Current Docs

Current docs must describe the repository as it exists now, not as it existed during intermediate repair phases.

This includes:

- Current project completion status.
- Current default prompt type.
- Current output parsing behavior.
- Current retry and reprocessing behavior.
- Current asset path and output path conventions.

### Rule 2: Historical Framing For Historical Docs

Documents under `docs/changes/` must clearly read as dated historical records.

Each historical document should clearly communicate:

- When the work happened.
- What problem existed at that time.
- What was changed.
- What result was achieved.
- What remains relevant to the current repository.

### Rule 3: Path Consistency

All references to the migrated list files must use `archive/temp_lists/<filename>`.

Examples, commands, and narrative references must all use the same canonical path style.

### Rule 4: Code-Accurate Behavior Descriptions

Documentation must match the current implementation in:

- `src/auto_asset_annotator/main.py`
- `src/auto_asset_annotator/core/pipeline.py`
- `src/auto_asset_annotator/core/prompt.py`
- `src/auto_asset_annotator/core/model.py`
- `src/auto_asset_annotator/utils/file.py`
- `config/config.yaml`

In particular, documentation must reflect that:

- The main annotation flow requests structured text for attribute extraction.
- The pipeline parses structured text into JSON output files.
- Category is overridden from the directory path.
- Existing output files are skipped unless forced or eligible for retry.
- `--asset_list_file` and `--retry_incomplete` are supported.

### Rule 5: Clear Command Intent

Command examples should make it obvious whether a command is:

- Standard usage
- Retry/recovery usage
- Historical repair usage
- Distributed/DLC usage

### Rule 6: Uniform Tone And Structure

Docs should use direct, factual phrasing and avoid mixed assumptions about project state.

Where useful, documents should converge on a simple structure such as:

- Purpose
- Current behavior or historical context
- Commands/examples
- Outputs/results
- Notes/current relevance

### Rule 7: Internal Link Validity

Current operational docs should not contain dead internal links.

If a document points to a missing repository file, the cleanup must repair that reference by either:

- pointing it to the correct existing target, or
- removing the dead link if no maintained target exists.

This specifically applies to top-level entry docs such as `README.md`, which should not advertise missing companion files.

## Documentation Update Strategy

### Tier 1: Current Operational Docs

These documents must become immediately usable for current readers:

- `README.md`
- `CLAUDE.md`
- `docs/introduction/*.md`
- `docs/installation/*.md`
- `docs/usage/*.md`
- `docs/development/*.md`
- `docs/guidebook/*.md`
- `docs/troubleshooting/*.md`
- `docs/dlc/*.md`
- `scripts/auto_caption/README.md`

Expected outcomes:

- No stale root-list paths.
- No conflicting output-format descriptions.
- No outdated project status text.
- No ambiguous workflow descriptions.

### Tier 2: Historical Change Docs

These documents must be normalized as accurate historical records:

- `docs/changes/*.md`

Expected outcomes:

- Corrected list-file paths.
- Consistent dated-history framing.
- Explicit distinction between historical actions and current repository state.
- Cleaner, more uniform sectioning.

## Implementation Sequence

The work should proceed in this order:

1. Inventory root-level loose files and confirm the move list.
2. Move target list files into `archive/temp_lists/`.
3. Update all repository references to the moved paths.
4. Refresh current operational docs.
5. Normalize historical change docs.
6. Perform consistency verification across documentation and code references.

This order minimizes broken references and ensures all rewritten docs target the post-cleanup repository state.

## Verification Plan

Verification must remain lightweight and must not load the VLM.

### Cleanup Verification

- Confirm that the target root-level `.txt` files no longer remain at the repository root.
- Confirm that their replacements exist in `archive/temp_lists/`.

### Reference Verification

- Search the repository for old root-path references to moved list files.
- Either eliminate them or leave them only in explicitly historical wording that still references the new canonical location.

### Documentation Accuracy Verification

- Cross-check the core docs against `main.py`, `pipeline.py`, `prompt.py`, `model.py`, `utils/file.py`, and `config/config.yaml`.
- Confirm that core docs agree on output behavior, retry logic, prompt behavior, and directory structure.

### Path And File Existence Verification

- Confirm that referenced scripts and docs paths exist.
- Confirm that commands shown in docs reference real script names and real flags.
- Confirm that important internal markdown links resolve to existing repository files.

## Risks And Mitigations

### Risk 1: Overwriting Historical Meaning

If historical docs are rewritten too aggressively, they may stop functioning as useful records.

Mitigation:

- Preserve the original event meaning and chronology.
- Only modernize structure, stale paths, and clarity.

### Risk 2: Introducing Broken Links Or Commands

Broad doc edits can easily leave mismatched paths.

Mitigation:

- Update moved-file references systematically.
- Verify with repository-wide searches after edits.

### Risk 3: Mixing Current Guidance With Historical Procedures

Readers may confuse routine usage with one-off repair workflows.

Mitigation:

- Label current docs around standard vs repair workflows.
- Add explicit current-relevance language to historical docs.

## Deliverables

The completed change should produce:

- A cleaner repository root.
- Archived historical list files under `archive/temp_lists/`.
- Updated current operational documentation.
- Normalized `docs/changes/` history documents.
- Repository-wide path consistency for moved list files.
- A docs set that matches the current implementation and current project state.

## Acceptance Criteria

This design is satisfied when all of the following are true:

- The target historical list files are no longer scattered in the root.
- `archive/temp_lists/` contains the canonical copies.
- Current docs accurately describe the current implementation and status.
- Historical docs are still historical, but no longer stale or misleading.
- Root-list file references are consistent across the repository.
- Current operational docs do not contain important dead internal markdown links.
- No heavy annotation/model command was executed during the cleanup.
