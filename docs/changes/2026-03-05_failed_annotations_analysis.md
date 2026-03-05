# Failed Annotations Analysis Report

**Date:** 2026-03-05
**Total Failed Files:** 283
**Analysis Method:** Automated pattern detection on raw_output field

---

## 1. Summary Statistics

| Metric | Value |
|--------|-------|
| Total Failed Annotations | 283 |
| Categories Affected | 20 |
| Most Affected Category | window (71 files) |
| Average Raw Output Length | 583.8 chars |
| Median Raw Output Length | 502 chars |
| Min Length | 44 chars |
| Max Length | 12219 chars |

---

## 2. Distribution by Category

| Category | Failed Count | Percentage |
|----------|--------------|------------|
| window | 71 | 25.1% |
| door | 53 | 18.7% |
| book | 47 | 16.6% |
| picture | 38 | 13.4% |
| other | 35 | 12.4% |
| cabinet | 11 | 3.9% |
| mirror | 4 | 1.4% |
| decoration | 4 | 1.4% |
| clock | 3 | 1.1% |
| wall | 3 | 1.1% |
| curtain | 3 | 1.1% |
| bottle | 2 | 0.7% |
| desk | 2 | 0.7% |
| oven | 1 | 0.4% |
| washing_machine | 1 | 0.4% |
| towel | 1 | 0.4% |
| bed | 1 | 0.4% |
| pillow | 1 | 0.4% |
| shelf | 1 | 0.4% |
| dish_washer | 1 | 0.4% |

---

## 3. Raw Output Pattern Analysis

### 3.1 Pattern Distribution

| Pattern Type | Count | Percentage | Description |
|--------------|-------|------------|-------------|
| image_tag_only | 272 | 96.1% | Output is just "**Image" followed by whitespace |
| multi_object_format | 8 | 2.8% | Contains multiple objects (Object 1, Object 2) |
| other | 1 | 0.4% | Other unstructured formats |
| possibly_truncated | 1 | 0.4% | Ends with ellipsis or colon |
| table_format | 1 | 0.4% | Uses markdown table format |

### 3.2 Key Findings

1. **Image-Only Outputs (96.1%)**: The vast majority of failures are outputs that contain only
   `**Image` followed by whitespace/newlines. This suggests the model is not generating actual
   content - possibly due to:
   - Image loading/processing issues
   - Model failing to "see" or interpret the images
   - Prompt misunderstanding where the model just echoes back the image marker

2. **Multi-Object Outputs (2.8%)**: Some outputs contain valid structured data but for multiple
   objects (Object 1, Object 2). The current parser only extracts the first occurrence of keys,
   but these outputs may contain useful information that could be parsed differently.

3. **Format Variations**: A small number use markdown tables or JSON format instead of the
   expected plain text format with headers.

---

## 4. Sample Raw Output Content by Pattern Type

### multi_object_format

**File:** `output/other/e8f638fd49cc32ef146bbde38dbb3ef7_annotation.json`

**Content:**
```
**Object 1: Ruler**

* **Category:** Measuring Tool
* **Description:** The ruler has a straight, elongated shape with a uniform width throughout its length. It is light yellow in color, with black markings indicating for measurements. The surface appears smooth and slightly glossy, suggesting a plastic finish. The ruler measures approximately 0.25 meters in length, 0.01 meters in width, and 0.005 meters in height. It is currently in a closed state, designed for measuring lengths. The distinctive feature is the precise measurement markings along its entire length.
* **Material:** The ruler is made of plastic, covering the entire body.
* **Dimensions:** 0.25 * 0.01 * 0.005 meters
* **Mass:** 0.05 kg
* **Placement:** OnTable

**Object 2: Toothpick**

* **Category:** Food Tool
* **Description:** The toothpick is a thin, elongated stick with a pointed tip at one end and a flat base at the other. It is light yellow in color, with a smooth surface and a matte finish. The toothpick measures ap
```

---

### image_only

**File:** `output/other/11bd153a8a041318959a8cb4be66a1bf_annotation.json`

**Content:**
```
**Image




































































































































































































































































































```

---

### very_short

**File:** `output/other/4e53b07207a412802b79659597eaecc2_annotation.json`

**Content:**
```
### Object 1: F

 addCriterion
### Object 2:
```

---

### table_format

**File:** `output/picture/d30922687b71461cccad92f4ee5c320e_annotation.json`

**Content:**
```
| Category | object |
| Description | The object appears to be a slender, elongated rod with a uniform cylindrical shape. It has a matte black surface with no visible texture or finish. The proportions suggest a tall and narrow form, possibly indicating a pen, pencil, or similar writing implement. The current state seems to be closed, as there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there there
```

---

## 5. Initial Observations on Failure Causes

### 5.1 Primary Failure Mode: Image-Only Outputs

The dominant failure pattern (96.1% of cases) is outputs containing only `**Image` with whitespace.
This indicates a fundamental issue with either:

- **Image Input Handling**: The model may not be receiving or processing the images correctly
- **Model Behavior**: The Qwen2.5-VL model may be outputting image markers when it cannot
  interpret the visual content
- **Prompt Effectiveness**: The current prompt (`extract_object_attributes_prompt`) may not
  be sufficiently guiding the model to produce the expected output format

### 5.2 Secondary Issues

1. **Multi-Object Detection**: Some images contain multiple objects, and the model correctly
   identifies them but outputs in a multi-object format that the parser doesn't handle.

2. **Format Inconsistency**: The model occasionally outputs markdown tables or JSON instead
   of the requested plain text format.

3. **Truncation**: Some outputs appear truncated (ending with `...` or `:`), suggesting
   `max_new_tokens` (currently 2048) may be insufficient for some cases.

### 5.3 Category-Specific Observations

- **window (71 failures)**: Highest failure rate - may indicate difficulty with transparent/reflective surfaces
- **door (53 failures)**: Second highest - large flat surfaces may be challenging
- **book (47 failures)**: Third highest - possibly due to uniform appearance
- **picture (38 failures)**: Art/decor items may have high visual variability
- **other (35 failures)**: Catch-all category with mixed results

---

## 6. Recommendations for Further Investigation

1. **Verify Image Loading**: Check that images are being correctly passed to the model
2. **Review Model Temperature**: Current setting (0.1) is low; consider if slightly higher would help
3. **Prompt Engineering**: Consider strengthening the prompt to explicitly reject image-only outputs
4. **Multi-Object Handling**: Enhance parser to handle multi-object outputs or add pre-processing
   to detect multiple objects
5. **Retry Logic**: Implement automatic retry with different prompt variations for image-only outputs
6. **Category-Specific Prompts**: Consider custom prompts for problematic categories (window, door)

---

*Report generated automatically by data-analyst agent*
