import os
import argparse
import time
import json

from natsort import natsorted
from tqdm import tqdm

from transformers import Qwen3VLMoeForConditionalGeneration, AutoProcessor
import torch

from qwen_utils import qwen_vlm_pipeline

os.environ["WORLD_SIZE"] = "0"


def split_list_into_chunks(object_list: list, num_chunks: int, chunk_index: int) -> list:
    """
    Split a list into chunks and return the specified chunk, jsut for submit jobs
    
    Args:
        object_list: The list to split
        num_chunks: Total number of chunks to split into
        chunk_index: Index of the chunk to return (0-indexed)
    
    Returns:
        The specified chunk of the list
    """
    total_objects = len(object_list)
    chunk_size = (total_objects + num_chunks - 1) // num_chunks  # Ceiling division
    start_idx = chunk_index * chunk_size
    end_idx = min((chunk_index + 1) * chunk_size, total_objects)
    
    print(f"[INFO] Processing chunk {chunk_index}/{num_chunks-1}: objects {start_idx} to {end_idx-1} ({end_idx - start_idx} objects)")
    
    return object_list[start_idx:end_idx]


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--params", type=int, default=30)
    parser.add_argument("--objects_dir", default='/shared/smartbot/caopeizhou/data/GRScenes-100/Asset_Library')
    parser.add_argument("--num_chunks", type=int, default=10, help="Total number of chunks to split into")
    parser.add_argument("--chunk_index", type=int, default=0, help="Index of chunk to process (0-indexed)")
    args = parser.parse_args()

    source_dir = args.objects_dir
    object_list = natsorted(os.listdir(source_dir))
    print(f"[INFO] Found {len(object_list)} objects in {source_dir}")
    
    # Split object_list into chunks and process based on chunk_index
    object_list = split_list_into_chunks(object_list, args.num_chunks, args.chunk_index)
    
    # init the model 
    parameters = args.params
    qwen_model_name = f"Qwen3-VL-{parameters}B-A3B-Instruct"   # New model
    vlm_model_path = f"/shared/smartbot/caopeizhou/models/Qwen/{qwen_model_name}"
    vlm_model = Qwen3VLMoeForConditionalGeneration.from_pretrained(
        vlm_model_path,
        dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",
        device_map="auto",
    )
    processor = AutoProcessor.from_pretrained(vlm_model_path, use_fast=True)

    for object_id in tqdm(object_list):
        object_path          = os.path.join(source_dir, object_id)
        thumbnails_dir       = os.path.join(object_path, "thumbnails")
        auto_annotation_dir  = os.path.join(object_path, "auto_annotation")
        attributes_path      = os.path.join(auto_annotation_dir, f"attributes_by_{qwen_model_name}.json")
        os.makedirs(auto_annotation_dir, exist_ok=True)
        attributes_results = {}
        
        is_annotation_finished = os.path.exists(attributes_path)
        has_thumbnails_dir = os.path.exists(thumbnails_dir)

        if not has_thumbnails_dir:
            print(f"[GRGenerator: GR100 Object Caption Qwen] Skipping {object_path} due to missing thumbnails dir.")
            continue
        
        if is_annotation_finished:
            print(f"[GRGenerator: GR100 Object Caption Qwen] Skipping {object_path} due to existing attributes.")
            continue
        else:
            print(f"[GRGenerator: GR100 Object Caption Qwen] Starting annotation {object_id}.")

            # Just for GR100, because the object_id is like "commercial-articulated-basket-02f563c8720e209efec34199dd999a53"
            object_pre_label_info = object_id.split('-')[:-1]    

            # Attribute Annotation
            start_time = time.time()
            attributes = qwen_vlm_pipeline([thumbnails_dir], vlm_model, processor, prompt_type="extract_object_attributes_prompt", object_additional_info=object_pre_label_info)
            end_time = time.time()
            print(f"[GRGenerator: Object Caption Qwen] Finished classifying object {object_id} by model {qwen_model_name} in {end_time-start_time:.3f}s")
            # Category result
            attributes_results[object_id] = attributes[0]

        with open(attributes_path, 'w') as f:
            json.dump(attributes_results, f, indent=4)
        print(f"[GRGenerator: Object Caption Qwen] Saved category result to {attributes_path}")



