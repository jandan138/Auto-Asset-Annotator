# Failed Annotations Investigation - Final Summary

**Date:** 2026-03-05
**Total Failed Annotations:** 283 (0.56% of 50,091)
**Status:** Investigation Complete, Parser Improvements Implemented

---

## Executive Summary

We investigated 283 failed annotation files (those containing `raw_output` fields) and discovered:

- **96.1%** are due to a model failure producing only `"**Image"` with whitespace
- **3.2%** are multi-object outputs that the parser couldn't handle
- **0.7%** are truncated or other edge cases

We implemented parser improvements to handle multi-object outputs and created a re-annotation strategy for the rest.

---

## Failure Categories

### 1. Image-Only Failures (272 files, 96.1%) - Primary Issue

**Symptom:** The model outputs only `**Image` followed by newlines

```
**Image



...(500+ newlines)...
```

**Root Cause:**
- VLM (Qwen2.5-VL-7B-Instruct) fails to generate content
- Possible causes: image encoding issues, model context limitations, corrupted input images
- This is a model-level failure, not a parser issue

**Fixability:** NO - These require re-annotation

**Action:**
- Use `scripts/reannotate_failures.py` to generate retry list
- Re-annotate with main pipeline
- Monitor for patterns (e.g., specific assets consistently failing)

---

### 2. Multi-Object Outputs (8 files, 2.8%) - Parser Issue (FIXED)

**Symptom:** Model correctly identifies multiple objects but parser fails

```markdown
**Object 1: Ruler**
* **Category:** Measuring Tool
* **Description:** The ruler has a straight shape...

**Object 2: Toothpick**
* **Category:** Tool
...
```

**Root Cause:** Parser expected single-object format

**Fixability:** YES - Fixed with enhanced parser

**Implementation:**
- Added `_is_multi_object_output()` detection
- Added `_extract_first_object()` extraction
- Parser now extracts first object only for consistency

**Status:** ✅ RESOLVED in pipeline.py

---

### 3. Truncated Outputs (2 files, 0.7%) - Model Issue

**Symptom:** Output cut off mid-generation

```
### Object 1: F
 addCriterion
### Object 2:
```

**Root Cause:** Model was interrupted or hit token limit

**Fixability:** NO - Requires re-annotation

**Action:**
- Re-annotate these files
- Consider increasing `max_new_tokens` if pattern persists

---

### 4. Other Format (1 file, 0.4%) - Model Issue

**Symptom:** Markdown table format with repetition artifacts

**Root Cause:** Model hallucination/repetition

**Fixability:** NO - Requires re-annotation

---

## Parser Improvements Implemented

### Changes to `src/auto_asset_annotator/core/pipeline.py`

1. **`parse_structured_text_enhanced()`** (line 214)
   - Orchestrates cleaning and extraction pipeline
   - Used instead of `parse_structured_text()` in `process_asset()`

2. **`_clean_artifacts()`** (line 149)
   - Removes `addCriterion` corruption
   - Removes `**Image` prefix lines
   - Removes word repetition patterns

3. **`_is_multi_object_output()`** (line 172)
   - Detects multi-object patterns like "Object 1:"

4. **`_extract_first_object()`** (line 189)
   - Extracts only first object from multi-object output

### Test Results

```
$ python test_parser_robustness.py -v
test_messy_format (__main__.TestPipeline) ... ok
test_missing_fields (__main__.TestPipeline) ... ok
test_multi_object_parsing (__main__.TestPipeline) ... ok

----------------------------------------------------------------------
Ran 3 tests in 0.002s

OK
```

---

## New Tools Created

### 1. `scripts/reannotate_failures.py`

**Purpose:** Analyze and prepare failed annotations for re-processing

**Usage:**
```bash
# Analyze failures
python scripts/reannotate_failures.py --output_dir ./output --analyze-only

# Save list for re-annotation
python scripts/reannotate_failures.py --output_dir ./output \
    --filter_type image_only --save_list failed_assets.txt

# Use with main pipeline
python -m auto_asset_annotator.main \
    --asset_list_file failed_assets.txt \
    --input_dir /path/to/input \
    --output_dir ./output \
    --force
```

**Features:**
- Categorizes failures (image_only, multi_object, truncated, other)
- Generates statistics by category
- Filters specific failure types
- Generates retry lists

---

## Current Status of 283 Failed Files

| Category | Count | Parser Fix | Re-annotation Needed |
|----------|-------|------------|---------------------|
| image_only | 272 | ❌ | ✅ Yes |
| multi_object | 8 | ✅ Fixed | ❌ No |
| truncated | 2 | ❌ | ✅ Yes |
| other | 1 | ❌ | ✅ Yes |
| **Total** | **283** | **8 fixed** | **275 needed** |

---

## Recommendations

### Immediate Actions

1. **Retry Multi-Object Files** (already fixed by parser)
   - These will parse correctly on next pipeline run
   - Can be re-processed with the enhanced parser

2. **Re-annotate Image-Only Failures** (275 files)
   ```bash
   python scripts/reannotate_failures.py --output_dir ./output \
       --save_list stubborn_assets.txt
   # Then re-run with main pipeline
   ```

### Future Improvements

3. **Prompt Engineering**
   - Add instruction: "Describe ONLY the main object"
   - Add: "Do not use markdown formatting"
   - Consider few-shot examples

4. **Image Quality Checks**
   - Pre-validate images before VLM inference
   - Detect corrupted/unreadable images

5. **Retry Logic Enhancement**
   - Implement automatic retry with different prompts
   - Track consistently failing assets

---

## Files Created/Modified

| File | Change |
|------|--------|
| `src/auto_asset_annotator/core/pipeline.py` | Added enhanced parser methods |
| `scripts/reannotate_failures.py` | New - failure analysis tool |
| `docs/changes/2026-03-05_failed_annotations_analysis.md` | Data analysis report |
| `docs/changes/2026-03-05_rawoutput_patterns.md` | Pattern categorization |
| `docs/changes/2026-03-05_parser_implementation.md` | Implementation details |
| `test_parser_robustness.py` | Updated with multi-object test |

---

## Next Steps

1. ✅ Parser improvements implemented and tested
2. ⏳ Run `reannotate_failures.py` to generate retry list
3. ⏳ Re-annotate 275 stubborn assets with main pipeline
4. ⏳ Monitor for patterns in consistently failing assets

---

## Appendix: Sample Commands

```bash
# Quick analysis
python scripts/reannotate_failures.py --output_dir ./output --analyze-only

# Generate retry list for stubborn assets
python scripts/reannotate_failures.py --output_dir ./output \
    --filter_type image_only --save_list stubborn_assets.txt

# Verify parser improvements
python test_parser_robustness.py -v
```
