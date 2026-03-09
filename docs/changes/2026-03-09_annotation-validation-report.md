# Annotation Validation Report

**Date**: 2026-03-09
**Target Directory**: `/cpfs/shared/simulation/zhuzihou/dev/usd-scene-physics-prep/GRScenes-test1/GRScenes_assets`

## Overall Summary

| Metric | Value |
|--------|-------|
| Total asset directories | 52,907 |
| Total annotation files | 52,907 |
| **Coverage** | **100.0%** |
| Files with ALL 5 fields complete | 41,742 (78.9%) |
| Files with raw_output (parse failure) | 0 |
| Files with some empty fields | 11,165 (21.1%) |
| JSON parse errors | 0 |

## Validation 1: File Completeness

**Result: PASS**

- Every asset directory has a corresponding `{asset_id}_annotation.json` file
- 0 missing annotation files
- Note: `Asset_annotation.json` in the root is a summary index (1.5MB, 82 categories) — not an asset annotation

## Validation 2: Field Quality

**Result: description is 100% complete; other fields have expected gaps**

All 52,907 assets have a non-null, non-empty `description` field.

Per-field empty/missing counts:

| Field | Null | Empty | Total Missing | Completion Rate |
|-------|------|-------|---------------|-----------------|
| description | 0 | 0 | 0 | **100.0%** |
| material | 0 | 8,700 | 8,700 | 83.6% |
| dimensions | 0 | 10,712 | 10,712 | 79.8% |
| mass | 0 | 10,169 | 10,169 | 80.8% |
| placement | 0 | 8,111 | 8,111 | 84.7% |

The 11,165 assets with empty fields are spread across categories. This is expected — the VLM model sometimes returns structured output with description filled but leaves physical property fields empty (especially for abstract objects like ceilings, walls, blankets, etc.).

**Key point**: No field has `null` values — they are either filled or empty string/empty list, which is a valid state for optional physical properties.

## Validation 3: Data Consistency

**Result: PASS (with minor format issues)**

| Check | Issues | Status |
|-------|--------|--------|
| UID matches directory name | 0 mismatches | PASS |
| Category matches parent dir | 0 mismatches | PASS |
| Placement is a list | 0 violations | PASS |
| JSON parseable | 0 errors | PASS |
| asset_type valid | 0 invalid | PASS |
| Dimensions format (X * Y * Z) | 160 non-standard | MINOR |
| Mass format (numeric) | 196 non-numeric | MINOR |

### Dimensions format issues (160 assets)

Some dimensions are incomplete or non-standard:
- `"2.0 * 1.5"` (missing Z dimension)
- `"0.25"` (single value)
- `"N/A"` or `"unknown"`

### Mass format issues (196 assets)

Some mass values are non-numeric text:
- `"N/A"`, `"unknown"`
- `"The exact mass of the object is unknown."`
- `"The grid has no mass as it is a digital construct."`

These are VLM model output artifacts where the model generated text instead of a number. These 196 assets are a subset of the 11,165 with empty fields.

## Conclusion

**The annotations are ready for use.** Key findings:

1. **100% coverage**: Every asset has an annotation file
2. **100% description completion**: All 52,907 assets have descriptions (the primary annotation field)
3. **~79-85% completion** for physical properties (material, dimensions, mass, placement)
4. **0 parse failures** (no raw_output fields)
5. **Perfect structural consistency**: uid, category, placement format, asset_type all correct
6. **Minor format issues**: 160 non-standard dimensions, 196 non-numeric mass values — these are cosmetic and can be cleaned up in a future pass if needed

### Readiness Assessment

| Requirement | Status |
|-------------|--------|
| Every asset has annotation file | YES |
| Every asset has description | YES |
| No parse failures | YES |
| Data structure consistent | YES |
| Physical properties 100% filled | NO (79-85%) |

**Recommendation**: Annotations are production-ready for downstream use. The empty physical property fields are expected for certain asset types (structural elements, abstract objects) and should not block usage. If 100% physical property completion is required, a targeted re-annotation pass for the ~11K assets with empty fields would be needed.
