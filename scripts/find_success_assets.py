import argparse
import os
import glob
import json
from tqdm import tqdm

def main():
    parser = argparse.ArgumentParser(description="Find assets that were successfully processed.")
    parser.add_argument("--output_dir", required=True, help="Directory containing annotation JSONs")
    parser.add_argument("--save_list", default="success_assets.txt", help="File to save the list of success asset IDs")
    args = parser.parse_args()

    # Find all JSON files recursively
    json_files = glob.glob(os.path.join(args.output_dir, "**/*_annotation.json"), recursive=True)
    
    success_assets = []
    
    print(f"Scanning {args.output_dir}...")
    for json_file in tqdm(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Asset ID is the key in the JSON
            # e.g. "bowl/123..."
            if not data:
                continue
                
            asset_id = list(data.keys())[0]
            content = data[asset_id]
            
            # Check for success: NO "raw_output" field
            if "raw_output" not in content:
                success_assets.append(asset_id)
                
        except Exception as e:
            # If JSON is invalid, it's definitely not a success
            pass

    print(f"Found {len(success_assets)} success assets.")
    
    # Save list
    if args.save_list:
        with open(args.save_list, 'w') as f:
            for asset in success_assets:
                f.write(f"{asset}\n")
        print(f"List saved to {args.save_list}")
        
    # Preview
    if success_assets:
        print("\nPreview of success assets:")
        for asset in success_assets[:5]:
            print(f" - {asset}")

if __name__ == "__main__":
    main()
