# Genesis-Lite Documentation Governance Design

## Summary

This design normalizes `Auto-Asset-Annotator` documentation using the useful parts of the
`genesis-llm` repository structure without forcing a disruptive full docs migration.

The goal is a stable documentation layer for operators and agents:

- a root agent rule entrypoint
- a docs index
- a runtime lock for validated project state
- clear buckets for design, operations, records, reference, and archive material
- templates that make future records consistent

This is a documentation governance change only. It does not change annotation runtime behavior,
model loading, parsing, output data, DLC submission logic, or tests.

## Context

The current repository already has useful documentation:

- `README.md` describes the project, quick start, current completion status, backends, and output behavior.
- `CLAUDE.md` contains repository rules, commands, architecture, current state, and agent documentation rules.
- `docs/dlc/README.md` is a maintained operator runbook for DLC jobs.
- `docs/superpowers/specs/` and `docs/superpowers/plans/` contain design and implementation process records.
- `docs/changes/` contains historical execution records from annotation repair, backfill, and DLC work.

The weakness is not missing content. The weakness is entrypoint and governance clarity:

- There is no `docs/index.md`, so maintainers must infer the documentation map from directory names.
- There is no root `AGENTS.md`, so cross-agent rules are mixed into `CLAUDE.md`.
- There is no project runtime lock equivalent to `GENESIS_RUNTIME_LOCK.md`.
- Historical records and current operator docs are both discoverable, but their roles are not named at the
  top level.
- Future documentation can drift because there are no small templates for design, operation records, and
  reference docs.

## Goals

1. Make the repository easier for humans and agents to enter safely.
2. Keep `README.md` focused on users and project overview.
3. Make `AGENTS.md` the root cross-agent rule document.
4. Keep `CLAUDE.md` as the Claude Code compatibility entrypoint, with less duplicate governance text.
5. Add `docs/index.md` as the canonical documentation table of contents.
6. Add `ANNOTATOR_RUNTIME_LOCK.md` to pin the validated runtime, data, backend, and evidence state.
7. Add lightweight documentation templates for future work.
8. Preserve all existing historical records and avoid broad path churn.

## Non-Goals

- No annotation job execution.
- No live API calls.
- No DLC job submission.
- No source-code behavior changes.
- No output dataset edits.
- No immediate bulk migration of every file under `docs/changes/`.
- No deletion of historical process records.
- No attempt to make all old records follow the new templates in this pass.

## Proposed Documentation Shape

The target shape follows a "Genesis-lite" pattern:

```text
.
├── AGENTS.md
├── ANNOTATOR_RUNTIME_LOCK.md
├── CLAUDE.md
├── README.md
├── archive/
│   └── README.md
└── docs/
    ├── index.md
    ├── design/
    │   └── README.md
    ├── operations/
    │   └── README.md
    ├── records/
    │   └── README.md
    ├── reference/
    │   └── README.md
    ├── templates/
    │   ├── design.md
    │   ├── operation-record.md
    │   └── reference.md
    ├── changes/
    ├── dlc/
    ├── development/
    ├── guidebook/
    ├── installation/
    ├── introduction/
    ├── superpowers/
    ├── troubleshooting/
    └── usage/
```

This design intentionally creates the new governance directories before moving old content into them.
`docs/changes/` remains valid as the historical record store for now. `docs/records/README.md` explains that
new dated records should use `docs/records/`, while older records remain under `docs/changes/` until a
separate migration pass.

## File Responsibilities

### `AGENTS.md`

Root cross-agent operating rules. It should contain:

- project context
- safety rules for annotation runs, API calls, and DLC submissions
- documentation requirements for agent work
- command quick reference
- directory quick reference
- current canonical docs entrypoints

It should be short enough for agents to read at session start.

### `CLAUDE.md`

Claude Code compatibility document. It should keep the commands and architecture details that are useful to
Claude Code, but it should point to `AGENTS.md` for cross-agent rules instead of being the only rule source.

### `docs/index.md`

Canonical docs index. It should answer:

- where to start
- what is current operational documentation
- where design docs live
- where records live
- what historical docs mean
- what the current status is

### `ANNOTATOR_RUNTIME_LOCK.md`

Validated project-state lock. It should pin:

- default runtime chain
- default local model path from checked-in config
- supported backends
- default prompt type
- output status and field completeness
- DLC profile/quota facts that are already documented
- validation evidence links
- verification checklist for future updates

This file should not contain secrets and should not include API keys.

### `archive/README.md`

Archive policy for historical lists and deprecated artifacts. It should state that archive content is for
reference and should not be treated as current operation input unless a maintained runbook explicitly says so.

### `docs/design/README.md`

Index for long-lived design documents. It can initially point to existing `docs/superpowers/specs/` and define
that future stable designs may be copied or summarized under `docs/design/`.

### `docs/operations/README.md`

Index for maintained runbooks. It should point at existing operational docs such as `docs/dlc/README.md`,
usage docs, configuration docs, and troubleshooting docs.

### `docs/records/README.md`

Index and policy for dated execution records. It should clarify the split:

- new records go under `docs/records/YYYY-MM-DD-topic.md`
- old records remain under `docs/changes/`
- `docs/changes/PROJECT_PROGRESS.md` remains the historical March 2026 milestone overview

### `docs/reference/README.md`

Index for stable reference material: output schema, prompt behavior, backend contracts, data layout, and command
surfaces. This pass creates the index only; detailed reference pages can be split later if needed.

### `docs/templates/*.md`

Small templates for future consistency. They must be concrete and short, with no placeholders that make the
template ambiguous.

## Documentation Rules

### Current vs Historical Framing

Current runbooks and indexes must describe the repository as it works now.

Historical records must keep their dated context and should not be rewritten to sound current unless they are
explicitly maintained operation docs.

### Evidence Links

Claims about validated state should link to evidence files:

- `docs/changes/PROJECT_PROGRESS.md` for March 2026 annotation completion
- `docs/dlc/README.md` for maintained DLC operation flow
- `docs/superpowers/specs/*` and `docs/superpowers/plans/*` for recent design and implementation decisions

### Runtime Safety

Docs must continue to warn that annotation commands can load large VLM weights and that API backend runs can
consume remote quota. No new documentation should encourage live model, API, or DLC execution without explicit
operator intent.

### No Broad Churn

This pass should add entrypoints and indexes, not rename every old document. Link stability matters more than a
perfectly clean taxonomy.

## Implementation Approach

Use four implementation tasks:

1. Add the root governance entrypoints: `AGENTS.md`, `ANNOTATOR_RUNTIME_LOCK.md`, and `archive/README.md`.
2. Add docs navigation and category indexes: `docs/index.md`, `docs/design/README.md`,
   `docs/operations/README.md`, `docs/records/README.md`, and `docs/reference/README.md`.
3. Add documentation templates under `docs/templates/`.
4. Reconcile `README.md` and `CLAUDE.md` so they point at the new governance layer without duplicating every rule.

Each task is independently reviewable and does not require runtime model execution.

## Validation Strategy

Use documentation-focused verification:

- `git diff --check`
- grep checks for new links and canonical entrypoints
- file existence checks for every linked document
- targeted pytest only if an available environment has both `torch` and `pytest`

Baseline note for this worktree:

- `python -m pytest tests -q` with the system Python produced `45 passed, 1 failed`.
- The failure was `ModuleNotFoundError: No module named 'torch'` in a local backend factory test.
- `.venv_dlc` has `torch 2.10.0+cu128` but does not have `pytest`.
- This is an environment baseline issue, not a documentation-change failure.

## Risks

### Risk: Documentation duplication

Mitigation: make new root files index and governance surfaces, not full copies of existing runbooks.

### Risk: Old links become stale

Mitigation: avoid moving existing docs in this pass. Add indexes and cross-links first.

### Risk: Agents treat historical records as current instructions

Mitigation: explicitly label `docs/changes/` as historical in `docs/index.md` and `docs/records/README.md`.

### Risk: Runtime lock drifts

Mitigation: add an update checklist to `ANNOTATOR_RUNTIME_LOCK.md` and link it from `AGENTS.md`.

## Self-Review

- No runtime behavior is changed.
- No live model, API, or DLC job is required.
- Existing docs remain at their current paths.
- The design covers the requested Genesis-like documentation normalization.
- The plan respects the user's instruction to continue without stopping for approval gates.
