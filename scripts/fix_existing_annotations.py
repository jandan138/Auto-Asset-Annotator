#!/usr/bin/env python3
"""
Batch fix script for existing annotation files.
Fixes: category mismatches, units in dimensions/mass.
"""

import json
import os
import re
import argparse
from pathlib import Path
from tqdm import tqdm


def normalize_dimensions(value):
    """Strip units from dimensions."""
    if not value or value == "null":
        return None
    if '*' in value:
        parts = re.split(r'\s*\*\s*', value)
        clean_parts = []
        for part in parts:
            match = re.search(r'(\d+\.?\d*)', part)
            if match:
                clean_parts.append(match.group(1))
        return ' * '.join(clean_parts) if clean_parts else value
    match = re.search(r'(\d+\.?\d*)', value)
    return match.group(1) if match else value


def normalize_mass(value):
    """Strip units from mass."""
    if not value or value == "null":
        return None
    match = re.search(r'(\d+\.?\d*)', value)
    return match.group(1) if match else value


def fix_annotation_file(filepath, output_dir):
    """Fix a single annotation file. Returns True if modified."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False

    if not data or len(data) != 1:
        return False

    asset_key = list(data.keys())[0]
    record = data[asset_key]

    # Skip failed annotations
    if 'raw_output' in record:
        return False

    # Extract category from path
    rel_path = os.path.relpath(filepath, output_dir)
    category_from_path = rel_path.split(os.sep)[0]

    modified = False

    # Fix category
    if record.get('category') != category_from_path:
        record['category'] = category_from_path
        modified = True

    # Fix dimensions
    if record.get('dimensions'):
        new_dims = normalize_dimensions(record['dimensions'])
        if new_dims != record['dimensions']:
            record['dimensions'] = new_dims
            modified = True

    # Fix mass
    if record.get('mass'):
        new_mass = normalize_mass(record['mass'])
        if new_mass != record['mass']:
            record['mass'] = new_mass
            modified = True

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

    return modified


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", default="./output", help="Output directory")
    args = parser.parse_args()

    files = list(Path(args.output_dir).rglob("*_annotation.json"))

    fixed_count = 0
    for filepath in tqdm(files, desc="Fixing annotations"):
        if fix_annotation_file(str(filepath), args.output_dir):
            fixed_count += 1

    print(f"Fixed {fixed_count} files out of {len(files)}")


if __name__ == "__main__":
    main()
