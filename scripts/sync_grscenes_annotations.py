#!/usr/bin/env python3
"""
Sync Auto-Asset wrapped annotations into GRScenes per-asset metadata files.

Source shape:
    {source_dir}/{category}/{asset_id}_annotation.json

Target shape:
    {target_dir}/{category}/{asset_id}/{asset_id}_annotation.json

The script updates only semantic fields and preserves GRScenes metadata fields
such as uid, asset_type, size fields, orientation, and softlink flags.
"""

import argparse
import json
import shutil
from pathlib import Path
from typing import Iterable, Optional


SEMANTIC_FIELDS = ["description", "material", "dimensions", "mass", "placement"]
SUMMARY_KEYS = [
    "source_files",
    "matched_target",
    "updated",
    "skipped",
    "failed",
    "no_target",
    "source_raw_output",
    "bad_source",
    "bad_target",
]


def is_empty(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, list):
        return len(value) == 0
    return False


def parse_placement(value) -> list:
    if is_empty(value):
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value).split(",") if item.strip()]


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json_atomic(path: Path, data) -> None:
    tmp_path = path.with_name(f"{path.name}.tmp-sync")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")
    tmp_path.replace(path)


def is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def validate_backup_dir(backup_dir: Path, target_dir: Path) -> None:
    backup_resolved = backup_dir.resolve()
    target_resolved = target_dir.resolve()
    if backup_resolved == target_resolved or is_relative_to(backup_resolved, target_resolved):
        raise ValueError("backup_dir must be outside target_dir")


def source_path_for_asset(source_dir: Path, asset: str) -> Path:
    category, asset_id = asset.split("/", 1)
    return source_dir / category / f"{asset_id}_annotation.json"


def iter_source_files(
    source_dir: Path,
    category: Optional[str] = None,
    asset_list_file: Optional[Path] = None,
    limit: Optional[int] = None,
) -> Iterable[Path]:
    if asset_list_file:
        with asset_list_file.open("r", encoding="utf-8") as f:
            files = [
                source_path_for_asset(source_dir, line.strip())
                for line in f
                if line.strip()
            ]
    elif category:
        files = sorted((source_dir / category).glob("*_annotation.json"))
    else:
        files = sorted(source_dir.glob("*/*_annotation.json"))

    if limit is not None:
        files = files[:limit]
    return files


def asset_from_source_path(source_dir: Path, source_file: Path):
    parts = source_file.relative_to(source_dir).parts
    if len(parts) != 2:
        raise ValueError("source_path_not_category_file")
    category, filename = parts
    if not filename.endswith("_annotation.json"):
        raise ValueError("source_filename_not_annotation_json")
    asset_id = filename[: -len("_annotation.json")]
    return category, asset_id


def normalized_field_value(field: str, value):
    if field == "placement":
        return parse_placement(value)
    return value


def should_update_field(field: str, old_value, new_value, overwrite: bool) -> bool:
    new_normalized = normalized_field_value(field, new_value)
    old_normalized = normalized_field_value(field, old_value)
    if is_empty(new_normalized):
        return False
    if not overwrite and not is_empty(old_normalized):
        return False
    return old_normalized != new_normalized


def fail_record(source_file: Path, reason: str, dry_run: bool, target_file=None):
    record = {
        "action": "failed",
        "reason": reason,
        "source": str(source_file),
        "target": str(target_file) if target_file else None,
        "dry_run": dry_run,
    }
    return record


def process_one(
    source_dir: Path,
    target_dir: Path,
    source_file: Path,
    *,
    dry_run: bool,
    overwrite: bool,
    backup_dir: Optional[Path],
) -> tuple[dict, dict]:
    try:
        category, asset_id = asset_from_source_path(source_dir, source_file)
    except ValueError as exc:
        return fail_record(source_file, str(exc), dry_run), {"failed": 1, "bad_source": 1}

    target_file = target_dir / category / asset_id / f"{asset_id}_annotation.json"
    base_record = {
        "source": str(source_file),
        "target": str(target_file),
        "asset": f"{category}/{asset_id}",
        "dry_run": dry_run,
    }

    if not target_file.exists():
        record = dict(base_record, action="no_target", reason="missing_target")
        return record, {"no_target": 1}

    try:
        source_data = load_json(source_file)
    except Exception as exc:
        return (
            dict(base_record, action="failed", reason="source_json_error", error=str(exc)),
            {"failed": 1, "bad_source": 1},
        )

    if not isinstance(source_data, dict) or len(source_data) != 1:
        return (
            dict(base_record, action="failed", reason="source_top_level_not_single_key"),
            {"failed": 1, "bad_source": 1},
        )

    source_key, source_annotation = next(iter(source_data.items()))
    expected_key = f"{category}/{asset_id}"
    if source_key != expected_key:
        return (
            dict(
                base_record,
                action="failed",
                reason="source_key_path_mismatch",
                source_key=source_key,
                expected_key=expected_key,
            ),
            {"failed": 1, "bad_source": 1},
        )

    if not isinstance(source_annotation, dict):
        return (
            dict(base_record, action="failed", reason="source_annotation_not_object"),
            {"failed": 1, "bad_source": 1},
        )

    if "raw_output" in source_annotation:
        return (
            dict(base_record, action="skipped", reason="source_raw_output"),
            {"skipped": 1, "source_raw_output": 1},
        )

    if source_annotation.get("category") not in (None, category):
        return (
            dict(
                base_record,
                action="failed",
                reason="source_category_mismatch",
                source_category=source_annotation.get("category"),
                expected_category=category,
            ),
            {"failed": 1, "bad_source": 1},
        )

    try:
        target_data = load_json(target_file)
    except Exception as exc:
        return (
            dict(base_record, action="failed", reason="target_json_error", error=str(exc)),
            {"failed": 1, "bad_target": 1},
        )

    if not isinstance(target_data, dict):
        return (
            dict(base_record, action="failed", reason="target_not_object"),
            {"failed": 1, "bad_target": 1},
        )
    if target_data.get("uid") != asset_id:
        return (
            dict(
                base_record,
                action="failed",
                reason="target_uid_mismatch",
                target_uid=target_data.get("uid"),
                expected_uid=asset_id,
            ),
            {"failed": 1, "bad_target": 1},
        )
    if target_data.get("category") != category:
        return (
            dict(
                base_record,
                action="failed",
                reason="target_category_mismatch",
                target_category=target_data.get("category"),
                expected_category=category,
            ),
            {"failed": 1, "bad_target": 1},
        )

    changes = {}
    updated_target = dict(target_data)
    for field in SEMANTIC_FIELDS:
        old_value = target_data.get(field)
        new_value = source_annotation.get(field)
        if not should_update_field(field, old_value, new_value, overwrite):
            continue
        normalized_new = normalized_field_value(field, new_value)
        changes[field] = {"old": normalized_field_value(field, old_value), "new": normalized_new}
        updated_target[field] = normalized_new

    if not changes:
        return (
            dict(base_record, action="skipped", reason="no_changes_needed"),
            {"matched_target": 1, "skipped": 1},
        )

    backup_path = None
    if not dry_run:
        if backup_dir is None:
            raise ValueError("backup_dir is required when dry_run=False")
        backup_path = backup_dir / target_file.relative_to(target_dir)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        if backup_path.exists():
            raise ValueError(f"backup target already exists: {backup_path}")
        shutil.copy2(target_file, backup_path)
        write_json_atomic(target_file, updated_target)

    return (
        dict(
            base_record,
            action="updated",
            fields=changes,
            backup=str(backup_path) if backup_path else None,
        ),
        {"matched_target": 1, "updated": 1},
    )


def add_counts(summary: dict, counts: dict) -> None:
    for key, value in counts.items():
        summary[key] = summary.get(key, 0) + value


def sync_annotations(
    source_dir,
    target_dir,
    *,
    audit_jsonl,
    backup_dir=None,
    dry_run=True,
    overwrite=False,
    category=None,
    asset_list_file=None,
    limit=None,
    summary_json=None,
) -> dict:
    source_dir = Path(source_dir)
    target_dir = Path(target_dir)
    audit_jsonl = Path(audit_jsonl)
    backup_dir = Path(backup_dir) if backup_dir else None
    asset_list_file = Path(asset_list_file) if asset_list_file else None
    summary_json = Path(summary_json) if summary_json else None

    if not dry_run and backup_dir is None:
        raise ValueError("backup_dir is required when dry_run=False")
    if not dry_run:
        validate_backup_dir(backup_dir, target_dir)

    summary = {key: 0 for key in SUMMARY_KEYS}
    summary["dry_run"] = dry_run
    summary["overwrite"] = overwrite
    summary["source_dir"] = str(source_dir)
    summary["target_dir"] = str(target_dir)
    summary["audit_jsonl"] = str(audit_jsonl)
    if backup_dir:
        summary["backup_dir"] = str(backup_dir)

    source_files = list(
        iter_source_files(
            source_dir,
            category=category,
            asset_list_file=asset_list_file,
            limit=limit,
        )
    )
    audit_jsonl.parent.mkdir(parents=True, exist_ok=True)

    with audit_jsonl.open("w", encoding="utf-8") as audit:
        for source_file in source_files:
            summary["source_files"] += 1
            record, counts = process_one(
                source_dir,
                target_dir,
                source_file,
                dry_run=dry_run,
                overwrite=overwrite,
                backup_dir=backup_dir,
            )
            add_counts(summary, counts)
            audit.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    if summary_json:
        summary_json.parent.mkdir(parents=True, exist_ok=True)
        summary_json.write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    return summary


def print_summary(summary: dict) -> None:
    print("=== GRScenes annotation sync summary ===")
    for key in SUMMARY_KEYS:
        print(f"{key}: {summary.get(key, 0)}")
    print(f"dry_run: {summary['dry_run']}")
    print(f"overwrite: {summary['overwrite']}")
    print(f"audit_jsonl: {summary['audit_jsonl']}")
    if "backup_dir" in summary:
        print(f"backup_dir: {summary['backup_dir']}")


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Sync Auto-Asset annotations into GRScenes metadata files"
    )
    parser.add_argument("--source-dir", required=True, help="Auto-Asset output root")
    parser.add_argument("--target-dir", required=True, help="GRScenes_assets root")
    parser.add_argument("--audit-jsonl", required=True, help="Audit JSONL output path")
    parser.add_argument("--summary-json", help="Optional summary JSON output path")
    parser.add_argument("--backup-dir", help="Backup root required with --apply")
    parser.add_argument("--apply", action="store_true", help="Write target files")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite non-empty target fields")
    parser.add_argument("--category", help="Only process one category")
    parser.add_argument("--asset-list-file", help="Process explicit category/asset_id list")
    parser.add_argument("--limit", type=int, help="Limit number of source files")
    args = parser.parse_args(argv)
    if args.apply and not args.backup_dir:
        parser.error("--backup-dir is required with --apply")
    return args


def main(argv=None) -> int:
    args = parse_args(argv)
    summary = sync_annotations(
        args.source_dir,
        args.target_dir,
        audit_jsonl=args.audit_jsonl,
        backup_dir=args.backup_dir,
        dry_run=not args.apply,
        overwrite=args.overwrite,
        category=args.category,
        asset_list_file=args.asset_list_file,
        limit=args.limit,
        summary_json=args.summary_json,
    )
    print_summary(summary)
    if summary["failed"] or summary["no_target"] or summary["source_raw_output"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
