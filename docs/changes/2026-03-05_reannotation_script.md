# Re-annotation Script Implementation

**Date:** 2026-03-05
**Script:** `/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/scripts/reannotate_failures.py`

## Overview

Created a comprehensive re-annotation script for analyzing and retrying failed asset annotations. The script scans output directories for annotation files containing `raw_output` fields (indicating parse failures) and categorizes them for targeted retry strategies.

## Features

### 1. Failure Detection
- Scans all `*_annotation.json` files in the output directory
- Identifies files with `raw_output` field (failed parses)
- Progress bar shows scanning status

### 2. Failure Categorization

The script categorizes failures into four types:

| Type | Description | Count | Percentage |
|------|-------------|-------|------------|
| `image_only` | Output contains only "**Image" with whitespace | 272 | 96.1% |
| `multi_object` | Output contains "Object 1", "Object 2" format | 8 | 2.8% |
| `truncated` | Output ends with "...", ":", or mid-word | 2 | 0.7% |
| `other` | Unrecognized format | 1 | 0.4% |

**Total failed annotations: 283 out of 50,091 (0.56%)**

### 3. Category Distribution

Top 10 categories by failure count:

1. window: 71 failures
2. door: 53 failures
3. book: 47 failures
4. picture: 38 failures
5. other: 35 failures
6. cabinet: 11 failures
7. mirror: 4 failures
8. decoration: 4 failures
9. clock: 3 failures
10. wall: 3 failures

### 4. Command-Line Interface

```bash
# Analyze failures without re-annotation (dry run)
python scripts/reannotate_failures.py --output_dir ./output --analyze-only

# Save all failed assets to a list
python scripts/reannotate_failures.py --output_dir ./output --save_list failed_assets.txt

# Save only specific failure type
python scripts/reannotate_failures.py --output_dir ./output \
    --filter_type image_only --save_list image_only_failures.txt
```

### 5. Integration with Main Pipeline

The generated asset list can be used with the main annotation pipeline:

```bash
python -m auto_asset_annotator.main \
    --asset_list_file failed_assets.txt \
    --input_dir /path/to/input \
    --output_dir ./output \
    --force
```

## Implementation Details

### Detection Patterns

```python
# Image-only failure: just "**Image" with optional whitespace
re.match(r'^\s*\*\*Image\s*$', text.strip())

# Multi-object format: "Object 1", "Object 2", etc.
re.search(r'(?:^|\n)[\*#\-]*\s*Object\s+\d+', text, re.IGNORECASE)

# Truncated output: ends with ellipsis, colon, or mid-word
text.rstrip().endswith(('...', ':', ' -', 'Object', 'Category'))
```

### Output Format

The saved asset list contains one asset ID per line:
```
other/54380a0b11e74a3936ff752c15419475
other/1689cb72bf2e6bf0640ae0548b402248
window/abc123...
```

## Test Results

### Analysis Mode
```bash
$ python scripts/reannotate_failures.py --output_dir ./output --analyze-only

============================================================
FAILED ANNOTATION ANALYSIS
============================================================
Total failed: 283

By Failure Type:
  image_only     :  272 ( 96.1%)
  multi_object   :    8 (  2.8%)
  truncated      :    2 (  0.7%)
  other          :    1 (  0.4%)

Top 10 Categories by Failure Count:
  window              :  71
  door                :  53
  book                :  47
  ...
```

### Filtered List Generation
```bash
$ python scripts/reannotate_failures.py --output_dir ./output \
    --filter_type image_only --save_list image_only_failures.txt

Saved 272 assets to image_only_failures.txt
```

## Recommendations for Retry Strategy

Based on the analysis:

1. **Image-only failures (96.1%)**: These are likely model failures where the VLM only output the image token. Retry with:
   - Same prompt (model may succeed on retry)
   - Consider adjusting `max_new_tokens` if truncation is suspected

2. **Multi-object format (2.8%)**: The model detected multiple objects. Options:
   - Accept first object (Object 1)
   - Use specialized single-object prompt
   - Manual review for complex scenes

3. **Truncated outputs (0.7%)**: Likely hit token limit. Retry with:
   - Increased `max_new_tokens` (e.g., 4096)
   - More concise prompt

4. **Other (0.4%)**: Manual review recommended

## Files Created

- `/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/scripts/reannotate_failures.py` - Main script
- `image_only_failures.txt` - Example filtered list (272 assets)
