#!/usr/bin/env python3
"""
Submit batch DLC jobs for Auto-Asset-Annotator.

This script submits multiple chunked annotation jobs to Alibaba Cloud PAI-DLC.
It loops through chunk IDs and calls launch_job.sh for each chunk.

Usage:
    python scripts/dlc/submit_batch.py --total 4 --name asset_annotation
    python scripts/dlc/submit_batch.py --total 10 --name annotation --max-total 50
"""

import argparse
import os
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional


def submit_jobs(
    chunk_total: int,
    task_name: str,
    data_sources: Optional[str] = None,
    command_args: Optional[str] = None,
    max_total: int = 100,
    dry_run: bool = True,
) -> None:
    """
    Submit batch DLC jobs for distributed annotation.

    Args:
        chunk_total: Total number of chunks to submit
        task_name: Base name for the task
        data_sources: Optional comma-separated data source IDs for DLC
        command_args: Extra auto_asset_annotator.main CLI flags for chunk mode
        max_total: Maximum allowed chunk count for safety
        dry_run: Print resolved launcher commands without submitting jobs
    """
    # Find project root (3 levels up from this script: scripts/dlc/submit_batch.py)
    repo_root = Path(__file__).resolve().parents[2]
    launch_script = repo_root / "scripts" / "dlc" / "launch_job.sh"

    if not launch_script.exists():
        print(f"ERROR: launch script not found: {launch_script}", file=sys.stderr)
        raise SystemExit(1)

    # Safety guard: prevent accidental massive submissions
    if chunk_total > max_total:
        print(
            f"ERROR: chunk_total={chunk_total} exceeds --max-total={max_total}. "
            "Pass a larger --max-total to override.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    successful: List[int] = []
    failed: List[int] = []
    dry_run_commands: List[str] = []

    for chunk_id in range(chunk_total):
        cmd: List[str] = [
            "bash",
            str(launch_script),
            task_name,
            str(chunk_id),
            str(chunk_total),
        ]

        # Arg 4: optional data_sources. Preserve positional meaning for arg 5+.
        if data_sources is not None:
            cmd.append(data_sources)
        elif command_args:
            cmd.append("")

        # Arg 5+: extra main.py flags for run_task.sh chunk mode
        if command_args:
            cmd.extend(shlex.split(command_args))

        command_str = shlex.join(cmd)

        env = os.environ.copy()

        if dry_run:
            env["DLC_DRY_RUN"] = "1"
            env["DLC_SUBMIT"] = "0"
            dry_run_commands.append(command_str)
            print(f"DRY RUN chunk {chunk_id}/{chunk_total - 1}: {command_str}")
            try:
                subprocess.run(cmd, check=True, cwd=str(repo_root), env=env)
                successful.append(chunk_id)
            except subprocess.CalledProcessError:
                failed.append(chunk_id)
            continue

        env["DLC_DRY_RUN"] = "0"
        env["DLC_SUBMIT"] = "1"
        env["DLC_REAL_SUBMIT_CONFIRM"] = f"{task_name}_{chunk_id}_{chunk_total}"
        print(f"Submitting chunk {chunk_id}/{chunk_total - 1}: {command_str}")

        # Exponential backoff retry: up to 3 retries with 1s/2s/4s delays
        max_retries = 3
        success = False
        for attempt in range(max_retries + 1):
            try:
                subprocess.run(cmd, check=True, cwd=str(repo_root), env=env)
                success = True
                break
            except subprocess.CalledProcessError as exc:
                if attempt < max_retries:
                    wait = 2**attempt  # 1, 2, 4 seconds
                    print(
                        f"  Attempt {attempt + 1} failed (exit {exc.returncode}), "
                        f"retrying in {wait}s...",
                        file=sys.stderr,
                    )
                    time.sleep(wait)
                else:
                    print(
                        f"  Chunk {chunk_id} failed after {max_retries + 1} attempts.",
                        file=sys.stderr,
                    )

        if success:
            successful.append(chunk_id)
        else:
            failed.append(chunk_id)

    # Summary report
    print(f"\n=== Submission summary ===")
    print(f"  Total chunks: {chunk_total}")
    print(f"  Successful chunks ({len(successful)}): {successful}")
    print(f"  Failed chunks    ({len(failed)}): {failed}")

    if dry_run:
        print("  Mode: dry-run")
        print(f"  Resolved launcher commands ({len(dry_run_commands)}):")
        for command in dry_run_commands:
            print(f"    {command}")
        if failed:
            print("\nDRY RUN failed: one or more launcher validations failed.")
            raise SystemExit(1)
        print("\nDRY RUN complete: no jobs were submitted.")
        return

    if failed:
        print("\nSome chunks failed to submit. Check the logs above for details.")
        raise SystemExit(1)
    else:
        print("\nAll chunks submitted successfully!")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Submit batch DLC jobs for Auto-Asset-Annotator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run 4 chunks for asset annotation (default)
  python scripts/dlc/submit_batch.py --total 4 --name asset_annotation

  # Dry-run with custom data sources
  python scripts/dlc/submit_batch.py --total 8 --name annotation \\
      --data_sources "d-source1,d-source2"

  # Submit with extra main.py chunk-mode flags
  python scripts/dlc/submit_batch.py --total 4 --name annotation \\
      --command_args "--input_dir /data/assets --output_dir /data/output"

  # Preview resolved launcher commands without submitting jobs
  python scripts/dlc/submit_batch.py --total 2 --name dryrun_test --dry-run

  # Submit real DLC jobs after reviewing dry-run output
  DLC_WORKSPACE_ID=270969 DLC_RESOURCE_ID=quota1r947pmazvk \\
  python scripts/dlc/submit_batch.py --total 4 --name asset_annotation --submit

  # Increase max-total limit for large batches
  python scripts/dlc/submit_batch.py --total 200 --name big_batch --max-total 250
        """,
    )
    parser.add_argument(
        "--total",
        type=int,
        required=True,
        help="Total number of chunks to submit",
    )
    parser.add_argument(
        "--name",
        type=str,
        default="asset_annotation",
        help="Base task name for the jobs (default: asset_annotation)",
    )
    parser.add_argument(
        "--data_sources",
        "--data-sources",
        type=str,
        default=None,
        help="Comma-separated data source IDs for DLC (default: use launch_job.sh default)",
    )
    parser.add_argument(
        "--command_args",
        "--command-args",
        type=str,
        default=None,
        help="Extra auto_asset_annotator.main flags for chunk mode (e.g., '--input_dir /path --output_dir /path')",
    )
    parser.add_argument(
        "--max-total",
        type=int,
        default=100,
        help="Maximum allowed chunk count to prevent accidental massive submissions (default: 100)",
    )
    submit_mode = parser.add_mutually_exclusive_group()
    submit_mode.add_argument(
        "--dry-run",
        dest="submit",
        action="store_false",
        default=False,
        help="Validate resolved launcher commands without submitting jobs (default)",
    )
    submit_mode.add_argument(
        "--submit",
        dest="submit",
        action="store_true",
        help="Submit real DLC jobs. Requires launch_job.sh real-submit guards to pass.",
    )
    args = parser.parse_args()

    if args.total <= 0:
        print("ERROR: --total must be a positive integer", file=sys.stderr)
        raise SystemExit(2)

    submit_jobs(
        args.total,
        args.name,
        args.data_sources,
        args.command_args,
        args.max_total,
        dry_run=not args.submit,
    )


if __name__ == "__main__":
    main()
