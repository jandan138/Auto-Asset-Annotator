import os
import json
import re
import argparse
from typing import Dict, Any, Optional

def extract_json_from_text(text: str) -> Optional[Dict[str, Any]]:
    """
    Attempt to extract and parse JSON from raw text using regex and heuristics.
    """
    if not text:
        return None
        
    # 1. Basic Cleanup: Remove Markdown code blocks
    text = re.sub(r'```json\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'```\s*', '', text)
    
    # 2. Try to find the outermost JSON object or array
    # Look for { ... } or [ ... ]
    # We use a stack-based approach or regex to find balanced braces if simple search fails,
    # but for now let's try regex for the largest block.
    
    # Heuristic 1: Look for standard JSON object
    try:
        # Try finding the first '{' and the last '}'
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1 and end > start:
            candidate = text[start:end+1]
            return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # Heuristic 2: Look for JSON array (sometimes model outputs list of dicts)
    try:
        start = text.find('[')
        end = text.rfind(']')
        if start != -1 and end != -1 and end > start:
            candidate = text[start:end+1]
            data = json.loads(candidate)
            if isinstance(data, list) and len(data) > 0:
                # If it's a list, usually we want the first item for this task
                return data[0]
            return data
    except json.JSONDecodeError:
        pass

    # Heuristic 3: Fix common syntax errors (trailing commas)
    # This is a bit risky but useful.
    try:
        # Remove trailing commas before closing braces
        candidate = re.sub(r',\s*([\]}])', r'\1', text[text.find('{'):text.rfind('}')+1])
        return json.loads(candidate)
    except (json.JSONDecodeError, IndexError):
        pass
        
    # Heuristic 4: Merge multiple JSON blocks if present (Model hallucination often splits output)
    # Example: ```json {part1} ``` ... ```json {part2} ```
    # This is complex, but we can try to find all {...} blocks and merge them.
    try:
        matches = re.findall(r'\{[^{}]*\}', text) 
        # Note: simple regex won't handle nested dicts well. 
        # But if the model outputs flat fragments, this might help.
        # Let's try a safer approach: find all valid JSON chunks.
        merged_data = {}
        
        # Simple parser for multiple blocks
        cursor = 0
        while cursor < len(text):
            start = text.find('{', cursor)
            if start == -1: break
            
            # Try to find a matching closing brace by balancing
            balance = 0
            for i in range(start, len(text)):
                if text[i] == '{': balance += 1
                elif text[i] == '}': balance -= 1
                
                if balance == 0:
                    # Found a block
                    chunk = text[start:i+1]
                    try:
                        chunk_data = json.loads(chunk)
                        if isinstance(chunk_data, dict):
                            merged_data.update(chunk_data)
                    except:
                        pass
                    cursor = i + 1
                    break
            else:
                # No closing brace found
                break
                
        if merged_data:
            return merged_data
            
    except Exception:
        pass

    return None

def fix_file(file_path: str, dry_run: bool = False, overwrite: bool = False):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print(f"[ERROR] Could not read file: {file_path}")
        return

    # Check if it's a "failed" file (has top-level key matching asset ID, and value has 'raw_output')
    # Structure: { "asset_id": { "raw_output": "..." } }
    
    changed = False
    new_data = {}
    
    for asset_id, content in data.items():
        if isinstance(content, dict) and "raw_output" in content and len(content) == 1:
            print(f"[INFO] Attempting to fix {asset_id}...")
            raw_text = content["raw_output"]
            
            extracted = extract_json_from_text(raw_text)
            
            if extracted:
                print(f"  -> Success! Extracted keys: {list(extracted.keys())}")
                new_data[asset_id] = extracted
                changed = True
            else:
                print(f"  -> Failed to extract JSON from raw text.")
                new_data[asset_id] = content # Keep original
        else:
            new_data[asset_id] = content

    if changed:
        # Save logic
        if overwrite:
            save_path = file_path
        else:
            dir_name = os.path.dirname(file_path)
            base_name = os.path.basename(file_path)
            name, ext = os.path.splitext(base_name)
            save_path = os.path.join(dir_name, f"{name}_fixed{ext}")
        
        if not dry_run:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(new_data, f, indent=4)
            print(f"[SAVE] Saved fixed version to: {save_path}")
        else:
            print(f"[DRY-RUN] Would save to: {save_path}")

def main():
    parser = argparse.ArgumentParser(description="Fix broken JSON outputs in Auto-Asset-Annotator results")
    parser.add_argument("--dir", required=True, help="Directory containing annotation JSONs (recursive search)")
    parser.add_argument("--dry-run", action="store_true", help="Don't write files, just show what would happen")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite original files if fix succeeds")
    args = parser.parse_args()
    
    print(f"Scanning {args.dir} for broken JSON files...")
    
    count = 0
    for root, dirs, files in os.walk(args.dir):
        for file in files:
            if file.endswith("_annotation.json") and not file.endswith("_fixed.json"):
                full_path = os.path.join(root, file)
                
                # Peek inside to see if it needs fixing (has raw_output)
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        # Read first few lines or full file (files are small)
                        content = f.read()
                        if '"raw_output"' in content:
                            fix_file(full_path, args.dry_run, args.overwrite)
                            count += 1
                except:
                    continue
                    
    print(f"\nDone. Processed {count} candidate files.")

if __name__ == "__main__":
    main()
