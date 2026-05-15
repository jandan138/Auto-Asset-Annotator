import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts" / "dlc"


class TestDLCScripts(unittest.TestCase):
    def test_submit_annotate_wrapper_shell_escapes_paths(self):
        env = os.environ.copy()
        env.update(
            {
                "INPUT_DIR": "/tmp/assets with spaces",
                "OUTPUT_DIR": "/tmp/out;semi",
            }
        )

        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "submit_annotate.sh"), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("--input_dir '/tmp/assets with spaces'", result.stdout)
        self.assertIn("--output_dir '/tmp/out;semi'", result.stdout)

    def test_submit_retry_failed_wrapper_shell_escapes_asset_list_path(self):
        with tempfile.NamedTemporaryFile(
            "w", delete=False, prefix="failed assets", suffix=".txt"
        ) as f:
            f.write("chair/abc123\n")
            asset_list = f.name
        self.addCleanup(lambda: os.path.exists(asset_list) and os.remove(asset_list))

        env = os.environ.copy()
        env.update(
            {
                "ASSET_LIST_FILE": asset_list,
            }
        )

        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "submit_retry_failed.sh"), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn(f"--asset_list_file {shlex.quote(asset_list)}", result.stdout)

    def test_submit_retry_incomplete_wrapper_shell_escapes_paths(self):
        env = os.environ.copy()
        env.update(
            {
                "INPUT_DIR": "/tmp/assets with spaces",
                "OUTPUT_DIR": "/tmp/out;semi",
            }
        )

        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "submit_retry_incomplete.sh"), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("--input_dir '/tmp/assets with spaces'", result.stdout)
        self.assertIn("--output_dir '/tmp/out;semi'", result.stdout)

    def test_submit_asset_list_wrapper_shell_escapes_paths(self):
        with tempfile.NamedTemporaryFile(
            "w", delete=False, prefix="failed assets", suffix=".txt"
        ) as f:
            f.write("chair/abc123\n")
            asset_list = f.name
        self.addCleanup(lambda: os.path.exists(asset_list) and os.remove(asset_list))

        env = os.environ.copy()
        env.update(
            {
                "INPUT_DIR": "/tmp/assets with spaces",
                "OUTPUT_DIR": "/tmp/out;semi",
            }
        )

        result = subprocess.run(
            [
                "bash",
                str(SCRIPTS_DIR / "submit_asset_list.sh"),
                "--dry-run",
                "--asset_list_file",
                asset_list,
            ],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("--input_dir '/tmp/assets with spaces'", result.stdout)
        self.assertIn("--output_dir '/tmp/out;semi'", result.stdout)
        self.assertIn(f"--asset_list_file {shlex.quote(asset_list)}", result.stdout)

    def test_python_runtime_supports_python_c_flag(self):
        result = subprocess.run(
            [
                "bash",
                str(SCRIPTS_DIR / "python_runtime.sh"),
                "-c",
                "print('runtime-ok')",
            ],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=os.environ.copy(),
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("runtime-ok", result.stdout)

    def test_run_task_without_args_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            code_root = Path(tmp)
            fake_python = code_root / ".venv_dlc" / "bin" / "python"
            fake_python.parent.mkdir(parents=True)
            fake_python.write_text("#!/bin/bash\nprintf 'fake-python %s\n' \"$*\"\n")
            fake_python.chmod(0o755)

            env = os.environ.copy()
            env["DLC_CODE_ROOT"] = str(code_root)

            result = subprocess.run(
                ["bash", str(SCRIPTS_DIR / "run_task.sh")],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Usage: run_task.sh <mode> [args...]", result.stdout)

    def test_submit_batch_supports_dry_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_root = Path(tmp)
            temp_scripts_dir = temp_root / "scripts" / "dlc"
            temp_scripts_dir.mkdir(parents=True)

            submit_batch_copy = temp_scripts_dir / "submit_batch.py"
            submit_batch_copy.write_text((SCRIPTS_DIR / "submit_batch.py").read_text())

            side_effect_path = temp_root / "launch_invoked.txt"
            fake_launch = temp_scripts_dir / "launch_job.sh"
            fake_launch.write_text(
                "#!/bin/bash\n"
                f"touch {side_effect_path}\n"
                "printf 'DLC_DRY_RUN=%s DLC_SUBMIT=%s\n' \"${DLC_DRY_RUN:-}\" \"${DLC_SUBMIT:-}\"\n"
                "printf 'launch invoked %s\n' \"$*\"\n"
            )
            fake_launch.chmod(0o755)

            result = subprocess.run(
                [
                    sys.executable,
                    str(submit_batch_copy),
                    "--total",
                    "2",
                    "--name",
                    "dryrun_test",
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
                cwd=temp_root,
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn("DRY RUN", result.stdout)
            self.assertIn("DLC_DRY_RUN=1 DLC_SUBMIT=0", result.stdout)
            self.assertIn("launch invoked dryrun_test 0 2", result.stdout)
            self.assertTrue(side_effect_path.exists())

    def test_submit_batch_defaults_to_dry_run_and_ignores_ambient_submit(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_root = Path(tmp)
            temp_scripts_dir = temp_root / "scripts" / "dlc"
            temp_scripts_dir.mkdir(parents=True)

            submit_batch_copy = temp_scripts_dir / "submit_batch.py"
            submit_batch_copy.write_text((SCRIPTS_DIR / "submit_batch.py").read_text())

            fake_launch = temp_scripts_dir / "launch_job.sh"
            fake_launch.write_text(
                "#!/bin/bash\n"
                "printf 'DLC_DRY_RUN=%s DLC_SUBMIT=%s\n' \"${DLC_DRY_RUN:-}\" \"${DLC_SUBMIT:-}\"\n"
                "printf 'launch invoked %s\n' \"$*\"\n"
            )
            fake_launch.chmod(0o755)

            env = os.environ.copy()
            env["DLC_SUBMIT"] = "1"

            result = subprocess.run(
                [
                    sys.executable,
                    str(submit_batch_copy),
                    "--total",
                    "1",
                    "--name",
                    "default_dryrun",
                ],
                capture_output=True,
                text=True,
                cwd=temp_root,
                env=env,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn("DLC_DRY_RUN=1 DLC_SUBMIT=0", result.stdout)
        self.assertIn("Mode: dry-run", result.stdout)

    def test_submit_batch_submit_sets_dlc_submit_for_launch_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_root = Path(tmp)
            temp_scripts_dir = temp_root / "scripts" / "dlc"
            temp_scripts_dir.mkdir(parents=True)

            submit_batch_copy = temp_scripts_dir / "submit_batch.py"
            submit_batch_copy.write_text((SCRIPTS_DIR / "submit_batch.py").read_text())

            fake_launch = temp_scripts_dir / "launch_job.sh"
            fake_launch.write_text(
                "#!/bin/bash\n"
                "printf 'DLC_DRY_RUN=%s DLC_SUBMIT=%s DLC_REAL_SUBMIT_CONFIRM=%s\n' \"${DLC_DRY_RUN:-}\" \"${DLC_SUBMIT:-}\" \"${DLC_REAL_SUBMIT_CONFIRM:-}\"\n"
                "printf 'launch invoked %s\n' \"$*\"\n"
            )
            fake_launch.chmod(0o755)

            result = subprocess.run(
                [
                    sys.executable,
                    str(submit_batch_copy),
                    "--total",
                    "1",
                    "--name",
                    "real_submit",
                    "--submit",
                ],
                capture_output=True,
                text=True,
                cwd=temp_root,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn("DLC_DRY_RUN=0 DLC_SUBMIT=1 DLC_REAL_SUBMIT_CONFIRM=real_submit_0_1", result.stdout)

    def test_submit_batch_dry_run_fails_nonzero_when_launcher_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            temp_root = Path(tmp)
            temp_scripts_dir = temp_root / "scripts" / "dlc"
            temp_scripts_dir.mkdir(parents=True)

            submit_batch_copy = temp_scripts_dir / "submit_batch.py"
            submit_batch_copy.write_text((SCRIPTS_DIR / "submit_batch.py").read_text())

            fake_launch = temp_scripts_dir / "launch_job.sh"
            fake_launch.write_text(
                "#!/bin/bash\n"
                "printf 'launcher failed %s\n' \"$*\"\n"
                "exit 23\n"
            )
            fake_launch.chmod(0o755)

            result = subprocess.run(
                [
                    sys.executable,
                    str(submit_batch_copy),
                    "--total",
                    "1",
                    "--name",
                    "bad_dryrun",
                    "--dry-run",
                ],
                capture_output=True,
                text=True,
                cwd=temp_root,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Mode: dry-run", result.stdout)
        self.assertIn("Failed chunks", result.stdout)

    def test_submit_batch_splits_command_args_and_preserves_empty_data_source_slot(
        self,
    ):
        with tempfile.TemporaryDirectory() as tmp:
            temp_root = Path(tmp)
            temp_scripts_dir = temp_root / "scripts" / "dlc"
            temp_scripts_dir.mkdir(parents=True)

            submit_batch_copy = temp_scripts_dir / "submit_batch.py"
            submit_batch_copy.write_text((SCRIPTS_DIR / "submit_batch.py").read_text())

            fake_launch = temp_scripts_dir / "launch_job.sh"
            fake_launch.write_text(
                "#!/bin/bash\n"
                "i=1\n"
                'for arg in "$@"; do\n'
                '  printf \'[%s]=<%s>\\n\' "$i" "$arg"\n'
                "  i=$((i + 1))\n"
                "done\n"
            )
            fake_launch.chmod(0o755)

            result = subprocess.run(
                [
                    sys.executable,
                    str(submit_batch_copy),
                    "--total",
                    "1",
                    "--name",
                    "argv_test",
                    "--dry-run",
                    "--command_args",
                    '--input_dir "/tmp/assets with spaces" --output_dir "/tmp/out;semi"',
                ],
                capture_output=True,
                text=True,
                cwd=temp_root,
            )

            self.assertEqual(result.returncode, 0)
            self.assertIn(
                "'' --input_dir '/tmp/assets with spaces' --output_dir '/tmp/out;semi'",
                result.stdout,
            )

    def test_launch_job_resolves_api_light_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_dlc = Path(tmp) / "dlc"
            fake_dlc.write_text("#!/bin/bash\nprintf '%s\n' \"$*\"\n")
            fake_dlc.chmod(0o755)

            env = os.environ.copy()
            env.update(
                {
                    "DLC_BIN": str(fake_dlc),
                    "DLC_CODE_ROOT": str(REPO_ROOT),
                    "DLC_PROFILE": "api_light",
                }
            )

            result = subprocess.run(
                [
                    "bash",
                    str(SCRIPTS_DIR / "launch_job.sh"),
                    "annotate",
                    "0",
                    "4",
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn("api_light", result.stdout)
        self.assertIn("Resolved config summary", result.stdout)
        self.assertIn("Resource ID:    quota1r947pmazvk", result.stdout)
        self.assertIn("Worker CPU:     14", result.stdout)
        self.assertIn("Worker Memory:  100Gi", result.stdout)

    def test_launch_job_defaults_to_dry_run_without_dlc_bin(self):
        env = os.environ.copy()
        env["DLC_CODE_ROOT"] = str(REPO_ROOT)
        env.pop("DLC_BIN", None)
        env.pop("DLC_SUBMIT", None)

        result = subprocess.run(
            [
                "bash",
                str(SCRIPTS_DIR / "launch_job.sh"),
                "dryrun_only",
                "0",
                "1",
            ],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Dry-run only", result.stdout)
        self.assertIn("Final command:", result.stdout)

    def test_launch_job_real_submit_requires_explicit_workspace_and_resource(self):
        env = os.environ.copy()
        env.update(
            {
                "DLC_BIN": "/bin/echo",
                "DLC_CODE_ROOT": str(REPO_ROOT),
                "DLC_SUBMIT": "1",
                "DLC_DRY_RUN": "0",
            }
        )
        env.pop("DLC_WORKSPACE_ID", None)
        env.pop("DLC_RESOURCE_ID", None)

        result = subprocess.run(
            [
                "bash",
                str(SCRIPTS_DIR / "launch_job.sh"),
                "real_guard",
                "0",
                "1",
            ],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DLC_WORKSPACE_ID", result.stderr)

    def test_launch_job_real_submit_requires_job_name_confirmation(self):
        env = os.environ.copy()
        env.update(
            {
                "DLC_BIN": "/bin/echo",
                "DLC_CODE_ROOT": str(REPO_ROOT),
                "DLC_SUBMIT": "1",
                "DLC_DRY_RUN": "0",
                "DLC_WORKSPACE_ID": "270969",
                "DLC_RESOURCE_ID": "quota1r947pmazvk",
            }
        )
        env.pop("DLC_REAL_SUBMIT_CONFIRM", None)

        result = subprocess.run(
            [
                "bash",
                str(SCRIPTS_DIR / "launch_job.sh"),
                "real_confirm_guard",
                "0",
                "1",
            ],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DLC_REAL_SUBMIT_CONFIRM", result.stderr)

    def test_launch_job_8gpu_uses_more_gpu_quota_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_dlc = Path(tmp) / "dlc"
            fake_dlc.write_text("#!/bin/bash\nprintf '%s\n' \"$*\"\n")
            fake_dlc.chmod(0o755)

            env = os.environ.copy()
            env.update(
                {
                    "DLC_BIN": str(fake_dlc),
                    "DLC_CODE_ROOT": str(REPO_ROOT),
                    "DLC_WORKER_GPU": "8",
                    "DLC_PROFILE": "local_hf_heavy",
                }
            )

            result = subprocess.run(
                [
                    "bash",
                    str(SCRIPTS_DIR / "launch_job.sh"),
                    "probe",
                    "0",
                    "1",
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Resource ID:    quotaksvqq2oh2pg", result.stdout)
        self.assertIn("Worker CPU:     128", result.stdout)
        self.assertIn("Worker Memory:  960Gi", result.stdout)

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

    def test_launch_job_shell_escapes_extra_args_in_final_command(self):
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
                    "",
                    "--input_dir",
                    "/tmp/assets with spaces",
                    "--output_dir",
                    "/tmp/out;semi",
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn("/tmp/assets\\ with\\ spaces", result.stdout)
        self.assertIn("/tmp/out\\;semi", result.stdout)

    def test_launch_job_embeds_worker_runtime_env_in_final_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_dlc = Path(tmp) / "dlc"
            fake_dlc.write_text("#!/bin/bash\nprintf '%s\n' \"$*\"\n")
            fake_dlc.chmod(0o755)

            env = os.environ.copy()
            env.update(
                {
                    "DLC_BIN": str(fake_dlc),
                    "DLC_CODE_ROOT": "/cpfs/user/zhuzihou/dev/Auto-Asset-Annotator",
                    "DLC_WORKER_SETUP_SCRIPT": "/cpfs/user/zhuzihou/conda-managed/bin/use-gcc-toolchain-hf-offline.sh",
                    "AUTO_ASSET_VENV": "/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310",
                    "UNSLOTH_COMPILE_LOCATION": "/cpfs/user/zhuzihou/tmp/auto asset cache",
                    "MODEL_BACKEND": "local_gemma4_multimodal",
                    "MODEL_PATH": "/cpfs/user/zhuzihou/models/gemma4/current",
                }
            )

            result = subprocess.run(
                [
                    "bash",
                    str(SCRIPTS_DIR / "launch_job.sh"),
                    "gemma4_probe",
                    "0",
                    "1",
                    "",
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
        self.assertIn("DLC_WORKER_SETUP_SCRIPT=", result.stdout)
        self.assertIn("AUTO_ASSET_VENV=", result.stdout)
        self.assertIn("UNSLOTH_COMPILE_LOCATION=", result.stdout)
        self.assertIn("MODEL_BACKEND=local_gemma4_multimodal", result.stdout)
        self.assertIn("MODEL_PATH=/cpfs/user/zhuzihou/models/gemma4/current", result.stdout)
        self.assertIn("/cpfs/user/zhuzihou/tmp/auto\\ asset\\ cache", result.stdout)

    def test_run_task_sources_worker_setup_before_python_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            code_root = Path(tmp)
            setup_script = code_root / "setup.sh"
            setup_script.write_text("export SETUP_MARKER=from-worker-setup\n")

            fake_runtime = code_root / "python_runtime.sh"
            fake_runtime.write_text(
                "#!/bin/bash\n"
                "printf 'SETUP_MARKER=%s\n' \"${SETUP_MARKER:-}\"\n"
                "printf '%s\n' \"$*\"\n"
            )
            fake_runtime.chmod(0o755)

            env = os.environ.copy()
            env.update(
                {
                    "DLC_CODE_ROOT": str(code_root),
                    "DLC_PYTHON_RUNTIME": str(fake_runtime),
                    "DLC_WORKER_SETUP_SCRIPT": str(setup_script),
                }
            )

            result = subprocess.run(
                [
                    "bash",
                    str(SCRIPTS_DIR / "run_task.sh"),
                    "0",
                    "1",
                    "--input_dir",
                    "/data/assets",
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn("SETUP_MARKER=from-worker-setup", result.stdout)

    def test_python_runtime_prefers_auto_asset_venv(self):
        with tempfile.TemporaryDirectory() as tmp:
            code_root = Path(tmp) / "repo"
            code_root.mkdir()
            fake_repo_package = code_root / "auto_asset_annotator"
            fake_repo_package.mkdir()
            (fake_repo_package / "__init__.py").write_text("")

            auto_asset_venv = Path(tmp) / "auto_asset_venv"
            fake_python = auto_asset_venv / "bin" / "python"
            fake_python.parent.mkdir(parents=True)
            fake_python.write_text(
                "#!/bin/bash\n"
                "if [ \"$1\" = \"-c\" ]; then exit 0; fi\n"
                "printf 'auto-asset-venv-python %s\n' \"$*\"\n"
            )
            fake_python.chmod(0o755)

            env = os.environ.copy()
            env.update(
                {
                    "DLC_CODE_ROOT": str(code_root),
                    "AUTO_ASSET_VENV": str(auto_asset_venv),
                }
            )

            result = subprocess.run(
                [
                    "bash",
                    str(SCRIPTS_DIR / "python_runtime.sh"),
                    "-m",
                    "auto_asset_annotator.main",
                    "--help",
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn("auto-asset-venv-python -m auto_asset_annotator.main --help", result.stdout)

    def test_python_runtime_adds_src_layout_to_pythonpath(self):
        with tempfile.TemporaryDirectory() as tmp:
            code_root = Path(tmp) / "repo"
            package_root = code_root / "src" / "auto_asset_annotator"
            package_root.mkdir(parents=True)
            (package_root / "__init__.py").write_text("SRC_LAYOUT_MARKER = 'ok'\n")

            auto_asset_venv = Path(tmp) / "auto_asset_venv"
            fake_python = auto_asset_venv / "bin" / "python"
            fake_python.parent.mkdir(parents=True)
            fake_python.symlink_to(sys.executable)

            env = os.environ.copy()
            env.update(
                {
                    "DLC_CODE_ROOT": str(code_root),
                    "AUTO_ASSET_VENV": str(auto_asset_venv),
                }
            )

            result = subprocess.run(
                [
                    "bash",
                    str(SCRIPTS_DIR / "python_runtime.sh"),
                    "-c",
                    "import auto_asset_annotator; print(auto_asset_annotator.SRC_LAYOUT_MARKER)",
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn("ok", result.stdout)

    def test_run_task_batch_mode_forwards_main_flags_after_chunk_args(self):
        with tempfile.TemporaryDirectory() as tmp:
            code_root = Path(tmp)
            fake_runtime = code_root / "python_runtime.sh"
            fake_runtime.write_text("#!/bin/bash\nprintf '%s\n' \"$*\"\n")
            fake_runtime.chmod(0o755)

            fake_python = code_root / ".venv_dlc" / "bin" / "python"
            fake_python.parent.mkdir(parents=True)
            fake_python.write_text("#!/bin/bash\nprintf 'fake-python %s\n' \"$*\"\n")
            fake_python.chmod(0o755)

            env = os.environ.copy()
            env["DLC_PYTHON_RUNTIME"] = str(fake_runtime)
            env["DLC_CODE_ROOT"] = str(code_root)

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
        self.assertIn(
            "-m auto_asset_annotator.main --num_chunks 4 --chunk_index 0 "
            "--input_dir /data/assets --output_dir /data/output",
            result.stdout,
        )

    def test_run_task_batch_mode_forwards_supported_env_vars_as_cli_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            code_root = Path(tmp)
            fake_runtime = code_root / "python_runtime.sh"
            fake_runtime.write_text("#!/bin/bash\nprintf '%s\n' \"$*\"\n")
            fake_runtime.chmod(0o755)

            env = os.environ.copy()
            env.update(
                {
                    "DLC_PYTHON_RUNTIME": str(fake_runtime),
                    "DLC_CODE_ROOT": str(code_root),
                    "MODEL_PATH": "/models/demo",
                    "MODEL_BACKEND": "openai_compatible",
                    "API_BASE_URL": "https://example.invalid/v1",
                    "API_KEY_ENV": "TEST_API_KEY",
                }
            )

            result = subprocess.run(
                [
                    "bash",
                    str(SCRIPTS_DIR / "run_task.sh"),
                    "0",
                    "4",
                    "--input_dir",
                    "/data/assets",
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn("--model_path /models/demo", result.stdout)
        self.assertIn("--model_backend openai_compatible", result.stdout)
        self.assertIn("--api_base_url https://example.invalid/v1", result.stdout)
        self.assertIn("--api_key_env TEST_API_KEY", result.stdout)

    def test_python_runtime_rejects_missing_api_requirements(self):
        with tempfile.TemporaryDirectory() as tmp:
            code_root = Path(tmp)
            fake_repo_package = code_root / "auto_asset_annotator"
            fake_repo_package.mkdir()
            (fake_repo_package / "__init__.py").write_text("")

            fake_python = code_root / ".venv_dlc" / "bin" / "python"
            fake_python.parent.mkdir(parents=True)
            fake_python.write_text(
                '#!/bin/bash\nif [ "$1" = "-c" ]; then exit 0; fi\nexit 0\n'
            )
            fake_python.chmod(0o755)

            env = os.environ.copy()
            env["DLC_CODE_ROOT"] = str(code_root)
            env["MODEL_BACKEND"] = "openai_compatible"
            env.pop("API_BASE_URL", None)
            env.pop("API_KEY_ENV", None)

            result = subprocess.run(
                [
                    "bash",
                    str(SCRIPTS_DIR / "python_runtime.sh"),
                    "-m",
                    "auto_asset_annotator.main",
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("API_BASE_URL is required", result.stderr)

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

    def test_submit_asset_list_dry_run_accepts_existing_file(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("chair/abc123\n")
            asset_list = f.name
        self.addCleanup(lambda: os.path.exists(asset_list) and os.remove(asset_list))
        result = subprocess.run(
            [
                "bash",
                str(SCRIPTS_DIR / "submit_asset_list.sh"),
                "--dry-run",
                "--asset_list_file",
                asset_list,
            ],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )
        self.assertEqual(result.returncode, 0)

    def test_submit_probe_supports_dry_run(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("chair/abc123\n")
            asset_list = f.name
        self.addCleanup(lambda: os.path.exists(asset_list) and os.remove(asset_list))

        env = os.environ.copy()
        env.update(
            {
                "MODEL_BACKEND": "openai_compatible",
                "ASSET_LIST_FILE": asset_list,
                "API_BASE_URL": "https://example.invalid/v1",
                "API_KEY_ENV": "TEST_API_KEY",
            }
        )

        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "submit_probe.sh"), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("annotate_probe", result.stdout)
        self.assertIn("--asset_list_file", result.stdout)

    def test_submit_probe_supports_gemma4_backend_dry_run(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("chair/abc123\n")
            asset_list = f.name
        self.addCleanup(lambda: os.path.exists(asset_list) and os.remove(asset_list))

        env = os.environ.copy()
        env.update(
            {
                "MODEL_BACKEND": "local_gemma4_multimodal",
                "MODEL_PATH": "/cpfs/user/zhuzihou/models/gemma4/current",
                "ASSET_LIST_FILE": asset_list,
            }
        )

        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "submit_probe.sh"), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("MODEL_BACKEND=local_gemma4_multimodal", result.stdout)
        self.assertIn("--model_backend local_gemma4_multimodal", result.stdout)
        self.assertIn("--model_path /cpfs/user/zhuzihou/models/gemma4/current", result.stdout)
        self.assertIn("--asset_list_file", result.stdout)

    def test_submit_probe_rejects_gemma4_without_model_path(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("chair/abc123\n")
            asset_list = f.name
        self.addCleanup(lambda: os.path.exists(asset_list) and os.remove(asset_list))

        env = os.environ.copy()
        env.update(
            {
                "MODEL_BACKEND": "local_gemma4_multimodal",
                "ASSET_LIST_FILE": asset_list,
            }
        )
        env.pop("MODEL_PATH", None)

        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "submit_probe.sh"), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MODEL_PATH is required", result.stderr)

    def test_submit_probe_enforced_model_flags_win_over_extra_main_args(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("chair/abc123\n")
            asset_list = f.name
        self.addCleanup(lambda: os.path.exists(asset_list) and os.remove(asset_list))

        env = os.environ.copy()
        env.update(
            {
                "MODEL_BACKEND": "local_gemma4_multimodal",
                "MODEL_PATH": "/cpfs/user/zhuzihou/models/gemma4/current",
                "ASSET_LIST_FILE": asset_list,
                "EXTRA_MAIN_ARGS": "--model_backend local_hf --model_path /bad/model",
            }
        )

        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "submit_probe.sh"), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
        )

        self.assertEqual(result.returncode, 0)
        self.assertLess(
            result.stdout.find("--model_backend local_hf"),
            result.stdout.rfind("--model_backend local_gemma4_multimodal"),
        )
        self.assertLess(
            result.stdout.find("--model_path /bad/model"),
            result.stdout.rfind("--model_path /cpfs/user/zhuzihou/models/gemma4/current"),
        )

    def test_submit_probe_requires_explicit_backend(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("chair/abc123\n")
            asset_list = f.name
        self.addCleanup(lambda: os.path.exists(asset_list) and os.remove(asset_list))

        env = os.environ.copy()
        env["ASSET_LIST_FILE"] = asset_list
        env.pop("MODEL_BACKEND", None)

        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "submit_probe.sh"), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires explicit MODEL_BACKEND", result.stderr)

    def test_submit_probe_requires_explicit_asset_list(self):
        env = os.environ.copy()
        env["MODEL_BACKEND"] = "local_hf"
        env.pop("ASSET_LIST_FILE", None)

        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "submit_probe.sh"), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires ASSET_LIST_FILE", result.stderr)

    def test_submit_gemma4_reannotate_rejects_legacy_output_dirs(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("basket/6c68230d67112b1dfd2bd7fa9322c756\n")
            asset_list = f.name
        self.addCleanup(lambda: os.path.exists(asset_list) and os.remove(asset_list))

        env = os.environ.copy()
        env.update(
            {
                "ASSET_LIST_FILE": asset_list,
                "OUTPUT_DIR": "./output",
            }
        )

        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "submit_gemma4_reannotate.sh"), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("refusing unsafe Gemma4 output directory", result.stderr)

    def test_submit_gemma4_reannotate_requires_annotation_runs_output_shape(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("basket/6c68230d67112b1dfd2bd7fa9322c756\n")
            asset_list = f.name
        self.addCleanup(lambda: os.path.exists(asset_list) and os.remove(asset_list))

        unsafe_outputs = [
            "/data/results",
            "/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/output",
            "/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/run_id/output/nested",
            "/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets/category/asset/output",
        ]

        for output_dir in unsafe_outputs:
            with self.subTest(output_dir=output_dir):
                env = os.environ.copy()
                env.update(
                    {
                        "ASSET_LIST_FILE": asset_list,
                        "OUTPUT_DIR": output_dir,
                    }
                )

                result = subprocess.run(
                    ["bash", str(SCRIPTS_DIR / "submit_gemma4_reannotate.sh"), "--dry-run"],
                    capture_output=True,
                    text=True,
                    cwd=REPO_ROOT,
                    env=env,
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("annotation_runs/<run_id>/output", result.stderr)

    def test_submit_gemma4_reannotate_rejects_protected_extra_main_args(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("basket/6c68230d67112b1dfd2bd7fa9322c756\n")
            asset_list = f.name
        self.addCleanup(lambda: os.path.exists(asset_list) and os.remove(asset_list))

        protected_args = [
            "--output_dir ./output",
            "--output_dir=./output",
            "--input_dir /tmp/other-assets",
            "--asset_list_file /tmp/other-list.txt",
            "--num_chunks 1",
            "--chunk_index 0",
        ]

        for extra_args in protected_args:
            with self.subTest(extra_args=extra_args):
                env = os.environ.copy()
                env.update(
                    {
                        "ASSET_LIST_FILE": asset_list,
                        "EXTRA_MAIN_ARGS": extra_args,
                    }
                )

                result = subprocess.run(
                    ["bash", str(SCRIPTS_DIR / "submit_gemma4_reannotate.sh"), "--dry-run"],
                    capture_output=True,
                    text=True,
                    cwd=REPO_ROOT,
                    env=env,
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("refusing protected EXTRA_MAIN_ARGS", result.stderr)

    def test_submit_gemma4_reannotate_dry_run_uses_isolated_output(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("basket/6c68230d67112b1dfd2bd7fa9322c756\n")
            asset_list = f.name
        self.addCleanup(lambda: os.path.exists(asset_list) and os.remove(asset_list))

        safe_output = (
            "/cpfs/user/zhuzihou/assets/dedup_workspaces/"
            "test0_transitive_apply_parallel/annotation_runs/"
            "20260514_gemma4_probe_v1/output"
        )
        env = os.environ.copy()
        env.update(
            {
                "ASSET_LIST_FILE": asset_list,
                "OUTPUT_DIR": safe_output,
                "INPUT_DIR": "/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets",
            }
        )

        result = subprocess.run(
            ["bash", str(SCRIPTS_DIR / "submit_gemma4_reannotate.sh"), "--dry-run"],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("MODEL_BACKEND=local_gemma4_multimodal", result.stdout)
        self.assertIn("--model_backend local_gemma4_multimodal", result.stdout)
        self.assertIn(f"--output_dir {safe_output}", result.stdout)
        self.assertIn("annotation_runs", result.stdout)

    def test_python_runtime_rejects_missing_gemma4_model_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            code_root = Path(tmp)
            fake_repo_package = code_root / "auto_asset_annotator"
            fake_repo_package.mkdir()
            (fake_repo_package / "__init__.py").write_text("")

            fake_python = code_root / ".venv_dlc" / "bin" / "python"
            fake_python.parent.mkdir(parents=True)
            fake_python.write_text(
                '#!/bin/bash\nif [ "$1" = "-c" ]; then exit 0; fi\nexit 0\n'
            )
            fake_python.chmod(0o755)

            env = os.environ.copy()
            env["DLC_CODE_ROOT"] = str(code_root)
            env["MODEL_BACKEND"] = "local_gemma4_multimodal"
            env["MODEL_PATH"] = "/tmp/does-not-exist-gemma4"

            result = subprocess.run(
                [
                    "bash",
                    str(SCRIPTS_DIR / "python_runtime.sh"),
                    "-m",
                    "auto_asset_annotator.main",
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MODEL_PATH does not exist", result.stderr)

    def test_python_runtime_requires_gemma4_model_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            code_root = Path(tmp)
            fake_repo_package = code_root / "auto_asset_annotator"
            fake_repo_package.mkdir()
            (fake_repo_package / "__init__.py").write_text("")

            fake_python = code_root / ".venv_dlc" / "bin" / "python"
            fake_python.parent.mkdir(parents=True)
            fake_python.write_text(
                '#!/bin/bash\nif [ "$1" = "-c" ]; then exit 0; fi\nexit 0\n'
            )
            fake_python.chmod(0o755)

            env = os.environ.copy()
            env["DLC_CODE_ROOT"] = str(code_root)
            env["MODEL_BACKEND"] = "local_gemma4_multimodal"
            env.pop("MODEL_PATH", None)

            result = subprocess.run(
                [
                    "bash",
                    str(SCRIPTS_DIR / "python_runtime.sh"),
                    "-m",
                    "auto_asset_annotator.main",
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MODEL_PATH is required", result.stderr)

    def test_python_runtime_rejects_cli_only_missing_gemma4_model_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            code_root = Path(tmp)
            fake_repo_package = code_root / "auto_asset_annotator"
            fake_repo_package.mkdir()
            (fake_repo_package / "__init__.py").write_text("")

            fake_python = code_root / ".venv_dlc" / "bin" / "python"
            fake_python.parent.mkdir(parents=True)
            fake_python.write_text(
                '#!/bin/bash\nif [ "$1" = "-c" ]; then exit 0; fi\nexit 0\n'
            )
            fake_python.chmod(0o755)

            env = os.environ.copy()
            env["DLC_CODE_ROOT"] = str(code_root)
            env.pop("MODEL_BACKEND", None)
            env.pop("MODEL_PATH", None)

            result = subprocess.run(
                [
                    "bash",
                    str(SCRIPTS_DIR / "python_runtime.sh"),
                    "-m",
                    "auto_asset_annotator.main",
                    "--model_backend",
                    "local_gemma4_multimodal",
                    "--model_path",
                    "/tmp/does-not-exist-gemma4",
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MODEL_PATH does not exist", result.stderr)

    def test_run_task_named_mode_forwards_supported_env_vars_as_cli_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            code_root = Path(tmp)
            fake_runtime = code_root / "python_runtime.sh"
            fake_runtime.write_text("#!/bin/bash\nprintf '%s\n' \"$*\"\n")
            fake_runtime.chmod(0o755)

            env = os.environ.copy()
            env.update(
                {
                    "DLC_PYTHON_RUNTIME": str(fake_runtime),
                    "DLC_CODE_ROOT": str(code_root),
                    "MODEL_PATH": "/models/demo",
                    "MODEL_BACKEND": "openai_compatible",
                    "API_BASE_URL": "https://example.invalid/v1",
                    "API_KEY_ENV": "TEST_API_KEY",
                }
            )

            result = subprocess.run(
                [
                    "bash",
                    str(SCRIPTS_DIR / "run_task.sh"),
                    "annotate",
                    "--input_dir",
                    "/data/assets",
                ],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
            )

        self.assertEqual(result.returncode, 0)
        self.assertIn("--prompt_type extract_object_attributes_prompt", result.stdout)
        self.assertIn("--model_path /models/demo", result.stdout)
        self.assertIn("--model_backend openai_compatible", result.stdout)
        self.assertIn("--api_base_url https://example.invalid/v1", result.stdout)
        self.assertIn("--api_key_env TEST_API_KEY", result.stdout)

    def test_run_task_custom_without_command_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            code_root = Path(tmp)
            fake_runtime = code_root / "python_runtime.sh"
            fake_runtime.write_text("#!/bin/bash\nprintf '%s\n' \"$*\"\n")
            fake_runtime.chmod(0o755)

            env = os.environ.copy()
            env.update(
                {
                    "DLC_PYTHON_RUNTIME": str(fake_runtime),
                    "DLC_CODE_ROOT": str(code_root),
                }
            )

            result = subprocess.run(
                ["bash", str(SCRIPTS_DIR / "run_task.sh"), "custom"],
                capture_output=True,
                text=True,
                cwd=REPO_ROOT,
                env=env,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("ERROR: Custom mode requires a Python command", result.stderr)


if __name__ == "__main__":
    unittest.main()
