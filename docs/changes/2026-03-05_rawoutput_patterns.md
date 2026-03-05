# Raw Output Pattern Analysis

**Date:** 2026-03-05
**Total Failed Files Analyzed:** 283

## Executive Summary

Analysis of failed annotation files (those containing `raw_output` fields) reveals distinct patterns in model output failures. The vast majority (96.1%) are due to a specific model output issue where the model outputs "**Image" followed only by newlines. The remaining failures are primarily due to multi-object outputs that the current parser cannot handle.

---

## Category Breakdown

### 1. Too Short / Image-Only Output (96.1% - 272 files)

**Pattern:** The model outputs "**Image" followed by many newlines and nothing else.

**Sample Content:**
```
**Image





...(500+ newlines)...
```

**Root Cause:** This appears to be a model failure where the VLM (Qwen2.5-VL-7B-Instruct) starts to respond but fails to generate actual content. This may be due to:
- Image encoding/processing issues
- Model context limitations
- Corrupted or unreadable input images

**Fixability:** NO - These require re-annotation

**Recommended Approach:**
- Re-annotate with the same prompt
- Consider retry with different image format or resolution
- If persistent, flag for manual review

---

### 2. Has Headers But Malformed (3.2% - 9 files)

**Pattern:** The output contains valid structured data with Category, Description, Material, Dimensions, Mass, and Placement fields, but in a multi-object format that the parser doesn't handle correctly.

**Sample Content:**
```markdown
**Object 1: Ruler**

* **Category:** Measuring Tool
* **Description:** The ruler has a straight, elongated shape...
* **Material:** The ruler is made of plastic...
* **Dimensions:** 0.25 * 0.01 * 0.005 meters
* **Mass:** 0.05 kg
* **Placement:** OnTable

**Object 2: Toothpick**
...
```

**Root Cause:** The model correctly identifies multiple objects in the image and provides structured output for each, but the parser expects single-object output and fails to extract any data.

**Fixability:** YES - Can be fixed with parser improvements

**Recommended Approach:**
- Enhance `parse_structured_text()` to detect multi-object output (patterns like "Object 1:", "Object 2:")
- Extract only the first object (primary object) for now
- Consider adding multi-object support in future

---

### 3. Multi-Object or List (0.4% - 1 file)

**Pattern:** Incomplete or corrupted multi-object output with section headers.

**Sample Content:**
```markdown
### Object 1: F

 addCriterion
### Object 2:
```

**Root Cause:** Model started generating multi-object output but was cut off or corrupted.

**Fixability:** NO - Requires re-annotation

**Recommended Approach:**
- Re-annotate with single-object focus prompt
- Consider increasing `max_new_tokens` if output is being truncated

---

### 4. Narrative No Structure (0.4% - 1 file)

**Pattern:** Very long output with repetitive text (likely model hallucination/repetition loop).

**Sample Content:**
```
| Category | object |
| Description | The object appears to be a slender, elongated rod...
there there there there there there there there there there...
(repeated 100+ times)
```

**Root Cause:** Model entered a repetition loop, generating "there" repeatedly.

**Fixability:** NO - Requires re-annotation

**Recommended Approach:**
- Re-annotate
- Consider adjusting temperature or sampling parameters
- May indicate problematic/low-quality input images

---

## Additional Observations

### The "addCriterion" Corruption

Some "successful" parses contain "addCriterion" text corruption in the output:

**Example:**
```json
{
    "description": "The object appears to be a circular dish... \n addCriterion: functional purpose...",
    "material": "The object is likely made of ceramic..."
}
```

This appears to be a model artifact that leaks through the parser. The parser should be enhanced to:
1. Strip "addCriterion" and related artifacts from output
2. Clean up repetitive text patterns

### Multi-Object Output Prevalence

Of the non-"Image-only" failures, approximately 90% are due to multi-object output format. The model is correctly identifying multiple objects but the parser cannot handle this format.

---

## Fixability Summary

| Category | Count | Percentage | Fixable via Parser | Needs Re-annotation |
|----------|-------|------------|-------------------|---------------------|
| Too Short (Image-only) | 272 | 96.1% | No | Yes |
| Has Headers But Malformed | 9 | 3.2% | Yes | No |
| Multi-Object or List | 1 | 0.4% | No | Yes |
| Narrative No Structure | 1 | 0.4% | No | Yes |
| **Total** | **283** | **100%** | **9 (3.2%)** | **274 (96.8%)** |

---

## Recommendations

### Immediate Actions

1. **Implement Multi-Object Parser Support** (addresses 3.2% of failures)
   - Detect patterns like `**Object 1:**`, `### Object 1:`, `1. Object:`
   - Extract first object only for consistency
   - Strip markdown formatting (`**`, `*`, `#`)

2. **Add Output Cleaning** (improves quality of existing parses)
   - Remove "addCriterion" artifacts
   - Remove repetition patterns (e.g., "there there there...")
   - Strip trailing newlines and whitespace

### For Re-annotation

3. **Retry Strategy for Image-only Failures** (96.1% of failures)
   - These should be re-annotated as-is
   - Monitor for patterns in which assets consistently fail
   - Consider image quality preprocessing

4. **Prompt Improvements** (future work)
   - Add explicit instruction: "Describe ONLY the main object"
   - Add: "Do not use markdown formatting in your response"
   - Consider few-shot examples with correct format

### Parser Enhancement Pseudocode

```python
def parse_structured_text_enhanced(text: str) -> Dict[str, str]:
    """Enhanced parser with multi-object support."""

    # Step 1: Clean input
    text = clean_artifacts(text)  # Remove addCriterion, etc.

    # Step 2: Check for multi-object output
    if re.search(r'(?:Object\s+\d+|^\s*\*\*Object)', text, re.MULTILINE):
        # Extract first object only
        text = extract_first_object(text)

    # Step 3: Parse as usual
    return parse_structured_text(text)

def clean_artifacts(text: str) -> str:
    """Remove model artifacts from output."""
    # Remove addCriterion
    text = re.sub(r'\s*addCriterion:?\s*', ' ', text)
    # Remove repetition patterns
    text = re.sub(r'(\b\w+\b)(\s+\1){3,}', ' \1', text)
    return text.strip()

def extract_first_object(text: str) -> str:
    """Extract only the first object from multi-object output."""
    # Match from "Object 1:" or "**Object 1:**" until "Object 2:" or end
    pattern = r'(?:^|\n)[\*#\-]*\s*Object\s+1:?\s*\**\s*[^\n]*\n([\s\S]*?)(?=(?:^|\n)[\*#\-]*\s*Object\s+2:|$)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text
```

---

## Files Referenced

- Analysis script: `/tmp/analyze_raw_output.py`
- Raw results: `/tmp/analysis_results.json`
- Failed file list: `/tmp/failed_files.txt`

## Sample Files by Category

### Too Short (Image-only)
- `output/other/11bd153a8a041318959a8cb4be66a1bf_annotation.json`
- `output/other/ef7065ff1ccbdcdd2a12485c1d55391d_annotation.json`
- `output/door/64bbf94de1b2be41c9894d65ecd4e4bc_annotation.json`

### Has Headers But Malformed (Multi-Object)
- `output/other/e8f638fd49cc32ef146bbde38dbb3ef7_annotation.json`
- `output/other/ed3dc948ef56e5faad857dd9b944291c_annotation.json`
- `output/decoration/0088042581bb42e17c35bb0cd64461da_annotation.json`

### Multi-Object or List
- `output/other/4e53b07207a412802b79659597eaecc2_annotation.json`

### Narrative No Structure
- `output/picture/d30922687b71461cccad92f4ee5c320e_annotation.json`
