# Backfill Incomplete Physical Properties

**Date**: 2026-03-09

## Context

After completing all 52,907 asset annotations and fixing 42 null descriptions, validation revealed that 11,418 assets (21.5%) had empty physical property fields (material, dimensions, mass, placement). The description field was 100% complete. Root cause: VLM model `addCriterion` corruption artifacts causing parse failures on physical property fields while description was captured.

## Infrastructure Changes

### New Scripts

1. **`scripts/find_incomplete_assets.py`** — Finds assets with empty/invalid physical property fields
   - Supports `--strict` mode (also flags invalid formats like "N/A", "unknown")
   - Supports `--stats` for per-category breakdown
   - Output compatible with `--asset_list_file` parameter

2. **`scripts/merge_annotations.py`** — Selective field merge
   - Only fills empty/invalid fields from new annotations
   - Preserves existing valid data (especially descriptions)
   - Validates dimensions (X * Y * Z) and mass (numeric) format
   - Default dry-run mode with `--apply` flag

### Modified Files

3. **`src/auto_asset_annotator/main.py`** — Added `--retry_incomplete` CLI parameter
   - When set, re-processes assets with empty material/dimensions/mass/placement
   - Does not affect existing `--force` or `raw_output` retry logic

4. **`CLAUDE.md`** — Updated commands and utility scripts documentation

## DLC Re-annotation

### Submission

```bash
python scripts/dlc/submit_batch.py --total 8 --name reannotate_incomplete \
    --command_args "--input_dir /cpfs/shared/simulation/zhuzihou/dev/usd-scene-physics-prep/GRScenes-test1/GRScenes_assets \
    --asset_list_file incomplete_assets.txt --output_dir ./output_reannotate --force"
```

### Jobs

| Job Name | Job ID | Status |
|----------|--------|--------|
| reannotate_incomplete_0_8 | dlc1xpp8uhn92ll4 | Succeeded |
| reannotate_incomplete_1_8 | dlc1y9ofm1tp9crh | Succeeded |
| reannotate_incomplete_2_8 | dlc1yjo0zte0s2sf | Succeeded |
| reannotate_incomplete_3_8 | dlc02kkcpz2ea5v0 | Succeeded |
| reannotate_incomplete_4_8 | dlcmjr49khq39oh1 | Succeeded |
| reannotate_incomplete_5_8 | dlcwjci17twvpfzl | Succeeded |
| reannotate_incomplete_6_8 | dlc16ixvt5p6kwp8 | Succeeded |
| reannotate_incomplete_7_8 | dlc1gij9lkdgywu5 | Succeeded |

All 8 jobs succeeded, producing 11,418 new annotation files in `output_reannotate/`.

### Re-annotation Quality

- Parse success rate: 99.82% (20 failures out of 11,418)
- Description: 99.95% complete
- Physical properties: 82-85% complete (remaining gaps are structural categories)
- Only ~18 files had genuinely malformed non-empty field values

## Merge Results

```bash
python scripts/merge_annotations.py --old_dir ./output --new_dir ./output_reannotate --apply
```

| Metric | Value |
|--------|-------|
| Files updated | 9,783 |
| Files skipped | 1,635 |
| material fields filled | 7,266 |
| dimensions fields filled | 8,975 |
| mass fields filled | 8,632 |
| placement fields filled | 6,855 |
| New annotation also empty | 6,282 field instances |

## Propagation

```bash
python scripts/fill_annotations.py --apply
```

9,783 target files updated in GRScenes_assets, 0 failures.

## Before vs After

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **All 5 fields complete** | **41,742 (78.9%)** | **50,798 (96.0%)** | **+9,056** |
| description complete | 52,907 (100%) | 52,907 (100%) | unchanged |
| material empty | 8,700 (16.4%) | 1,434 (2.7%) | -7,266 |
| dimensions empty | 10,712 (20.2%) | 1,911 (3.6%) | -8,801 |
| mass empty | 10,169 (19.2%) | 1,709 (3.2%) | -8,460 |
| placement empty | 8,111 (15.3%) | 1,256 (2.4%) | -6,855 |
| raw_output failures | 0 | 0 | unchanged |

## Remaining Gaps

2,148 assets (4.1%) still have some empty physical property fields. Top categories:

| Category | Incomplete | Total | Rate |
|----------|-----------|-------|------|
| other | 530 | 12,210 | 4.3% |
| wall | 504 | 15,961 | 3.2% |
| ground | 461 | 10,107 | 4.6% |
| bottle | 128 | 1,698 | 7.5% |
| ceiling | 62 | 1,610 | 3.9% |
| faucet | 33 | 64 | 51.6% |

These are predominantly structural elements (wall, ground, ceiling) where physical properties are inherently ambiguous, or complex geometry (faucet) that confuses the VLM.

## Recommendation

The **96.0% completion rate** is production-ready. Options for the remaining 4.1%:

1. **Accept current state** (recommended) — remaining gaps are structural/abstract assets
2. Manual annotation of the 2,148 remaining assets if 100% is required
3. Third VLM pass with modified prompts (diminishing returns expected)
