# DLC Stubborn Assets Re-run Task Report

**Date:** 2026-03-06
**Task:** Re-run annotation for stubborn (previously failed) assets
**Status:** Task Planned - Pending Execution
**Team:** dlc-rerun-team

---

## Executive Summary

This document reports on the planned DLC (Deep Learning Containers) re-run task for stubborn assets that failed initial annotation. The task involves re-processing failed assets using distributed computing on Alibaba Cloud PAI-DLC.

**Key Metrics:**
- **Initial Failed Assets:** 283 (0.56% of 50,091 total assets)
- **Planned Chunks:** 4 parallel workers
- **Estimated Processing Time:** TBD (dependent on actual execution)

---

## 1. Task Overview

### 1.1 Background

During the initial annotation run of 50,091 assets, 283 assets (0.56%) failed to produce valid structured output. These failures were categorized and analyzed in previous investigations (see [2026-03-05_failed_annotations_summary.md](./2026-03-05_failed_annotations_summary.md)).

### 1.2 Objectives

1. Re-annotate all stubborn assets that failed initial processing
2. Validate the effectiveness of parser improvements on multi-object outputs
3. Identify consistently failing assets for further investigation
4. Document DLC distributed processing workflow for future reference

### 1.3 Scope

| Category | Count | Action | Rationale |
|----------|-------|--------|-----------|
| image_only | 272 | Re-annotate | Model failed to generate content |
| multi_object | 8 | Re-annotate | Parser improvements should now handle these |
| truncated | 2 | Re-annotate | Model output was incomplete |
| other | 1 | Re-annotate | Unusual format requiring retry |
| **Total** | **283** | **Full re-run** | **Complete recovery attempt** |

---

## 2. Failure Type Analysis

### 2.1 Image-Only Failures (272 assets, 96.1%)

**Symptom:** Model outputs only `**Image` followed by whitespace/newlines

```
**Image


...(500+ newlines)...
```

**Root Cause:** VLM (Qwen2.5-VL-7B-Instruct) fails to generate meaningful content, possibly due to:
- Image encoding issues
- Model context limitations
- Corrupted input images

**Expected Outcome:** These assets may succeed on retry due to non-deterministic model behavior, or may require manual inspection if they consistently fail.

### 2.2 Multi-Object Outputs (8 assets, 2.8%)

**Symptom:** Model correctly identifies multiple objects but original parser failed

```markdown
**Object 1: Ruler**
* **Category:** Measuring Tool
...

**Object 2: Toothpick**
* **Category:** Tool
...
```

**Root Cause:** Original parser expected single-object format

**Fix Applied:** Enhanced parser with `_extract_first_object()` method now handles these cases by extracting the first object only.

**Expected Outcome:** These should now parse successfully with the improved pipeline.

### 2.3 Truncated Outputs (2 assets, 0.7%)

**Symptom:** Output cut off mid-generation

```
### Object 1: F
 addCriterion
### Object 2:
```

**Root Cause:** Model was interrupted or hit token limit

**Expected Outcome:** Retry may succeed with complete output.

### 2.4 Other Format (1 asset, 0.4%)

**Symptom:** Markdown table format with repetition artifacts

**Root Cause:** Model hallucination/repetition

**Expected Outcome:** Retry may produce valid output.

---

## 3. DLC Execution Plan

### 3.1 Architecture

```
DSW/Local Terminal          DLC Cluster                 Worker Containers
       |                          |                              |
       |  submit_batch.py         |                              |
       |  (4 chunks)              |                              |
       |------------------------->|                              |
       |                          |  launch_job.sh               |
       |                          |  (4 parallel tasks)          |
       |                          |----------------------------->|
       |                          |                              | run_task.sh
       |                          |                              | (chunk mode)
       |                          |                              |
       |                          |                              | auto_asset_annotator.main
       |                          |                              | --num_chunks 4
       |                          |                              | --chunk_index N
```

### 3.2 Chunk Distribution

| Chunk | Index | Assets | Approx. Count |
|-------|-------|--------|---------------|
| 1 | 0 | 1st quarter | ~71 |
| 2 | 1 | 2nd quarter | ~71 |
| 3 | 2 | 3rd quarter | ~71 |
| 4 | 3 | 4th quarter | ~70 |

### 3.3 Command Reference

**Generate stubborn asset list:**
```bash
python scripts/reannotate_failures.py --output_dir ./output \
    --save_list stubborn_assets.txt
```

**Submit DLC batch job:**
```bash
python scripts/dlc/submit_batch.py --total 4 --name stubborn_retry \
    --command_args "--input_dir /data/assets --output_dir /data/results \
        --asset_list_file stubborn_assets.txt --force"
```

**Monitor job status:**
```bash
./dlc get jobs
./dlc logs <job_id>
```

---

## 4. Resource Configuration

### 4.1 Worker Specifications

| Resource | Value | Notes |
|----------|-------|-------|
| GPU | 1 | NVIDIA GPU for VLM inference |
| CPU | 16 | Sufficient for data loading |
| Memory | 32Gi | Model requires ~14GB |
| Shared Memory | 64Gi | For model loading |
| Priority | 7 | Standard priority |

### 4.2 Container Configuration

| Setting | Value |
|---------|-------|
| Image | `dsw-registry-vpc.cn-beijing.cr.aliyuncs.com/pai-training-algorithm/pytorch:2.1.0-cuda12.1-py310` |
| Model Path | `/cpfs/shared/simulation/zhuzihou/models/Qwen2.5-VL-7B-Instruct` |
| Code Root | `/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator` |

---

## 5. Expected Results

### 5.1 Success Criteria

| Metric | Target | Measurement |
|--------|--------|-------------|
| Parse Success Rate | >=90% | Assets with valid JSON (no raw_output) |
| Job Completion | 100% | All 4 chunks finish without errors |
| Output Validity | 100% | All outputs are valid JSON |

### 5.2 Result Categories

After re-run, assets will fall into one of:

1. **Success:** Valid structured JSON with all fields
2. **Still Failed:** Contains `raw_output` field (requires further investigation)
3. **Error:** Job-level failure (requires resubmission)

---

## 6. Post-Execution Actions

### 6.1 Verification Steps

```bash
# 1. Check for remaining failures
python scripts/find_failed_assets.py --output_dir ./output \
    --save_list still_failed.txt

# 2. Compare before/after counts
wc -l stubborn_assets.txt
wc -l still_failed.txt

# 3. Calculate success rate
# Success Rate = (283 - len(still_failed)) / 283 * 100%
```

### 6.2 Documentation Updates

- Update this report with actual execution results
- Document any new failure patterns discovered
- Update CLAUDE.md with refined DLC commands if needed

---

## 7. Known Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Consistent model failures | Medium | High | Document assets for manual review |
| DLC job failures | Low | Medium | Retry failed chunks individually |
| Resource contention | Low | Low | Off-peak scheduling |
| Parser edge cases | Low | Medium | Capture samples for analysis |

---

## 8. Related Documents

| Document | Description |
|----------|-------------|
| [2026-03-05_failed_annotations_summary.md](./2026-03-05_failed_annotations_summary.md) | Initial failure analysis |
| [2026-03-05_dlc_migration.md](./2026-03-05_dlc_migration.md) | DLC infrastructure setup |
| [docs/dlc/README.md](../dlc/README.md) | DLC usage guide |
| [CLAUDE.md](../../CLAUDE.md) | Project command reference |

---

## 9. Appendix: File Locations

```
/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/
├── stubborn_assets.txt              # List of assets to re-run
├── scripts/dlc/submit_batch.py      # Batch submission script
├── scripts/dlc/launch_job.sh        # DLC job launcher
├── scripts/dlc/run_task.sh          # Container task executor
├── scripts/reannotate_failures.py   # Failure analysis tool
├── scripts/find_failed_assets.py    # Post-run verification
└── docs/changes/2026-03-06_stubborn_assets_rerun.md  # This document
```

---

## 10. Task Status Log

| Date | Event | Status |
|------|-------|--------|
| 2026-03-05 | Failure analysis completed | Done |
| 2026-03-05 | Parser improvements implemented | Done |
| 2026-03-05 | DLC infrastructure tested | Done |
| 2026-03-06 | Re-run task planned | Done |
| 2026-03-06 | DLC jobs submitted (4 batches) | Done |
| 2026-03-06 | Batches 1-3 completed | Done |
| 2026-03-06 | Batch 4 failed (infrastructure) | Done |
| 2026-03-06 | Batch 4 resubmitted | Pending |
| TBD | Batch 4 completed | Pending |
| TBD | Final results verified | Pending |

---

## 11. Execution Results

### 11.1 Batch Execution Summary

| Batch | Assets | Success | Failed | Success Rate | DLC Job Status |
|-------|--------|---------|--------|--------------|----------------|
| Batch 1 | 71 | 66 | 5 | 93.0% | Succeeded |
| Batch 2 | 71 | 70 | 1 | 98.6% | Succeeded |
| Batch 3 | 71 | 65 | 6 | 91.5% | Succeeded |
| Batch 4 | 70 | 0 | 70 | 0.0% | Failed (exit 128) |
| **Total** | **283** | **201** | **82** | **71.0%** | **75%** |

### 11.2 Success Rate Analysis

**Initial State:**
- Total stubborn assets: 283
- All had `raw_output` field (100% failure rate)

**After Re-run (Batches 1-3):**
- Successfully parsed: 201 assets
- Still failing: 12 assets (batches 1-3) + 70 assets (batch 4) = 82 total
- Effective success rate: 201/213 = **94.4%** (for completed batches)

**Failure Types After Re-run:**
- Image-only failures (persisted): ~12 assets
- Infrastructure failure (batch 4): 70 assets

### 11.3 Batch 4 Failure Details

**Job:** stubborn_rerun_3_4 (dlc1jkbc3tzb6q62)
**Exit Code:** 128
**Cause:** Container runtime error - "services already exists" naming conflict
**Status:** Requires resubmission

---

*See 2026-03-06_stubborn_assets_final_report.md for complete final results after batch 4 retry.*
