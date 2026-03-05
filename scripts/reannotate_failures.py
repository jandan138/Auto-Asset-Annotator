#!/usr/bin/env python3
"""
Re-annotate failed assets.

Usage:
    # Just analyze and report (no VLM)
    python scripts/reannotate_failures.py --output_dir ./output --analyze-only

    # Generate list for re-annotation
    python scripts/reannotate_failures.py --output_dir ./output --save_list failed_assets.txt
"""

import json
import os
import re
import argparse
from collections import defaultdict
from pathlib import Path
from tqdm import tqdm


def is_image_only_failure(text: str) -> bool:
    """Check if output is just '**Image' with whitespace."""
    if not text:
        return False
    # Pattern: optional whitespace, **Image, optional whitespace, end
    return bool(re.match(r'^\s*\*\*Image\s*$', text.strip()))


def is_multi_object_format(text: str) -> bool:
    """Detect multi-object output format."""
    if not text:
        return False
    return bool(re.search(r'(?:^|\n)[\*#\-]*\s*Object\s+\d+', text, re.IGNORECASE))


def is_truncated(text: str) -> bool:
    """Detect truncated output."""
    if not text:
        return False
    text = text.rstrip()
    return text.endswith(('...', ':', ' -', 'Object', 'Category'))


def categorize_failure(raw_output: str) -> str:
    """Categorize failure type."""
    if is_image_only_failure(raw_output):
        return "image_only"
    elif is_truncated(raw_output):
        return "truncated"
    elif is_multi_object_format(raw_output):
        return "multi_object"
    else:
        return "other"


def load_failed_assets(output_dir: str):
    """Load all failed annotations with categorization."""
    failed = []

    json_files = list(Path(output_dir).rglob("*_annotation.json"))

    for filepath in tqdm(json_files, desc="Scanning for failures"):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not data or len(data) != 1:
                continue

            asset_key = list(data.keys())[0]
            record = data[asset_key]

            if 'raw_output' not in record:
                continue

            raw = record['raw_output']
            failure_type = categorize_failure(raw)

            # Get relative path for asset ID
            rel_path = os.path.relpath(filepath, output_dir)
            category = rel_path.split(os.sep)[0]

            failed.append({
                'filepath': str(filepath),
                'asset_key': asset_key,
                'category': category,
                'failure_type': failure_type,
                'raw_sample': raw[:200] if len(raw) > 200 else raw
            })

        except Exception as e:
            print(f"Error reading {filepath}: {e}")

    return failed


def main():
    parser = argparse.ArgumentParser(
        description="Analyze and re-annotate failed assets"
    )
    parser.add_argument(
        '--output_dir',
        required=True,
        help='Directory containing annotation outputs'
    )
    parser.add_argument(
        '--analyze-only',
        action='store_true',
        help='Only analyze failures, do not re-annotate'
    )
    parser.add_argument(
        '--save_list',
        help='Save list of failed assets to file'
    )
    parser.add_argument(
        '--filter_type',
        choices=['image_only', 'multi_object', 'truncated', 'other'],
        help='Only process specific failure type'
    )

    args = parser.parse_args()

    # Load failed assets
    print(f"Scanning {args.output_dir} for failed annotations...")
    failed = load_failed_assets(args.output_dir)

    if not failed:
        print("No failed annotations found!")
        return

    # Categorize
    by_type = defaultdict(list)
    by_category = defaultdict(list)

    for item in failed:
        by_type[item['failure_type']].append(item)
        by_category[item['category']].append(item)

    # Print summary
    print(f"\n{'='*60}")
    print(f"FAILED ANNOTATION ANALYSIS")
    print(f"{'='*60}")
    print(f"Total failed: {len(failed)}")

    print(f"\nBy Failure Type:")
    for ft in ['image_only', 'multi_object', 'truncated', 'other']:
        count = len(by_type[ft])
        pct = 100 * count / len(failed)
        print(f"  {ft:15s}: {count:4d} ({pct:5.1f}%)")

    print(f"\nTop 10 Categories by Failure Count:")
    sorted_cats = sorted(by_category.items(), key=lambda x: -len(x[1]))[:10]
    for cat, items in sorted_cats:
        print(f"  {cat:20s}: {len(items):3d}")

    # Show samples
    print(f"\n{'='*60}")
    print(f"SAMPLES BY TYPE")
    print(f"{'='*60}")

    for ft in ['image_only', 'multi_object', 'truncated', 'other']:
        items = by_type[ft]
        if not items:
            continue
        print(f"\n--- {ft.upper()} ({len(items)} files) ---")
        for item in items[:2]:  # Show 2 samples
            print(f"\nAsset: {item['asset_key']}")
            print(f"Raw output sample: {item['raw_sample'][:150]}...")

    # Save list if requested
    if args.save_list:
        with open(args.save_list, 'w') as f:
            for item in failed:
                if args.filter_type and item['failure_type'] != args.filter_type:
                    continue
                f.write(f"{item['asset_key']}\n")
        print(f"\nSaved {len(failed)} assets to {args.save_list}")

    # Analyze-only exit
    if args.analyze_only:
        print(f"\nAnalysis complete. Use --save_list to generate retry list.")
        return

    # Note about VLM re-annotation
    print(f"\n{'='*60}")
    print(f"RE-ANNOTATION NOT IMPLEMENTED")
    print(f"{'='*60}")
    print(f"VLM re-annotation requires loading the model.")
    print(f"To re-annotate, use the saved list with the main pipeline:")
    print(f"  python -m auto_asset_annotator.main \\")
    print(f"      --asset_list_file {args.save_list or 'failed_assets.txt'} \\")
    print(f"      --input_dir /path/to/input \\")
    print(f"      --output_dir ./output")


if __name__ == "__main__":
    main()
