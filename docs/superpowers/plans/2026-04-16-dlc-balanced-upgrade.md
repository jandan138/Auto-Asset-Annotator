# DLC Balanced Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the repository’s DLC workflow into a reliable, annotation-focused submission and operations system with correct chunk handling, a lightweight runtime wrapper, small resource profiles, stable submit wrappers, and operator-grade documentation.

**Architecture:** Keep the existing `submit_batch.py -> launch_job.sh -> run_task.sh -> python -m auto_asset_annotator.main` chain, but harden each layer. Move environment setup and preflight into a new `python_runtime.sh`, make `launch_job.sh` the authoritative place for resource-profile resolution and final job command construction, keep `run_task.sh` as a thin annotation-first dispatcher, and back the shell changes with a Python test harness that exercises script behavior through subprocess calls.

**Tech Stack:** Bash, Python 3.10+, `unittest`, subprocess-based script tests, existing DLC CLI integration, `apply_patch` for edits.

---

## File Structure Map

### Create

- `scripts/dlc/python_runtime.sh`
  - Lightweight runtime wrapper for venv discovery, preflight, and Python invocation.
- `scripts/dlc/submit_annotate.sh`
  - Canonical wrapper for full annotation batch submission.
- `scripts/dlc/submit_retry_failed.sh`
  - Canonical wrapper for rerunning `archive/temp_lists/failed_assets.txt`.
- `scripts/dlc/submit_retry_incomplete.sh`
  - Canonical wrapper for `--retry_incomplete` submissions.
- `scripts/dlc/submit_asset_list.sh`
  - Canonical wrapper for explicit asset-list jobs.
- `tests/test_dlc_scripts.py`
  - Subprocess-based test harness for DLC shell scripts.
- `docs/changes/2026-04-16_dlc_balanced_upgrade.md`
  - Change log documenting research, design, code changes, verification, and open issues.

### Modify

- `scripts/dlc/submit_batch.py`
- `scripts/dlc/launch_job.sh`
- `scripts/dlc/run_task.sh`
- `docs/dlc/README.md`
- `docs/dlc/TESTING.md`
- `README.md`
- `CLAUDE.md`
- `docs/usage/cli_reference.md`

## Task 1: Lock The DLC Argument Contract With Tests

**Files:**
- Create: `tests/test_dlc_scripts.py`
- Read: `scripts/dlc/submit_batch.py`
- Read: `scripts/dlc/launch_job.sh`
- Read: `scripts/dlc/run_task.sh`

- [ ] **Step 1: Write a failing subprocess-based DLC script test file**

Create `tests/test_dlc_scripts.py` with this initial structure:

```python
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts" / "dlc"


class TestDLCScripts(unittest.TestCase):
    def test_run_task_without_args_exits_nonzero(self):
        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "run_task.sh")],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        self.assertNotEqual(result.returncode, 0)

    def test_submit_batch_supports_dry_run(self):
        result = subprocess.run(
            [
                ".venv_dlc/bin/python",
                "scripts/dlc/submit_batch.py",
                "--total",
                "2",
                "--name",
                "dryrun_test",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("dryrun_test", result.stdout)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Add a failing launcher contract test**

Extend `tests/test_dlc_scripts.py` with a fake DLC binary test that verifies chunk args are not duplicated:

```python
    def test_launch_job_default_command_does_not_duplicate_chunk_args(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_dlc = Path(tmp) / "dlc"
            fake_dlc.write_text("#!/bin/bash\nprintf '%s\n' \"$*\"\n")
            fake_dlc.chmod(0o755)

            env = os.environ.copy()
            env["DLC_BIN"] = str(fake_dlc)
            env["DLC_CODE_ROOT"] = str(REPO_ROOT)

            result = subprocess.run(
                [
                    "bash",
                    str(SCRIPTS_DIR / "launch_job.sh"),
                    "annotate_assets",
                    "0",
                    "4",
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("run_task.sh 0 4", result.stdout)
            self.assertNotIn("run_task.sh 0 4 0 4", result.stdout)
```

- [ ] **Step 3: Run the new tests to verify they fail before implementation**

Run:

```bash
PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_dlc_scripts
```

Expected:

- FAIL because `run_task.sh` currently exits `0` on no args
- FAIL because `submit_batch.py` has no `--dry-run`
- FAIL because `launch_job.sh` currently duplicates chunk args

- [ ] **Step 4: Add one more failing test for `run_task.sh` batch forwarding**

Extend `tests/test_dlc_scripts.py` with a fake runtime wrapper test:

```python
    def test_run_task_batch_mode_forwards_main_flags_after_chunk_args(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_runtime = Path(tmp) / "python_runtime.sh"
            fake_runtime.write_text(
                "#!/bin/bash\nprintf '%s\n' \"$*\"\n"
            )
            fake_runtime.chmod(0o755)

            env = os.environ.copy()
            env["DLC_PYTHON_RUNTIME"] = str(fake_runtime)
            env["DLC_CODE_ROOT"] = str(REPO_ROOT)

            result = subprocess.run(
                [
                    "bash",
                    str(SCRIPTS_DIR / "run_task.sh"),
                    "0",
                    "4",
                    "--input_dir",
                    "/data/assets",
                    "--output_dir",
                    "/data/output",
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("python -m auto_asset_annotator.main --num_chunks 4 --chunk_index 0 --input_dir /data/assets --output_dir /data/output", result.stdout)
```

- [ ] **Step 5: Re-run tests to capture the full red baseline**

Run:

```bash
PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_dlc_scripts
```

Expected: FAIL, confirming the current shell contract is not yet correct.

## Task 2: Add Runtime Wrapper And Slim `run_task.sh`

**Files:**
- Create: `scripts/dlc/python_runtime.sh`
- Modify: `scripts/dlc/run_task.sh`
- Modify: `tests/test_dlc_scripts.py`

- [ ] **Step 1: Implement the runtime wrapper with explicit preflight**

Create `scripts/dlc/python_runtime.sh` with this structure:

```bash
#!/bin/bash
set -euo pipefail

CODE_ROOT=${DLC_CODE_ROOT:-"/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator"}

if [ -d "$CODE_ROOT/.venv_dlc" ]; then
    VENV_PATH="$CODE_ROOT/.venv_dlc"
elif [ -d "$CODE_ROOT/.venv" ]; then
    VENV_PATH="$CODE_ROOT/.venv"
else
    echo "ERROR: No virtual environment found at $CODE_ROOT/.venv_dlc or $CODE_ROOT/.venv" >&2
    exit 1
fi

PYTHON_BIN="$VENV_PATH/bin/python"
if [ ! -f "$PYTHON_BIN" ]; then
    echo "ERROR: Python not found at $PYTHON_BIN" >&2
    exit 1
fi

export PYTHONUNBUFFERED=1
export PYTHONPATH="$CODE_ROOT:${PYTHONPATH:-}"
cd "$CODE_ROOT"

"$PYTHON_BIN" - <<'PY'
import auto_asset_annotator
print("[INFO] auto_asset_annotator import OK")
PY

"$PYTHON_BIN" "$@"
```

- [ ] **Step 2: Run a wrapper-only smoke check**

Run:

```bash
bash scripts/dlc/python_runtime.sh -c "print('ok')"
```

Expected: FAIL initially, because the wrapper currently treats the first argument as a file path rather than Python `-c` input. This confirms you need the next step.

- [ ] **Step 3: Teach the wrapper to pass through Python flags safely**

Adjust `python_runtime.sh` so it supports:

- `-c ...`
- `-m module ...`
- script path execution

For example:

```bash
"$PYTHON_BIN" "$@"
```

must remain the final invocation, but the preflight should not consume or reorder arguments.

- [ ] **Step 4: Refactor `run_task.sh` to use the wrapper and fail nonzero on bad invocation**

Change `scripts/dlc/run_task.sh` so it:

- finds `python_runtime.sh` through:

```bash
PYTHON_RUNTIME=${DLC_PYTHON_RUNTIME:-"$CODE_ROOT/scripts/dlc/python_runtime.sh"}
```

- exits `1` on no arguments, not `0`
- removes direct venv/PYTHONPATH setup from `run_task.sh`
- keeps the supported modes limited to:
  - `annotate`
  - `classify`
  - `extract`
  - `custom`
  - default chunk mode

- [ ] **Step 5: Make chunk mode call the wrapper with a canonical main command**

The batch path in `run_task.sh` must resolve to exactly this shape:

```bash
bash "$PYTHON_RUNTIME" -m auto_asset_annotator.main --num_chunks "$CHUNK_TOTAL" --chunk_index "$CHUNK_ID" "$@"
```

and nothing else before the extra `main.py` flags.

- [ ] **Step 6: Wire explicit env-to-CLI forwarding only where supported**

If these environment variables are set, append them as explicit CLI flags in `run_task.sh` batch path:

```bash
MODEL_PATH -> --model_path
MODEL_BACKEND -> --model_backend
API_BASE_URL -> --api_base_url
API_KEY_ENV -> --api_key_env
```

Do not export dead environment variables that `main.py` never reads.

- [ ] **Step 7: Re-run the DLC script tests to verify the batch contract now passes**

Run:

```bash
PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_dlc_scripts
```

Expected: the no-arg exit and batch-forwarding tests now pass, while dry-run/resource-profile tests are still pending Task 3.

## Task 3: Upgrade `launch_job.sh` And `submit_batch.py`

**Files:**
- Modify: `scripts/dlc/launch_job.sh`
- Modify: `scripts/dlc/submit_batch.py`
- Modify: `tests/test_dlc_scripts.py`

- [ ] **Step 1: Add failing dry-run/resource-profile tests**

Extend `tests/test_dlc_scripts.py` with these tests:

```python
    def test_submit_batch_dry_run_does_not_execute_launcher(self):
        result = subprocess.run(
            [
                ".venv_dlc/bin/python",
                "scripts/dlc/submit_batch.py",
                "--total",
                "2",
                "--name",
                "dryrun_test",
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("DRY RUN", result.stdout)

    def test_launch_job_resolves_api_light_profile(self):
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
                ["bash", str(SCRIPTS_DIR / "launch_job.sh"), "annotate", "0", "4"],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
            )
            self.assertEqual(result.returncode, 0)
            self.assertIn("api_light", result.stdout)
            self.assertIn("Resolved config", result.stdout)
```

- [ ] **Step 2: Run the tests to verify they fail before implementation**

Run:

```bash
PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_dlc_scripts
```

Expected: FAIL because `--dry-run` and profile handling do not exist yet.

- [ ] **Step 3: Add `--dry-run` to `submit_batch.py`**

Implement these changes:

- new CLI flag:

```python
parser.add_argument("--dry-run", action="store_true", help="Print the resolved launcher commands without submitting jobs")
```

- in `submit_jobs(...)`, if `dry_run` is true:
  - print the command for each chunk
  - do not call `subprocess.run(...)`
  - print a summary and return success

- [ ] **Step 4: Correct the meaning of `command_args`**

Update `submit_batch.py` comments/help text so `command_args` is described as extra `main.py` CLI flags for the batch path, not a run-mode override.

- [ ] **Step 5: Refactor `launch_job.sh` to one clear argument contract**

Make these exact shell rules true:

```bash
DATA_SOURCES=${4:-"...defaults..."}
COMMAND_ARGS=${5:-""}
```

and:

```bash
--command="bash $CODE_ROOT/scripts/dlc/run_task.sh $CHUNK_ID $CHUNK_TOTAL ${COMMAND_ARGS}"
```

must no longer duplicate the chunk pair.

- [ ] **Step 6: Add repository-specific resource profiles**

In `launch_job.sh`, add one profile selector, e.g.:

```bash
DLC_PROFILE=${DLC_PROFILE:-local_hf_default}
case "$DLC_PROFILE" in
  api_light)
    TPL_GPU=1; TPL_CPU=8; TPL_MEM=48Gi; TPL_SHMEM=48Gi; TPL_RES="quotalplclkpgjgv" ;;
  local_hf_default)
    TPL_GPU=1; TPL_CPU=16; TPL_MEM=118Gi; TPL_SHMEM=118Gi; TPL_RES="quotalplclkpgjgv" ;;
  local_hf_heavy)
    TPL_GPU=1; TPL_CPU=24; TPL_MEM=160Gi; TPL_SHMEM=160Gi; TPL_RES="quotalplclkpgjgv" ;;
  *)
    echo "ERROR: Unsupported DLC_PROFILE: $DLC_PROFILE" >&2
    exit 1 ;;
esac
```

Then allow `DLC_WORKER_GPU`, `DLC_WORKER_CPU`, `DLC_WORKER_MEMORY`, `DLC_WORKER_SHARED_MEMORY`, and `DLC_RESOURCE_ID` to override those defaults.

- [ ] **Step 7: Print a resolved submission summary before submit**

Ensure `launch_job.sh` prints:

- `DLC_PROFILE`
- resolved GPU/CPU/memory/shared-memory/resource
- data sources
- final command payload

- [ ] **Step 8: Re-run the DLC script tests**

Run:

```bash
PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_dlc_scripts
```

Expected: the dry-run, command contract, and profile-resolution tests pass.

## Task 4: Add Stable Submit Wrappers And Upgrade Operator Docs

**Files:**
- Create: `scripts/dlc/submit_annotate.sh`
- Create: `scripts/dlc/submit_retry_failed.sh`
- Create: `scripts/dlc/submit_retry_incomplete.sh`
- Create: `scripts/dlc/submit_asset_list.sh`
- Modify: `docs/dlc/README.md`
- Modify: `docs/dlc/TESTING.md`
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `docs/usage/cli_reference.md`
- Create: `docs/changes/2026-04-16_dlc_balanced_upgrade.md`

- [ ] **Step 1: Add canonical submit wrappers**

Create these shell wrappers with a common pattern:

```bash
#!/bin/bash
set -euo pipefail

CODE_ROOT=${DLC_CODE_ROOT:-"/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator"}
SUBMIT_PY="$CODE_ROOT/scripts/dlc/submit_batch.py"

TOTAL=${TOTAL:-4}
NAME=${NAME:-annotate_assets}

python "$SUBMIT_PY" --total "$TOTAL" --name "$NAME" "$@"
```

Each wrapper must bake the intended canonical `--command_args` for its workflow:

- `submit_annotate.sh`
- `submit_retry_failed.sh`
- `submit_retry_incomplete.sh`
- `submit_asset_list.sh`

- [ ] **Step 2: Ensure wrappers support `--dry-run` transparently**

Run:

```bash
bash scripts/dlc/submit_annotate.sh --dry-run
```

Expected: the wrapper forwards `--dry-run` cleanly to `submit_batch.py`.

- [ ] **Step 3: Rewrite `docs/dlc/README.md` as an operator runbook**

The updated document must include these exact sections:

```markdown
## Supported Workflows
## Preflight Checklist
## Submission Methods
## Resource Profiles
## Monitoring And Logs
## Post-Run Validation
## Recovery And Rerun
## Backend Notes
```

The document must clearly explain:

- `local_hf` vs `openai_compatible`
- the new profile names
- wrapper scripts vs raw `submit_batch.py`
- the corrected chunk-mode contract

- [ ] **Step 4: Rewrite `docs/dlc/TESTING.md` into a real smoke/probe guide**

The updated file must include:

```markdown
## Smoke Test Scope
## Minimum Safe Test Size
## Required Evidence
## Pass/Fail Gates
## Escalation To Larger Runs
```

- [ ] **Step 5: Update top-level docs that mention DLC**

Apply these exact doc updates:

```markdown
README.md
- point operators to `docs/dlc/README.md` for the maintained DLC workflow

CLAUDE.md
- record the upgraded DLC chain and note that wrapper scripts are the preferred operator entrypoints

docs/usage/cli_reference.md
- keep CLI flags current for DLC chunk mode and rerun options
```

- [ ] **Step 6: Create the DLC upgrade change log**

Create `docs/changes/2026-04-16_dlc_balanced_upgrade.md` with these sections:

```markdown
## Research / Investigation
## Design Decisions
## Code Changes
## Testing
## Open Issues
```

Record:

- the duplicated chunk-arg bug
- why `python_runtime.sh` was added
- why only a few wrappers were added instead of copying the full `usd-scene-physics-prep` mode matrix

- [ ] **Step 7: Run lightweight doc/script verification**

Run:

```bash
PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_dlc_scripts
bash scripts/dlc/submit_annotate.sh --dry-run
bash scripts/dlc/submit_retry_failed.sh --dry-run
bash scripts/dlc/submit_retry_incomplete.sh --dry-run
```

Expected: wrapper scripts and docs align with actual script behavior.

## Task 5: Final DLC Verification And Handoff

**Files:**
- Verify: `scripts/dlc/submit_batch.py`
- Verify: `scripts/dlc/launch_job.sh`
- Verify: `scripts/dlc/python_runtime.sh`
- Verify: `scripts/dlc/run_task.sh`
- Verify: wrapper scripts
- Verify: `docs/dlc/README.md`
- Verify: `docs/dlc/TESTING.md`

- [ ] **Step 1: Run the full DLC verification suite**

Run:

```bash
PYTHONPATH=. .venv_dlc/bin/python -m unittest tests.test_dlc_scripts
```

Expected: PASS.

- [ ] **Step 2: Verify dry-run output for one canonical wrapper**

Run:

```bash
bash scripts/dlc/submit_annotate.sh --dry-run
```

Expected: the printed command chain shows exactly one chunk pair and the expected profile/runtime wrapper path.

- [ ] **Step 3: Verify direct `run_task.sh` usage behavior**

Run:

```bash
bash scripts/dlc/run_task.sh
```

Expected: usage is printed and exit status is nonzero.

- [ ] **Step 4: Verify wrapper-to-submit path for failure/retry workflows**

Run:

```bash
bash scripts/dlc/submit_retry_failed.sh --dry-run
bash scripts/dlc/submit_retry_incomplete.sh --dry-run
bash scripts/dlc/submit_asset_list.sh --dry-run --asset_list_file archive/temp_lists/failed_assets.txt
```

Expected: wrappers emit canonical commands without requiring operators to hand-assemble `--command_args`.

- [ ] **Step 5: Review the final change set without committing**

Run:

```bash
git diff --stat
git diff
```

Expected: the final diff shows a coherent DLC substrate upgrade, tests, wrappers, and operator docs. Do not create a commit unless the user explicitly asks.

## Self-Review Checklist

- [ ] Spec coverage check: Task 1 covers argument-contract tests; Task 2 covers runtime wrapper and `run_task.sh`; Task 3 covers launcher/batch submitter; Task 4 covers wrappers/docs/change log; Task 5 covers final verification.
- [ ] Draft-marker scan: search this plan for banned drafting markers and remove any accidental match before execution.
- [ ] Consistency check: keep the primary contract as `run_task.sh <chunk_id> <chunk_total> [extra main.py flags...]`; keep profiles limited to `api_light`, `local_hf_default`, and `local_hf_heavy`; keep the task surface annotation-first.

## Notes For The Implementer

- Use `apply_patch` for manual edits.
- Do not import Isaac-Sim-specific runtime logic from `usd-scene-physics-prep`.
- Do not submit real DLC jobs unless the user explicitly asks.
- Do not create any git commit unless the user explicitly asks.
