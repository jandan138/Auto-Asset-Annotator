# Pipeline Failure Analysis Report

**Date:** 2026-03-05
**Scope:** Analysis of raw_output fallback conditions in the annotation pipeline
**Files Analyzed:**
- `/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/src/auto_asset_annotator/core/pipeline.py`
- `/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/src/auto_asset_annotator/core/prompt.py`

---

## Executive Summary

The pipeline produces `raw_output` when the structured text parser fails to extract valid key-value pairs from the model's response. This report documents the exact conditions, code paths, and failure modes.

---

## 1. Code Paths Leading to raw_output

There are **three distinct code paths** that result in `raw_output` being saved instead of structured data:

### Path 1: Empty Result from Parser (lines 66-68)

```python
# In process_asset() method, lines 63-68
if "json" in prompt_type.lower() or "extract" in prompt_type.lower():
    try:
        result = self.parse_structured_text(result_text)
        if not result:  # Empty dict evaluates to False
            print(f"[WARN] No structured data found for {asset_id}. Saving raw text.")
            result = {"raw_output": result_text}
```

**Trigger:** `parse_structured_text()` returns `{}` (empty dictionary)

### Path 2: Exception During Parsing (lines 82-84)

```python
# In process_asset() method, lines 82-84
    except Exception as e:
        print(f"[WARN] Failed to parse structured text for {asset_id}: {e}. Saving raw text.")
        result = {"raw_output": result_text}
```

**Trigger:** Any unhandled exception during `parse_structured_text()` execution

### Path 3: All Values Are None (lines 157-158 in parse_structured_text)

```python
# In parse_structured_text() method, lines 157-158
if all(v is None for v in result.values()):
    return {}
```

**Trigger:** Parser finds no matches for any of the expected keys, resulting in all values being `None`

---

## 2. Parser Behavior Analysis

### 2.1 Regex Pattern Details (lines 140-143)

The parser uses a sophisticated regex pattern for each expected key:

```python
pattern = r"(?:^|\n)[\*#\-]*\s*(" + key + r")\s*:\s*([\s\S]*?)(?=(?:^|\n)[\*#\-]*\s*(?:Category|Description|Material|Dimensions|Mass|Placement)\s*:|$)"
```

**Pattern Breakdown:**

| Component | Meaning |
|-----------|---------|
| `(?:^|\n)` | Start of string or new line |
| `[\*#\-]*` | Optional markdown bullets/headers (`*`, `#`, `-`) |
| `\s*` | Optional whitespace |
| `(` + key + `)` | The expected key name (Category, Description, etc.) |
| `\s*:\s*` | Colon with optional surrounding whitespace |
| `([\s\S]*?)` | Capture content (lazy match, includes newlines) |
| `(?=...)` | Positive lookahead to stop at next key or end |

### 2.2 Keys Expected (line 114)

```python
keys = ["Category", "Description", "Material", "Dimensions", "Mass", "Placement"]
```

### 2.3 Value Cleaning (lines 146-150)

```python
value = match.group(2).strip()
# Clean up value: remove leading "** " if present (common artifact)
value = re.sub(r'^[\*#\-]*\s*', '', value)
# Normalize key to lowercase for consistency
result[key.lower()] = value
```

### 2.4 Missing Key Handling (lines 151-153)

```python
else:
    # If key missing, set to None
    result[key.lower()] = None
```

---

## 3. Failure Conditions Summary

### 3.1 Condition A: No Keys Matched

**Scenario:** The model output contains none of the expected keys.

**Example outputs that would trigger this:**
```
"This is a red chair made of wood."
```
(No "Category:", "Description:", etc. headers)

**Result:** `parse_structured_text()` returns `{}` → triggers raw_output

### 3.2 Condition B: All Values None

**Scenario:** Keys are present but regex fails to capture values (rare due to `.*` fallback).

**Example outputs that would trigger this:**
```
Category:
Description:
Material:
```
(Empty values after colons)

**Result:** `all(v is None for v in result.values())` is True → returns `{}` → triggers raw_output

### 3.3 Condition C: Exception During Parsing

**Scenario:** Unexpected error in regex execution or string processing.

**Possible causes:**
- Memory issues with very large responses
- Encoding/decoding errors
- Invalid regex state

**Result:** Exception caught → triggers raw_output with error message

### 3.4 Condition D: Partial Matches (DOES NOT trigger raw_output)

**Important:** If at least one key is matched with a non-empty value, the parser returns partial results.

**Example:**
```
Category: chair
Description: A wooden chair
```
(Missing Material, Dimensions, Mass, Placement)

**Result:** Returns `{"category": "chair", "description": "A wooden chair", "material": None, ...}`
**Does NOT trigger raw_output** - partial data is accepted

---

## 4. Prompt Analysis

### 4.1 Expected Format (from prompt.py, lines 63-78)

The `extract_object_attributes_prompt` explicitly requests:

```
Required format:
Category: object type (will be set automatically from directory name)
Description: comprehensive description covering...
Material: describe all materials present...
Dimensions: length * width * height as numbers only WITHOUT units...
Mass: mass as a number only WITHOUT units...
Placement: select one or more possible placements from the list...
```

### 4.2 Why Model Might Not Follow Format

1. **Markdown formatting:** Model may wrap output in ``` code blocks
2. **Bold headers:** Model may use `**Category:**` instead of `Category:`
3. **JSON output:** Model may return JSON despite instruction not to
4. **Conversational style:** Model may add introductory/concluding text
5. **Missing fields:** Model may omit fields it cannot determine
6. **Different capitalization:** `category:` instead of `Category:`

### 4.3 Parser Tolerance

The parser is **moderately tolerant:**

| Variation | Tolerance |
|-----------|-----------|
| Case differences | YES - `re.IGNORECASE` flag used |
| Markdown bullets (`*`, `-`, `#`) | YES - stripped from key and value |
| Bold markers (`**Key**`) | PARTIAL - `**` before key may interfere |
| Extra whitespace | YES - `\s*` handles this |
| Different key order | YES - each key searched independently |
| Missing keys | YES - set to None (unless ALL missing) |
| Code block wrapping | NO - would require preprocessing |
| JSON format | NO - would fail regex matching |

---

## 5. Recommendations

### 5.1 Preprocessing Improvements

Consider adding text preprocessing before parsing:

```python
# Strip markdown code blocks
text = re.sub(r'```[\w]*\n?', '', text)
text = re.sub(r'```', '', text)

# Normalize bold markers around keys
text = re.sub(r'\*\*\s*(\w+)\s*:\s*\*\*', r'\1:', text)
```

### 5.2 Better Error Logging

Current logging only shows that parsing failed. Consider logging:
- First 200 characters of raw output for debugging
- Which specific keys were found/missing
- Regex match details

### 5.3 Retry Logic

Failed parses (raw_output) could trigger:
1. A second inference with a more explicit prompt
2. A different prompt type that might work better
3. Human review queue

---

## Appendix: Complete Code References

### process_asset() - Structured Parsing Logic (lines 63-84)

```python
# Parse structured text if expected
if "json" in prompt_type.lower() or "extract" in prompt_type.lower():
    try:
        result = self.parse_structured_text(result_text)
        if not result:
            print(f"[WARN] No structured data found for {asset_id}. Saving raw text.")
            result = {"raw_output": result_text}
        else:
            # Extract category from directory path and override
            asset_relative_path = os.path.relpath(asset_path, self.config.data.input_dir)
            category_from_dir = asset_relative_path.split(os.sep)[0]

            # Override category with directory name
            result['category'] = category_from_dir

            # Normalize dimensions and mass
            if result.get('dimensions'):
                result['dimensions'] = self._normalize_dimensions(result['dimensions'])
            if result.get('mass'):
                result['mass'] = self._normalize_mass(result['mass'])
    except Exception as e:
        print(f"[WARN] Failed to parse structured text for {asset_id}: {e}. Saving raw text.")
        result = {"raw_output": result_text}
```

### parse_structured_text() - Full Method (lines 107-160)

```python
def parse_structured_text(self, text: str) -> Dict[str, str]:
    """
    Parses structured text using regex to find key-value pairs.
    Robustly handles multi-object outputs by only taking the first occurrence of keys.
    """
    result = {}
    # Define expected keys in order of likelihood
    keys = ["Category", "Description", "Material", "Dimensions", "Mass", "Placement"]

    for key in keys:
        pattern = r"(?:^|\n)[\*#\-]*\s*(" + key + r")\s*:\s*([\s\S]*?)(?=(?:^|\n)[\*#\-]*\s*(?:Category|Description|Material|Dimensions|Mass|Placement)\s*:|$)"

        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Store the value, stripped of whitespace
            value = match.group(2).strip()
            # Clean up value: remove leading "** " if present (common artifact)
            value = re.sub(r'^[\*#\-]*\s*', '', value)
            # Normalize key to lowercase for consistency
            result[key.lower()] = value
        else:
            # If key missing, set to None/null
            result[key.lower()] = None

    # If we found absolutely nothing, return empty dict to trigger raw_output fallback
    # But if we found at least one field (even if others are None), we consider it a success.
    if all(v is None for v in result.values()):
        return {}

    return result
```

---

*End of Analysis Report*
