import os
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
        env = os.environ.copy()
        env.update(
            {
                "ASSET_LIST_FILE": "/tmp/failed assets.txt",
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
        self.assertIn("--asset_list_file '/tmp/failed assets.txt'", result.stdout)

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
                "/tmp/failed assets.txt",
            ],
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
            env=env,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("--input_dir '/tmp/assets with spaces'", result.stdout)
        self.assertIn("--output_dir '/tmp/out;semi'", result.stdout)
        self.assertIn("--asset_list_file '/tmp/failed assets.txt'", result.stdout)

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
            self.assertIn("launch_job.sh dryrun_test 0 2", result.stdout)
            self.assertFalse(side_effect_path.exists())

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
        self.assertIn("--worker_cpu=8", result.stdout)

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
