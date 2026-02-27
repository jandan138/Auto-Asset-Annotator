import os
import json
import argparse
from tqdm import tqdm

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--save_list", default="failed_assets.txt")
    args = parser.parse_args()

    failed_assets = []
    
    print(f"Scanning {args.output_dir}...")
    
    for root, dirs, files in os.walk(args.output_dir):
        for file in files:
            if file.endswith("_annotation.json"):
                full_path = os.path.join(root, file)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        # Check failure criteria: has "raw_output" inside
                        if isinstance(data, dict):
                            # Usually data is { "asset_id": { ... } }
                            first_val = list(data.values())[0]
                            if isinstance(first_val, dict) and "raw_output" in first_val:
                                # Construct relative asset path from filename or json key
                                # Asset ID is usually the key, e.g. "basket/123"
                                asset_id = list(data.keys())[0]
                                failed_assets.append(asset_id)
                except Exception:
                    # Corrupted file also counts as failed
                    # Try to deduce asset id from path relative to output_dir
                    rel_dir = os.path.relpath(root, args.output_dir)
                    asset_name = file.replace("_annotation.json", "")
                    if rel_dir == ".":
                        failed_assets.append(asset_name)
                    else:
                        failed_assets.append(os.path.join(rel_dir, asset_name))

    with open(args.save_list, "w") as f:
        for asset in failed_assets:
            f.write(f"{asset}\n")
            
    print(f"Found {len(failed_assets)} failed assets.")
    print(f"List saved to {args.save_list}")
    
    # Preview
    print("\nPreview of failed assets:")
    for a in failed_assets[:5]:
        print(f" - {a}")

if __name__ == "__main__":
    main()
