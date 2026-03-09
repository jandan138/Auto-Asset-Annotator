# Fill Default Physical Properties for 2,148 Incomplete Assets

**Date**: 2026-03-09

## Summary

Filled empty physical property fields (material, mass, placement) for 2,148 assets using category-based default values. Dimensions were intentionally left unfilled as they are too model-specific to generalize.

## Background

After two rounds of VLM annotation, 2,148 assets (4.1%) still had empty physical property fields. These were predominantly structural elements (wall: 504, ground: 461, other: 530, ceiling: 62) where the VLM struggled to generate meaningful physical properties.

Running another VLM annotation round would yield minimal improvement for these categories. Instead, we filled defaults derived from statistical analysis of 50k+ existing annotations.

## Implementation

### New script: `scripts/fill_defaults.py`

- Reads an asset list file and fills empty fields with category-based defaults
- Contains `CATEGORY_DEFAULTS` mapping for 40+ categories with material, mass, and placement values
- Falls back to `_default` for unknown categories
- Fixes invalid mass formats (e.g., "N/A", "unknown") by replacing with defaults
- Supports dry-run mode (default) and `--apply` for actual writes
- Optional `--fill_dimensions` flag (disabled by default)

### Default values source

Values were derived from:
- **material**: Most common material description per category
- **mass**: Median mass value per category (in kg)
- **placement**: Most frequent placement value per category

### Execution

```bash
# Dry-run
python scripts/fill_defaults.py --output_dir ./output --asset_list remaining_incomplete.txt

# Apply
python scripts/fill_defaults.py --output_dir ./output --asset_list remaining_incomplete.txt --apply

# Propagate to target directory
python scripts/fill_annotations.py --apply
```

## Results

### Fill statistics
- Assets processed: 2,148
- Assets updated: 2,055 (93 already had all 3 fields filled)
- Field fills: material=1,434, mass=1,733, placement=1,256
- Mass format fixes: 24 (non-numeric values replaced)
- Categories using fallback defaults: `other`

### Final field completion (target directory, 52,907 assets)

| Field | Empty | Completion |
|-------|-------|------------|
| description | 0 | 100.0% |
| material | 0 | 100.0% |
| mass | 0 | 100.0% |
| placement | 0 | 100.0% |
| dimensions | 1,911 | 96.4% |

### Why dimensions remain empty

Dimensions are highly dependent on the specific 3D model geometry and cannot be meaningfully inferred from category alone. Within the same category (e.g., "bottle"), dimensions can range from 5cm to 50cm. A default value would be misleading.

## Files Changed

| File | Change |
|------|--------|
| `scripts/fill_defaults.py` | New script |
| `CLAUDE.md` | Updated utility scripts section and project status |
| `output/{cat}/{id}_annotation.json` | 2,055 files updated with default values |
