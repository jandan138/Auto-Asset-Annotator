# Genesis-Lite Documentation Governance Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Genesis-lite documentation governance layer for Auto-Asset-Annotator without changing runtime behavior or moving existing historical docs.

**Architecture:** Add stable root governance files, a docs index, category indexes, and small templates. Keep existing documentation at current paths and use cross-links to clarify which docs are current, historical, operational, or process records.

**Tech Stack:** Markdown, git, shell verification commands, existing repository documentation.

---

## File Structure Map

### Create

- `AGENTS.md` - root cross-agent operating rules and safety entrypoint.
- `ANNOTATOR_RUNTIME_LOCK.md` - validated runtime, data, backend, DLC, and evidence lock.
- `archive/README.md` - archive policy for historical lists and deprecated artifacts.
- `docs/index.md` - canonical documentation table of contents.
- `docs/design/README.md` - long-lived design index.
- `docs/operations/README.md` - maintained runbook index.
- `docs/records/README.md` - dated record policy and historical `docs/changes/` bridge.
- `docs/reference/README.md` - stable reference index.
- `docs/templates/design.md` - design document template.
- `docs/templates/operation-record.md` - execution record template.
- `docs/templates/reference.md` - reference document template.

### Modify

- `README.md` - add a maintained docs index link and governance entrypoints without expanding the README.
- `CLAUDE.md` - point to `AGENTS.md` for cross-agent rules and keep Claude-specific commands and architecture guidance.
- `docs/dlc/README.md` - tighten real-submission safety wording around probe and operator examples.

### Do Not Modify

- `src/`
- `tests/`
- `config/config.yaml`
- `scripts/dlc/`
- `output/`
- `output_reannotate/`
- existing files under `docs/changes/`
- existing files under `docs/superpowers/` except this plan and the paired design spec

## Baseline Notes

- Worktree: `/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/.worktrees/docs-genesis-lite-governance`
- Baseline system-Python test command: `python -m pytest tests -q`
- Baseline system-Python result: `45 passed, 1 failed`, with the failure caused by missing `torch`.
- `.venv_dlc` has `torch 2.10.0+cu128` but lacks `pytest`.
- This plan relies on documentation verification because the implementation is documentation-only.

## Task 1: Root Governance Entrypoints

**Files:**
- Create: `AGENTS.md`
- Create: `ANNOTATOR_RUNTIME_LOCK.md`
- Create: `archive/README.md`
- Test: file existence, link target checks, grep checks

- [ ] **Step 1: Read the current root guidance and reference guidance**

Run:

```bash
sed -n '1,260p' README.md
sed -n '1,340p' CLAUDE.md
sed -n '1,220p' /cpfs/user/zhuzihou/dev/genesis-llm/AGENTS.md
sed -n '1,220p' /cpfs/user/zhuzihou/dev/genesis-llm/GENESIS_RUNTIME_LOCK.md
```

Expected: current repo rules, command examples, architecture, project status, and Genesis-style governance patterns are visible.

- [ ] **Step 2: Create `AGENTS.md`**

Use `apply_patch` to add a concise agent rule document with these exact sections:

```markdown
# AGENTS.md - AI Agent Rules for Auto-Asset-Annotator

## Project Context

Auto-Asset-Annotator is a Qwen2.5-VL based 3D asset annotation pipeline. The maintained runtime chain is:

```text
CLI -> Config -> ModelEngine -> AnnotationPipeline -> parsed JSON output
```

The current project state records 52,907 annotated assets with complete `description`, `material`, `dimensions`, `mass`, and `placement` fields. Treat `output/` as the stable structured result set unless a task explicitly says otherwise.

## Key Rules

1. Do not run local VLM annotation commands unless explicitly instructed; they can load large model weights.
2. Do not run API-backed annotation commands unless explicitly instructed; they can consume remote quota and require real secrets.
3. Do not submit real DLC jobs unless explicitly instructed; dry-run first and record the command.
4. Never commit API keys, credentials, `.env` files, model weights, checkpoints, or large generated outputs.
5. Keep `config/config.yaml` as the checked-in default configuration; use CLI flags or environment variables for run-specific overrides.
6. Treat model output as structured text that is parsed into JSON by the pipeline, not as trusted direct JSON.
7. New work must update the relevant docs when behavior, commands, runtime assumptions, or operational status changes.
8. New dated execution records go under `docs/records/YYYY-MM-DD-topic.md`; older records remain under `docs/changes/`.

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
```

Expected: `AGENTS.md` exists and does not duplicate the full `CLAUDE.md`.

- [ ] **Step 3: Create `ANNOTATOR_RUNTIME_LOCK.md`**

Use `apply_patch` to add a runtime lock with these sections:

```markdown
# Auto-Asset-Annotator Runtime Lock

Validation status: ANNOTATION_OUTPUT_COMPLETE_2026_03_09_AND_DLC_WORKFLOW_REFRESHED_2026_04_16

Validation dates:

- Annotation completion evidence: 2026-03-09
- DLC workflow refresh evidence: 2026-04-16
- Documentation governance lock created: 2026-05-13

## Runtime Chain

```text
CLI -> Config -> ModelEngine -> AnnotationPipeline -> parsed JSON output
```

## Default Local Runtime

- Package entrypoint: `python -m auto_asset_annotator.main`
- Default config: `config/config.yaml`
- Default backend: `local_hf`
- Default local model path: `/cpfs/shared/simulation/zhuzihou/models/Qwen2.5-VL-7B-Instruct`
- Default prompt type: `extract_object_attributes_prompt`
- Default output behavior: model returns structured text; pipeline parses and normalizes fields; `main.py` writes JSON.

Config source: checked-in `config/config.yaml` and current root docs as of this lock update.

## Supported Backends

- `local_hf`: local Hugging Face/Qwen-VL inference.
- `openai_compatible`: remote multimodal chat-completions-compatible inference using data URL images.

## Output State

Validated from historical records, not re-counted during this documentation pass:

- Total annotated assets: 52,907
- Original assets: 50,091
- Backfilled assets: 2,816
- Complete fields: `description`, `material`, `dimensions`, `mass`, `placement`
- Stable structured result directory: `output/`

## DLC Runtime State

- Maintained chain: `submit_*.sh -> submit_batch.py -> launch_job.sh -> run_task.sh -> python_runtime.sh -> python -m auto_asset_annotator.main`
- Maintained runbook: `docs/dlc/README.md`
- Current smartbot quota mapping:
  - `1/2/4 GPU` -> `quota1r947pmazvk`
  - `8 GPU` -> `quotaksvqq2oh2pg`

## Evidence Records

- Project completion overview: `docs/changes/PROJECT_PROGRESS.md`
- DLC balanced upgrade: `docs/changes/2026-04-16_dlc_balanced_upgrade.md`
- DLC quota alignment and probe: `docs/changes/2026-04-16_dlc_quota_alignment_and_probe.md`
- Documentation cleanup record: `docs/changes/2026-04-15_repo-cleanup-and-doc-governance-execution.md`

## Boundaries

- This lock records documented project state; it does not prove a fresh model run.
- This lock does not validate a live API endpoint.
- This lock does not validate a fresh real DLC submission.
- This lock does not contain secrets, API keys, model weights, or credentials.

## Update Checklist

- Update this file when default backend, model path, prompt type, output state, DLC quota mapping, or validation evidence changes.
- Record the evidence file before promoting a new validation status.
- Do not record secrets or API keys in this file.
```

Expected: the runtime lock pins current documented facts, includes dates and boundaries, and links only to existing evidence files.

- [ ] **Step 4: Create `archive/README.md`**

Use `apply_patch` to add:

```markdown
# Archive

Historical artifacts kept for reference. Files here are not current operator entrypoints unless a maintained runbook or script explicitly points to them.

## Contents

- `temp_lists/` - legacy storage for historical and operator-curated asset lists. These paths remain supported operational inputs when referenced by maintained scripts or runbooks.

## Rules

- Prefer git history or dated records over ad hoc backup files.
- Do not move new operational inputs here unless they are historical or intentionally operator-curated lists.
- When a runbook or script depends on a list under `archive/temp_lists/`, link or print the exact path.
```

Expected: archive policy exists and matches current use of `archive/temp_lists/`.

- [ ] **Step 5: Verify Task 1**

Run:

```bash
test -f AGENTS.md
test -f ANNOTATOR_RUNTIME_LOCK.md
test -f archive/README.md
grep -n "docs/index.md" AGENTS.md
grep -n "ANNOTATOR_RUNTIME_LOCK.md" AGENTS.md
grep -n "52,907" ANNOTATOR_RUNTIME_LOCK.md
grep -n "Boundaries" ANNOTATOR_RUNTIME_LOCK.md
git diff --check -- AGENTS.md ANNOTATOR_RUNTIME_LOCK.md archive/README.md
```

Expected: all commands exit 0.

- [ ] **Step 6: Commit Task 1**

Run:

```bash
git add AGENTS.md ANNOTATOR_RUNTIME_LOCK.md archive/README.md
git commit -m "docs: add root documentation governance entrypoints"
```

Expected: one commit containing only the three Task 1 files.

## Task 2: Documentation Navigation And Category Indexes

**Files:**
- Create: `docs/index.md`
- Create: `docs/design/README.md`
- Create: `docs/operations/README.md`
- Create: `docs/records/README.md`
- Create: `docs/reference/README.md`
- Test: file existence, link target checks, grep checks

- [ ] **Step 1: Create the category directories**

Run:

```bash
mkdir -p docs/design docs/operations docs/records docs/reference
```

Expected: all four directories exist.

- [ ] **Step 2: Create `docs/index.md`**

Use `apply_patch` to add sections for quick navigation, project overview, current status, and documentation policy. Include these links:

```markdown
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
- Historical records: `changes/`
- Superpowers specs and plans: `superpowers/`

## Project Overview

Auto-Asset-Annotator annotates 3D assets with structured physical and semantic fields. The maintained chain is:

```text
CLI -> Config -> ModelEngine -> AnnotationPipeline -> parsed JSON output
```

## Current Status

- 52,907 assets have complete structured annotations.
- `output/` is the stable structured result set.
- The default prompt is `extract_object_attributes_prompt`.
- The model returns structured text for extraction prompts; the pipeline parses it into JSON.

## Documentation Map

- `design/` - long-lived design indexes and future stable designs.
- `operations/` - maintained runbook index.
- `records/` - new dated execution records.
- `reference/` - stable reference index.
- `changes/` - historical March and April 2026 records retained at original paths.
- `superpowers/` - agent design specs and implementation plans.

## Writing Policy

Use current docs for current behavior. Use dated records for work history. When changing commands, runtime assumptions, DLC behavior, output contracts, or validation status, update the relevant docs and link evidence from `ANNOTATOR_RUNTIME_LOCK.md` when the validated state changes.
```

Expected: docs index is concise and points to current docs without moving existing files.

- [ ] **Step 3: Create `docs/design/README.md`**

Use `apply_patch` to add an index that links to existing stable design/process docs:

```markdown
# Design Documents

Long-lived designs live here when they describe stable architecture or future implementation direction.

Current design sources:

- Superpowers specs: `../superpowers/specs/`
- Repository cleanup and documentation governance design: `../superpowers/specs/2026-04-15-repo-cleanup-and-doc-governance-design.md`
- API backend design: `../superpowers/specs/2026-04-16-api-backend-for-multimodal-annotation-design.md`
- DLC balanced upgrade design: `../superpowers/specs/2026-04-16-dlc-balanced-upgrade-design.md`
- Genesis-lite documentation governance design: `../superpowers/specs/2026-05-13-genesis-lite-doc-governance-design.md`

New stable designs may be added directly under `docs/design/` when they are not just agent implementation process records.
```

- [ ] **Step 4: Create `docs/operations/README.md`**

Use `apply_patch` to add:

```markdown
# Operations

Maintained operational documentation for running, validating, and recovering annotation workflows.

## Maintained Runbooks

- DLC operator runbook: `../dlc/README.md`
- DLC testing notes: `../dlc/TESTING.md`
- Quick start: `../usage/quick_start.md`
- CLI reference: `../usage/cli_reference.md`
- Configuration: `../usage/configuration.md`
- Data preparation: `../usage/data_preparation.md`
- Troubleshooting: `../troubleshooting/common_issues.md`

## Safety

Use dry-run paths before DLC submission. Do not run local VLM or API-backed annotation unless the operator explicitly intends to consume local GPU memory or remote API quota.
```

- [ ] **Step 5: Create `docs/records/README.md`**

Use `apply_patch` to add:

```markdown
# Records

Dated execution records for new work should be written here as `YYYY-MM-DD-topic.md`.

Existing historical records remain under `../changes/` to preserve links and avoid unnecessary churn. The March 2026 completion overview is `../changes/PROJECT_PROGRESS.md`.

`AGENTS.md` and `CLAUDE.md` define this as the active location for new dated records. Do not move old `../changes/` files as part of routine documentation updates.

## Record Rules

- State the date and purpose.
- Record commands that were run.
- Record results and evidence paths.
- Distinguish current operational guidance from historical context.
- Link follow-up work when a record changes project status.
```

- [ ] **Step 6: Create `docs/reference/README.md`**

Use `apply_patch` to add:

```markdown
# Reference

Stable reference material should live here when it is more durable than a dated record.

Current reference sources:

- Project structure: `../development/project_structure.md`
- Prompt extension guide: `../development/custom_prompts.md`
- Model extension guide: `../development/extending_models.md`
- Configuration reference: `../usage/configuration.md`
- CLI reference: `../usage/cli_reference.md`
- Data layout and output format: `../usage/data_preparation.md`

Future reference pages can split output schema, backend contracts, prompt behavior, and DLC environment contracts into focused files.
```

- [ ] **Step 7: Verify Task 2**

Run:

```bash
test -f docs/index.md
test -f docs/design/README.md
test -f docs/operations/README.md
test -f docs/records/README.md
test -f docs/reference/README.md
grep -n "52,907" docs/index.md
grep -n "changes/" docs/index.md docs/records/README.md
git diff --check -- docs/index.md docs/design/README.md docs/operations/README.md docs/records/README.md docs/reference/README.md
```

Expected: all commands exit 0.

- [ ] **Step 8: Commit Task 2**

Run:

```bash
git add docs/index.md docs/design/README.md docs/operations/README.md docs/records/README.md docs/reference/README.md
git commit -m "docs: add documentation index and category maps"
```

Expected: one commit containing only Task 2 files.

## Task 3: Documentation Templates

**Files:**
- Create: `docs/templates/design.md`
- Create: `docs/templates/operation-record.md`
- Create: `docs/templates/reference.md`
- Test: file existence and placeholder-quality grep checks

- [ ] **Step 1: Create the template directory**

Run:

```bash
mkdir -p docs/templates
```

Expected: `docs/templates/` exists.

- [ ] **Step 2: Create `docs/templates/design.md`**

Use `apply_patch` to add:

```markdown
# Design Title

Date: YYYY-MM-DD

## Summary

Write one paragraph describing the intended change and why it matters.

## Context

List the current files, workflows, or constraints that shape the design.

## Goals

- State the first concrete outcome.
- State the second concrete outcome.

## Non-Goals

- State behavior or scope that this design will not change.

## Proposed Design

Describe the selected approach, file boundaries, and expected data or control flow.

## Validation

List the commands, inspections, or evidence records that will prove the work is correct.

## Risks

List known risks and the mitigation for each risk.
```

- [ ] **Step 3: Create `docs/templates/operation-record.md`**

Use `apply_patch` to add:

```markdown
# Operation Record Title

Date: YYYY-MM-DD

## Purpose

State what was attempted and why.

## Commands

```bash
command that was run
```

## Results

Record job IDs, output paths, counts, pass/fail status, and notable logs.

## Evidence

- Link to output files, records, or verification commands.

## Follow-Up

- Record the next concrete action, or state that no follow-up is required.
```

- [ ] **Step 4: Create `docs/templates/reference.md`**

Use `apply_patch` to add:

```markdown
# Reference Title

## Purpose

State what stable contract or concept this page documents.

## Contract

Describe the fields, commands, paths, or interfaces that readers can rely on.

## Examples

```bash
example command
```

## Update Rules

State when this reference must be updated.
```

- [ ] **Step 5: Verify Task 3**

Run:

```bash
test -f docs/templates/design.md
test -f docs/templates/operation-record.md
test -f docs/templates/reference.md
grep -n "YYYY-MM-DD" docs/templates/design.md docs/templates/operation-record.md
grep -nE 'TO''DO|T''BD' docs/templates/*.md && exit 1 || true
git diff --check -- docs/templates/design.md docs/templates/operation-record.md docs/templates/reference.md
```

Expected: files exist, date markers are present, no unfinished-marker matches are present, and diff check is clean.

- [ ] **Step 6: Commit Task 3**

Run:

```bash
git add docs/templates/design.md docs/templates/operation-record.md docs/templates/reference.md
git commit -m "docs: add documentation templates"
```

Expected: one commit containing only Task 3 files.

## Task 4: Reconcile Root Entry Docs

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `docs/dlc/README.md`
- Test: grep checks and link target checks

- [ ] **Step 1: Update `README.md` safety framing and documentation links**

Use `apply_patch` to add this note near `## Quick Start`, before the first annotation command:

```markdown
These commands are operational examples. The default annotation command can load the local VLM. API-backed examples can consume remote quota. Use them only when you intentionally want to run annotation.
```

Then adjust the `## Documentation` section so it includes these entries near the top:

```markdown
- 文档总览: `docs/index.md`
- Agent 协作规则: `AGENTS.md`
- 运行状态锁: `ANNOTATOR_RUNTIME_LOCK.md`
```

Keep the existing user-facing links to overview, installation, quick start, CLI, DLC, development, and troubleshooting docs.

Expected: README remains user-facing and does not duplicate the new docs index.

- [ ] **Step 2: Update the top of `CLAUDE.md`**

Use `apply_patch` to add this short section after the title:

```markdown
## Shared Agent Rules

Read `AGENTS.md` for repository-wide agent rules, safety constraints, documentation requirements, and directory quick reference. This file keeps Claude Code specific commands, architecture notes, and operational details.
```

Expected: `CLAUDE.md` points to `AGENTS.md` before detailed commands.

- [ ] **Step 3: Replace the long agent documentation rule in `CLAUDE.md` with a pointer**

Use `apply_patch` to replace the section starting at `## Agent Team Documentation Rule (Mandatory)` with:

```markdown
## Agent Team Documentation Rule

Repository-wide agent documentation requirements live in `AGENTS.md`. In short: every behavior, command, runtime assumption, or operational status change must update the relevant maintained docs or a dated record under `docs/records/YYYY-MM-DD-topic.md` before the task is treated as complete. Historical records under `docs/changes/` remain at their existing paths.
```

Expected: `CLAUDE.md` no longer owns duplicate cross-agent governance text and no longer mandates new records under `docs/changes/`.

- [ ] **Step 4: Tighten `docs/dlc/README.md` real-submit wording**

Use `apply_patch` to replace this sentence in the probe workflow section:

```markdown
The real submission path is the same command without `--dry-run`.
```

with:

```markdown
Real submission is a quota-consuming operation. After a reviewed dry-run, use the same command without `--dry-run` only when the operator explicitly intends to create the tiny DLC job.
```

Expected: the DLC runbook still documents the path, but no longer frames real submission as a casual next step.

- [ ] **Step 5: Verify Task 4**

Run:

```bash
grep -n "docs/index.md" README.md
grep -n "AGENTS.md" README.md CLAUDE.md
grep -n "ANNOTATOR_RUNTIME_LOCK.md" README.md
grep -n "Every agent in a team MUST" CLAUDE.md && exit 1 || true
grep -n "docs/records/YYYY-MM-DD-topic.md" CLAUDE.md
grep -n "quota-consuming" docs/dlc/README.md
test -f docs/index.md
test -f AGENTS.md
test -f ANNOTATOR_RUNTIME_LOCK.md
git diff --check -- README.md CLAUDE.md docs/dlc/README.md
```

Expected: new links exist, old duplicate mandatory agent block is gone, and diff check is clean.

- [ ] **Step 6: Commit Task 4**

Run:

```bash
git add README.md CLAUDE.md docs/dlc/README.md
git commit -m "docs: link root docs to governance entrypoints"
```

Expected: one commit containing README, CLAUDE, and the small DLC safety wording change.

## Task 5: Final Verification And Review

**Files:**
- Inspect: all changed files
- Test: final documentation and git checks

- [ ] **Step 1: Verify changed file list**

Run:

```bash
git diff --name-only main...HEAD
```

Expected: output includes only docs and root documentation files from this plan.

- [ ] **Step 2: Verify linked file existence**

Run:

```bash
for f in \
  AGENTS.md \
  ANNOTATOR_RUNTIME_LOCK.md \
  archive/README.md \
  docs/index.md \
  docs/design/README.md \
  docs/operations/README.md \
  docs/records/README.md \
  docs/reference/README.md \
  docs/templates/design.md \
  docs/templates/operation-record.md \
  docs/templates/reference.md \
  docs/dlc/README.md \
  docs/changes/PROJECT_PROGRESS.md; do test -f "$f"; done
```

Expected: command exits 0.

- [ ] **Step 3: Run final whitespace verification**

Run:

```bash
git diff --check main...HEAD
```

Expected: command exits 0.

- [ ] **Step 4: Run relative Markdown link verification**

Run:

```bash
python - <<'PY'
from pathlib import Path
import re
import sys

files = [Path(p) for p in [
    "README.md",
    "CLAUDE.md",
    "AGENTS.md",
    "ANNOTATOR_RUNTIME_LOCK.md",
    "archive/README.md",
    "docs/index.md",
    "docs/design/README.md",
    "docs/operations/README.md",
    "docs/records/README.md",
    "docs/reference/README.md",
    "docs/templates/design.md",
    "docs/templates/operation-record.md",
    "docs/templates/reference.md",
    "docs/dlc/README.md",
]]

missing = []
pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)|`([^`]+\.md)`")

for path in files:
    text = path.read_text(encoding="utf-8")
    for match in pattern.finditer(text):
        target = match.group(1) or match.group(2)
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        target = target.split("#", 1)[0]
        if not target or target.startswith("/"):
            continue
        if "*" in target:
            continue
        candidate = (path.parent / target).resolve()
        if not candidate.exists():
            missing.append(f"{path}:{target}")

if missing:
    print("\n".join(missing))
    sys.exit(1)
PY
```

Expected: command exits 0 and prints no missing links.

- [ ] **Step 5: Run final content checks**

Run:

```bash
grep -n "docs/index.md" README.md AGENTS.md
grep -n "docs/index.md" CLAUDE.md
grep -n "AGENTS.md" README.md CLAUDE.md docs/index.md
grep -n "ANNOTATOR_RUNTIME_LOCK.md" README.md CLAUDE.md AGENTS.md docs/index.md
grep -n "docs/changes" docs/index.md docs/records/README.md
grep -n "docs/records" AGENTS.md CLAUDE.md docs/index.md docs/records/README.md
grep -n "output/" AGENTS.md ANNOTATOR_RUNTIME_LOCK.md
grep -n "local_hf" ANNOTATOR_RUNTIME_LOCK.md
grep -n "openai_compatible" ANNOTATOR_RUNTIME_LOCK.md
```

Expected: all checks produce matching lines.

- [ ] **Step 6: Run available test command and record baseline**

Run:

```bash
python -m pytest tests -q
```

Expected: in the current system Python environment, this may reproduce the known baseline `torch` import failure. Record the exact pass/fail count in the final response and do not claim the Python test suite passes unless a fresh run exits 0.

- [ ] **Step 7: Request final multi-agent review**

Dispatch at least one reviewer agent with:

```text
Review the documentation governance changes from main...HEAD in /cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/.worktrees/docs-genesis-lite-governance. Check link correctness, scope control, consistency with the Genesis-lite design, and whether README/CLAUDE/AGENTS responsibilities are clear. Do not edit files. Return findings ordered by severity with file references.
```

Expected: Critical and Important findings are fixed or explicitly rejected with evidence.

- [ ] **Step 8: Final status**

Run:

```bash
git status --short --branch
git log --oneline --decorate -n 6
```

Expected: worktree is on `docs-genesis-lite-governance`; no uncommitted changes remain unless a final review fix is intentionally left for the next commit.
