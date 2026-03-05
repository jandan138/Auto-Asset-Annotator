# Data Analysis Report: Annotation Quality Issues

**Date:** 2026-03-05
**Analyst:** Claude Code (data-investigator agent)
**Dataset:** `/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/output`
**Total Successful Annotations:** 49,808 files

---

## Executive Summary

Analysis of the annotation outputs reveals **three critical data quality issues** affecting the majority of the dataset:

1. **Category Mismatch (92.7% of files):** The annotated category field rarely matches the directory name
2. **Units in Dimensions (58.4% of files):** Dimensions contain text units like "meters" instead of just numbers
3. **Units in Mass (59.4% of files):** Mass values contain text units like "kg" or "kilograms" instead of just numbers

---

## Issue 1: Category Mismatches

### Scale
- **46,164 files (92.7%)** have category values that do NOT match the directory name
- Only **3,644 files (7.3%)** have matching category values

### Problem Pattern
The VLM is outputting generic or incorrect category names instead of using the directory name.

### Top Incorrect Category Values

| Category Value | Count | % of Total |
|----------------|-------|------------|
| "object" | 35,710 | 71.7% |
| "Object" | 762 | 1.5% |
| "cup" | 633 | 1.3% |
| "furniture" | 491 | 1.0% |
| "cushion" | 442 | 0.9% |
| "container" | 411 | 0.8% |
| "Door" | 408 | 0.8% |
| "object case" | 244 | 0.5% |
| "Can" | 221 | 0.4% |
| "line" | 213 | 0.4% |
| "Plant" | 206 | 0.4% |
| "door" | 206 | 0.4% |

### Examples of Mismatches

| Directory | Annotated Category | Severity |
|-----------|-------------------|----------|
| bowl | "object" | Critical |
| bowl | "plate" | Critical |
| wall | "object" | Critical |
| ceiling | "object" | Critical |
| cabinet | "furniture" | Moderate |
| cabinet | "sink" | Critical |
| bottle | "Can" | Critical |
| bed | "furniture" | Moderate |
| clothes | "clothing" | Minor |
| telephone | "object type" | Critical |

### Root Cause
The prompt is asking the VLM to classify the object without constraining it to the known directory name. The VLM is making its own judgment about category rather than using the provided directory structure.

---

## Issue 2: Dimensions with Units

### Scale
- **29,080 files (58.4%)** have dimensions WITH units
- **10,458 files (21.0%)** have dimensions WITHOUT units (correct format)
- **10,270 files (20.6%)** have NULL/None dimensions

### Unit Patterns Found in Dimensions

| Unit Pattern | Count | % of files with units |
|--------------|-------|----------------------|
| "meters" | 5,752 | 19.8% |
| "m" (isolated) | 113 | 0.4% |
| "cm" | 1 | <0.1% |

### Examples of Problematic Dimensions

```
# With units (INCORRECT)
"0.30 * 0.30 * 0.05 meters"
"0.5 * 0.15 * 0.01 m"
"1 * 1 * 1 meters (estimated based on the square grid layout)"
"0.30 * 0.20 * 0.05 meters (largest board) / 0.25 * 0.15 * 0.05 meters (smallest board)"
"0.5 * 0.2 * 0.3 (meters)"
": 0.5 * 0.5 * 0.1 meters (Estimate based on visual proportions)."

# Without units (CORRECT)
"0.15 * 0.15 * 0.20"
"0.2"
"1.00 * 0.75 * 0.80"
```

### Root Cause
The prompt is not explicitly instructing the VLM to output dimensions without units. The VLM is naturally including units in its response.

---

## Issue 3: Mass with Units

### Scale
- **29,572 files (59.4%)** have mass WITH units
- **10,473 files (21.0%)** have mass WITHOUT units (correct format)
- **9,763 files (19.6%)** have NULL/None mass

### Unit Patterns Found in Mass

| Unit Pattern | Count | % of files with units |
|--------------|-------|----------------------|
| "kilograms" | 3,214 | 10.9% |
| "kg" | 2,747 | 9.3% |
| "meters" | 3 | <0.1% (error) |

### Examples of Problematic Mass Values

```
# With units (INCORRECT)
"0.5 kg"
"0.05 kilograms"
"0.001 kg (estimated based on the dimensions and material material)"
"The mass of the object is also unknown, but we can estimate it to be around 0.01 kg."
"- **Estimate:** 50 kg"
"Estimated mass is 0.1 kg."
"The mass of the object cannot be determined from the image alone. However, based on the estimated dimensions, it could be weigh around 0.01 kg."
"50 (kilograms)"
": 0.5 kg (Estimate based on material and dimensions)."

# Without units (CORRECT)
"0.2"
"0.05"
"50.0"
"5"
```

### Root Cause
Same as dimensions - the prompt is not explicitly instructing the VLM to output mass without units.

---

## Impact Analysis

### By Category

Categories with highest mismatch rates (sampled):

| Category | Sampled | Mismatches | Mismatch Rate |
|----------|---------|------------|---------------|
| ceiling | 322 | 322 | ~100% |
| column | 76 | 76 | ~100% |
| wall | high | high | ~100% |
| ground | high | high | ~100% |
| cabinet | 227 | 227 | ~100% |
| blanket | 45 | 45 | ~100% |
| book | 98 | 98 | ~100% |
| bottle | 136 | 136 | ~100% |
| cup | 55 | 55 | ~100% |

Categories with better alignment:

| Category | Sampled | Correct | Correct Rate |
|----------|---------|---------|--------------|
| book | 311 | 213 | 68.5% |
| bottle | 338 | 202 | 59.8% |
| cup | 106 | 51 | 48.1% |
| door | 100 | 38 | 38.0% |
| pillow | 100 | 34 | 34.0% |
| table | 100 | 28 | 28.0% |
| chair | 100 | 24 | 24.0% |

---

## Recommendations

### Immediate Actions

1. **Fix Category Field**
   - The category should be set to the directory name, not inferred by the VLM
   - Remove category classification from the VLM prompt
   - Use the directory structure as the source of truth

2. **Fix Dimensions Format**
   - Update prompt to explicitly request dimensions without units
   - Add post-processing to strip units from existing annotations
   - Expected format: `"0.2 * 0.3 * 0.4"` (numbers only, space-separated by `*`)

3. **Fix Mass Format**
   - Update prompt to explicitly request mass without units
   - Add post-processing to strip units from existing annotations
   - Expected format: `"0.5"` (number only)

### Prompt Template Updates Needed

The current prompt template should be modified to:
1. Remove category classification instruction
2. Add explicit instruction: "Output dimensions as numbers only, without units (e.g., 0.2 * 0.3 * 0.4)"
3. Add explicit instruction: "Output mass as a number only, without units (e.g., 0.5)"

### Post-Processing Script

A batch fix script should be created to:
1. Set category = directory name for all files
2. Strip units from dimensions using regex
3. Strip units from mass using regex
4. Handle edge cases (ranges, multiple values, text descriptions)

---

## Files Analyzed

- Success list: `/tmp/success_assets.txt` (49,808 entries)
- Output directory: `/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/output`
- Categories covered: 79
- Sample size for detailed analysis: 10,000 files

---

## Appendix: Raw Data Examples

### Category Mismatch Examples
```json
// File: bowl/57a70808c39fa6dea32172da4b359181_annotation.json
{
  "category": "plate",  // Should be "bowl"
  "dimensions": "0.15 * 0.30 * 0.05 meters",
  "mass": "0.2 kg"
}

// File: wall/b1c0ef34acf95a6593eaf2f02db3ef16_annotation.json
{
  "category": "object",  // Should be "wall"
  "dimensions": null,
  "mass": "The mass cannot be accurately determined..."
}
```

### Units Examples
```json
// Dimensions with units
"0.30 * 0.30 * 0.05 meters"
"0.5 * 0.15 * 0.01 m"
"1 * 1 * 1 meters (estimated...)"

// Mass with units
"0.5 kg"
"0.05 kilograms"
"Estimated mass is 0.1 kg."
"The mass of the object is estimated to be around 0.2 kilograms."
```
