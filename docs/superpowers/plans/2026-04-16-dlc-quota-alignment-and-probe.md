# DLC Quota Alignment And Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Align the repository’s DLC resource templates and quota routing with the newer less-gpu / more-gpu policy, add stronger fail-fast validation, and introduce a standard probe submission workflow.

**Architecture:** Keep the existing semantic profile UX (`api_light`, `local_hf_default`, `local_hf_heavy`) but resolve each profile through canonical `1/2/4/8 GPU` templates and the new quota mapping. Strengthen `launch_job.sh`, wrapper scripts, and `python_runtime.sh` with explicit validation, then add a `submit_probe.sh` wrapper plus updated operator docs and a probe-ready runbook.

**Tech Stack:** Bash, Python 3.10+, `unittest`, subprocess-based DLC script tests, current DLC wrapper chain, `apply_patch` for edits.

---

## File Structure Map

### Create

- `scripts/dlc/submit_probe.sh`
  - Canonical tiny-scope probe wrapper for safe real submissions.
- `docs/changes/2026-04-16_dlc_quota_alignment_and_probe.md`
  - Change log for quota migration, validation additions, and probe workflow.

### Modify

- `scripts/dlc/launch_job.sh`
  - Canonical GPU-count templates, quota routing, and chunk validation.
- `scripts/dlc/python_runtime.sh`
  - Stronger backend-specific preflight.
- `scripts/dlc/submit_retry_failed.sh`
  - Early failed-list existence validation.
- `scripts/dlc/submit_asset_list.sh`
  - Early asset-list existence validation.
- `docs/dlc/README.md`
- `docs/dlc/TESTING.md`
- `README.md`
- `CLAUDE.md`
- `tests/test_dlc_scripts.py`

## Task 1: Add Red Tests For Quota Mapping And Validation

**Files:**
- Modify: `tests/test_dlc_scripts.py`

- [ ] **Step 1: Add a failing launch-template test for 1 GPU quota routing**

Extend `tests/test_dlc_scripts.py` with:

```python
    def test_launch_job_1gpu_uses_less_gpu_quota_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_dlc = Path(tmp) / "dlc"
            fake_dlc.write_text("#!/bin/bash\nprintf '%s\n' \"$*\"\n")
            fake_dlc.chmod(0o755)
            env = os.environ.copy()
            env.update({
                "DLC_BIN": str(fake_dlc),
                "DLC_CODE_ROOT": str(REPO_ROOT),
                "DLC_PROFILE": "api_light",
            })
            result = subprocess.run(
                ["bash", str(SCRIPTS_DIR / "launch_job.sh"), "probe", "0", "1"],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("Resource ID:    quota1r947pmazvk", result.stdout)
            self.assertIn("Worker CPU:     14", result.stdout)
            self.assertIn("Worker Memory:  100Gi", result.stdout)
```

- [ ] **Step 2: Add a failing launch-template test for 8 GPU quota routing**

Add:

```python
    def test_launch_job_8gpu_uses_more_gpu_quota_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_dlc = Path(tmp) / "dlc"
            fake_dlc.write_text("#!/bin/bash\nprintf '%s\n' \"$*\"\n")
            fake_dlc.chmod(0o755)
            env = os.environ.copy()
            env.update({
                "DLC_BIN": str(fake_dlc),
                "DLC_CODE_ROOT": str(REPO_ROOT),
                "DLC_WORKER_GPU": "8",
                "DLC_PROFILE": "local_hf_heavy",
            })
            result = subprocess.run(
                ["bash", str(SCRIPTS_DIR / "launch_job.sh"), "probe", "0", "1"],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("Resource ID:    quotaksvqq2oh2pg", result.stdout)
            self.assertIn("Worker CPU:     128", result.stdout)
            self.assertIn("Worker Memory:  960Gi", result.stdout)
```

- [ ] **Step 3: Add failing validation tests for bad chunk arguments**

Add:

```python
    def test_launch_job_rejects_negative_chunk_id(self):
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "launch_job.sh"), "probe", "-1", "4"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        self.assertNotEqual(result.returncode, 0)

    def test_launch_job_rejects_chunk_id_out_of_range(self):
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "launch_job.sh"), "probe", "4", "4"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        self.assertNotEqual(result.returncode, 0)
```

- [ ] **Step 4: Add failing wrapper-validation tests for missing asset lists**

Add:

```python
    def test_submit_asset_list_requires_existing_file(self):
        result = subprocess.run(
            [
                "bash",
                str(SCRIPTS_DIR / "submit_asset_list.sh"),
                "--dry-run",
                "--asset_list_file",
                "/tmp/does-not-exist.txt",
            ],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        self.assertNotEqual(result.returncode, 0)
```

- [ ] **Step 5: Add failing runtime-preflight tests for API mode**

Add:

```python
    def test_python_runtime_rejects_missing_api_requirements(self):
        with tempfile.TemporaryDirectory() as tmp:
            code_root = Path(tmp)
            venv_python = code_root / ".venv_dlc" / "bin" / "python"
            venv_python.parent.mkdir(parents=True)
            venv_python.write_text("#!/bin/bash\nif [ \"$1\" = \"-\" ]; then exit 0; fi\nexit 0\n")
            venv_python.chmod(0o755)

            env = os.environ.copy()
            env["DLC_CODE_ROOT"] = str(REPO_ROOT)
            env["MODEL_BACKEND"] = "openai_compatible"
            env.pop("API_BASE_URL", None)
            env.pop("API_KEY_ENV", None)

            result = subprocess.run(
                ["bash", str(SCRIPTS_DIR / "python_runtime.sh"), "-m", "auto_asset_annotator.main"],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
            )
            self.assertNotEqual(result.returncode, 0)
```

- [ ] **Step 6: Run the DLC test suite to capture the red baseline**

Run:

```bash
PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_dlc_scripts
```

Expected: FAIL on new quota/validation/probe expectations before implementation.

## Task 2: Implement Quota Mapping, Template Alignment, And Validation

**Files:**
- Modify: `scripts/dlc/launch_job.sh`
- Modify: `tests/test_dlc_scripts.py`

- [ ] **Step 1: Add chunk-value validation to `launch_job.sh`**

Implement shell validation for:

```bash
CHUNK_ID >= 0
CHUNK_TOTAL >= 1
CHUNK_ID < CHUNK_TOTAL
```

Reject invalid values before any submission logic runs.

- [ ] **Step 2: Introduce canonical GPU-count templates**

Update `launch_job.sh` so it resolves canonical templates by effective GPU count:

```bash
case "$GPU_COUNT" in
  1)
    TPL_GPU=1; TPL_CPU=14; TPL_MEM=100Gi; TPL_SHMEM=100Gi; TPL_RES=quota1r947pmazvk ;;
  2)
    TPL_GPU=2; TPL_CPU=28; TPL_MEM=200Gi; TPL_SHMEM=200Gi; TPL_RES=quota1r947pmazvk ;;
  4)
    TPL_GPU=4; TPL_CPU=56; TPL_MEM=400Gi; TPL_SHMEM=400Gi; TPL_RES=quota1r947pmazvk ;;
  8)
    TPL_GPU=8; TPL_CPU=128; TPL_MEM=960Gi; TPL_SHMEM=960Gi; TPL_RES=quotaksvqq2oh2pg ;;
  *)
    echo "ERROR: Unsupported GPU count: $GPU_COUNT" >&2; exit 1 ;;
esac
```

- [ ] **Step 3: Keep semantic profiles but map them to GPU counts**

In `launch_job.sh`, resolve semantic profiles to GPU counts like this:

```bash
case "$DLC_PROFILE" in
  api_light) PROFILE_GPU_COUNT=1 ;;
  local_hf_default) PROFILE_GPU_COUNT=1 ;;
  local_hf_heavy) PROFILE_GPU_COUNT=4 ;;
  *) echo "ERROR: Unsupported DLC_PROFILE: $DLC_PROFILE" >&2; exit 1 ;;
esac

GPU_COUNT=${DLC_GPU_COUNT:-$PROFILE_GPU_COUNT}
```

Then use the canonical GPU-count template table from Step 2.

- [ ] **Step 4: Preserve override semantics after template resolution**

After template selection, keep this pattern:

```bash
WORKER_GPU=${DLC_WORKER_GPU:-$TPL_GPU}
WORKER_CPU=${DLC_WORKER_CPU:-$TPL_CPU}
WORKER_MEMORY=${DLC_WORKER_MEMORY:-$TPL_MEM}
WORKER_SHARED_MEMORY=${DLC_WORKER_SHARED_MEMORY:-$TPL_SHMEM}
RESOURCE_ID=${DLC_RESOURCE_ID:-$TPL_RES}
```

This keeps manual overrides possible, but defaults now align with the new quota model.

- [ ] **Step 5: Re-run the DLC script tests**

Run:

```bash
PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_dlc_scripts
```

Expected: quota-routing and chunk-validation tests now pass. Runtime/wrapper-specific tests may still be pending Task 3.

## Task 3: Strengthen Runtime And Wrapper Fail-Fast Behavior

**Files:**
- Modify: `scripts/dlc/python_runtime.sh`
- Modify: `scripts/dlc/submit_retry_failed.sh`
- Modify: `scripts/dlc/submit_asset_list.sh`
- Modify: `tests/test_dlc_scripts.py`

- [ ] **Step 1: Add backend-specific runtime preflight**

In `python_runtime.sh`, before invoking Python:

- if `MODEL_BACKEND=openai_compatible`:
  - require `API_BASE_URL`
  - require `API_KEY_ENV`
  - require the environment variable named by `API_KEY_ENV` to be set and non-empty

- if `MODEL_PATH` looks like a local path (contains `/` or begins with `.`) and `MODEL_BACKEND` is unset or `local_hf`:
  - verify the path exists

Fail with clear error messages.

- [ ] **Step 2: Add wrapper-level file existence checks**

Implement fail-fast checks:

```bash
submit_retry_failed.sh -> ensure archive/temp_lists/failed_assets.txt exists
submit_asset_list.sh -> ensure provided asset-list path exists and is readable
```

If missing, exit nonzero before calling `submit_batch.py`.

- [ ] **Step 3: Add a regression test for wrapper file validation**

Extend `tests/test_dlc_scripts.py` with a success-path asset-list wrapper test using a temporary file:

```python
    def test_submit_asset_list_dry_run_accepts_existing_file(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("chair/abc123\n")
            asset_list = f.name
        self.addCleanup(lambda: os.path.exists(asset_list) and os.remove(asset_list))
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "submit_asset_list.sh"), "--dry-run", "--asset_list_file", asset_list],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0)
```

- [ ] **Step 4: Add a regression test for runtime API preflight**

Adjust the Task 1 red test so it becomes green when the API requirements are enforced correctly.

- [ ] **Step 5: Re-run the full DLC script suite**

Run:

```bash
PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_dlc_scripts
```

Expected: PASS.

## Task 4: Add Probe Wrapper And Update Operator Docs

**Files:**
- Create: `scripts/dlc/submit_probe.sh`
- Modify: `docs/dlc/README.md`
- Modify: `docs/dlc/TESTING.md`
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Create: `docs/changes/2026-04-16_dlc_quota_alignment_and_probe.md`

- [ ] **Step 1: Create `submit_probe.sh`**

Implement a small wrapper with this shape:

```bash
#!/bin/bash
set -euo pipefail

CODE_ROOT=${DLC_CODE_ROOT:-"/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator"}
TOTAL=${TOTAL:-1}
NAME=${NAME:-annotate_probe}
PROFILE=${DLC_PROFILE:-api_light}

bash "$CODE_ROOT/scripts/dlc/submit_annotate.sh" \
  --dry-run "$@"
```

Then adapt it so:

- it supports real submit when `--dry-run` is not passed
- it defaults to `TOTAL=1`
- it prints probe-oriented guidance

- [ ] **Step 2: Add one exact API probe recipe and one exact local probe recipe to docs**

Update `docs/dlc/TESTING.md` with two explicit commands:

- API probe:

```bash
DLC_PROFILE=api_light TOTAL=1 NAME=api_probe \
API_BASE_URL=http://... API_KEY_ENV=NEWAPI_API_KEY MODEL_BACKEND=openai_compatible MODEL_PATH=gemini-2.5-flash-image \
bash scripts/dlc/submit_probe.sh --dry-run
```

- Local probe:

```bash
DLC_PROFILE=local_hf_default TOTAL=1 NAME=local_probe \
MODEL_BACKEND=local_hf MODEL_PATH=/path/to/local/model \
bash scripts/dlc/submit_probe.sh --dry-run
```

The docs must state clearly that the real job path is the same command without `--dry-run`.

- [ ] **Step 3: Update `docs/dlc/README.md` for the new quota model**

Document:

- `1/2/4 GPU -> quota1r947pmazvk`
- `8 GPU -> quotaksvqq2oh2pg`
- semantic profiles still exist, but are backed by canonical GPU-count templates

- [ ] **Step 4: Add the probe-and-quota change log**

Create `docs/changes/2026-04-16_dlc_quota_alignment_and_probe.md` with sections:

```markdown
## Research / Investigation
## Design Decisions
## Code Changes
## Testing
## Open Issues
```

- [ ] **Step 5: Run lightweight wrapper/doc verification**

Run:

```bash
PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_dlc_scripts
bash scripts/dlc/submit_probe.sh --dry-run
```

Expected: PASS, and the probe wrapper prints the expected canonical submission path.

## Task 5: Final Verification And Handoff

**Files:**
- Verify: `scripts/dlc/launch_job.sh`
- Verify: `scripts/dlc/python_runtime.sh`
- Verify: wrappers
- Verify: `docs/dlc/README.md`
- Verify: `docs/dlc/TESTING.md`

- [ ] **Step 1: Run the full DLC test suite**

Run:

```bash
PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_dlc_scripts
```

Expected: PASS.

- [ ] **Step 2: Run the canonical dry-run wrappers**

Run:

```bash
bash scripts/dlc/submit_annotate.sh --dry-run
bash scripts/dlc/submit_retry_failed.sh --dry-run
bash scripts/dlc/submit_retry_incomplete.sh --dry-run
bash scripts/dlc/submit_asset_list.sh --dry-run --asset_list_file archive/temp_lists/failed_assets.txt
bash scripts/dlc/submit_probe.sh --dry-run
```

Expected: PASS.

- [ ] **Step 3: Run one fake-launcher probe for each quota class**

Run:

```bash
TMP=$(mktemp -d)
FAKE_DLC="$TMP/dlc"
printf '%s\n' '#!/bin/bash' 'printf "%s\n" "$*"' > "$FAKE_DLC"
chmod +x "$FAKE_DLC"

DLC_BIN="$FAKE_DLC" DLC_PROFILE=api_light bash scripts/dlc/launch_job.sh probe 0 1
DLC_BIN="$FAKE_DLC" DLC_WORKER_GPU=8 DLC_PROFILE=local_hf_heavy bash scripts/dlc/launch_job.sh probe 0 1
```

Expected:

- 1-GPU path resolves `quota1r947pmazvk`
- 8-GPU path resolves `quotaksvqq2oh2pg`

- [ ] **Step 4: Review the final diff without committing**

Run:

```bash
git diff --stat
git diff
```

Expected: coherent second-round DLC alignment and probe additions. Do not create a commit unless the user explicitly asks.

## Self-Review Checklist

- [ ] Spec coverage check: Task 1 covers new red tests; Task 2 covers quota/template alignment; Task 3 covers fail-fast runtime/wrapper validation; Task 4 covers probe workflow and docs; Task 5 covers final verification.
- [ ] Draft-marker scan: search this plan for banned drafting markers and remove any accidental match before execution.
- [ ] Consistency check: keep semantic profiles, align them through canonical GPU-count templates, and route 8-GPU jobs to `quotaksvqq2oh2pg`.

## Notes For The Implementer

- Use `apply_patch` for manual edits.
- Do not remove semantic `DLC_PROFILE` names; align them with the new quota model instead.
- Do not submit a real probe job unless explicitly requested by the user.
- Do not create any git commit unless the user explicitly asks.
