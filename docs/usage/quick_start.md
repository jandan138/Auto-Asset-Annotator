# 快速开始

本页展示当前默认用法，适合首次确认安装、目录结构和输出位置是否正确。

当前仓库支持三种运行方式：

- `local_hf`：本地加载 Qwen-VL 权重。
- `local_gemma4_multimodal`：本地加载 Gemma4 image-text 权重。
- `openai_compatible`：远程调用 OpenAI-compatible 多模态接口，配置示例使用 `gemini-2.5-flash-image`。

## 1. 准备输入目录

输入目录通常按 `类别/资产ID/图片文件` 组织，例如：

```text
test_data/
  chair/
    chair_0001/
      front.png
      left.png
      back.png
      right.png
```

## 2. 运行默认标注命令

默认配置文件是 `config/config.yaml`，默认 prompt 类型是 `extract_object_attributes_prompt`。最常见的启动方式是：

```bash
python -m auto_asset_annotator.main --input_dir ./test_data --output_dir ./test_output
```

如果不传 `--prompt_type`，程序会使用配置中的默认 prompt。

仓库 checked-in 的 `config/config.yaml` 默认使用 `local_hf`，所以上面的命令默认走本地模型。

如果你要改用 API 示例路径，必须同时准备真实的 API host 和环境变量：

```bash
export NEWAPI_API_KEY="<your-api-key>"
python -m auto_asset_annotator.main \
  --model_backend openai_compatible \
  --model_path gemini-2.5-flash-image \
  --api_base_url https://your-openai-compatible-host \
  --api_key_env NEWAPI_API_KEY \
  --input_dir ./test_data \
  --output_dir ./test_output
```

只导出 `NEWAPI_API_KEY` 而不设置真实 `api_base_url` 仍然不能运行 API 后端。

如果你要显式使用 API CLI 覆盖，可以这样写：

```bash
python -m auto_asset_annotator.main \
  --model_backend openai_compatible \
  --model_path gemini-2.5-flash-image \
  --api_base_url https://your-openai-compatible-host \
  --api_key_env NEWAPI_API_KEY \
  --input_dir ./test_data \
  --output_dir ./test_output
```

如果要切回本地推理，只需把 `model.backend` 改成 `local_hf`，并把 `model.name` 指向本地权重目录。`device_map`、`dtype`、`attn_implementation` 仅在本地后端生效，API 后端会忽略这些字段。

如果要做 Gemma4 本地多模态 probe，显式指定独立 backend 和固定 release 路径：

```bash
RUN_ROOT=/cpfs/user/zhuzihou/tmp/auto_asset_annotator_smoke/$(date -u +%Y%m%dT%H%M%SZ)_grscenes_basket_6c68230d_gemma4
DATA_ROOT=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets
mkdir -p "$RUN_ROOT/input" "$RUN_ROOT/output" "$RUN_ROOT/logs" "$RUN_ROOT/cache"
printf '%s\n' 'basket/6c68230d67112b1dfd2bd7fa9322c756' > "$RUN_ROOT/input/asset_list.txt"

HF_HUB_OFFLINE=1 \
TRANSFORMERS_OFFLINE=1 \
TOKENIZERS_PARALLELISM=false \
UNSLOTH_COMPILE_LOCATION="$RUN_ROOT/cache/unsloth_compiled_cache" \
PYTHONPATH=src \
/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python \
  -m auto_asset_annotator.main \
  --model_backend local_gemma4_multimodal \
  --model_path /cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8 \
  --asset_list_file "$RUN_ROOT/input/asset_list.txt" \
  --input_dir "$DATA_ROOT" \
  --output_dir "$RUN_ROOT/output"
```

这条命令会加载大模型，只有明确做 live smoke/probe 时才运行。已验证的 Gemma4 smoke runtime 是 `/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python`；仓库 `.venv_dlc` 中的 Transformers 版本不足以完成 Gemma4 多模态图片输入。完整命令、隔离输出目录、Unsloth cache 规范和真实输出示例见 `docs/usage/gemma4_local_smoke.md`。

## 3. 查看输出

完成后，程序会在输出目录下写入：

```text
test_output/
  chair/
    chair_0001_annotation.json
```

## 4. 输出说明

属性提取模式下，输出 JSON 不是模型直接返回的 JSON。实际流程是：

1. 模型返回带标题的 structured text。
2. `AnnotationPipeline` 在代码中解析 structured text。
3. `main.py` 将解析后的结果写入 JSON 文件。

示例：

```json
{
  "chair/chair_0001": {
    "category": "chair",
    "description": "A chair with ...",
    "material": "wooden frame, fabric seat",
    "dimensions": "0.5 * 0.5 * 0.9",
    "mass": "5.0",
    "placement": "OnFloor"
  }
}
```

如果解析失败，结果会保存 `raw_output`，后续可继续重试。

输出 JSON 的风格与仓库现有 `./output/...` 标注结果一致，但不等于 GRScenes 原始资产 metadata schema。字段类型、顶层 key 和回填建议见 `docs/usage/output_schema.md`。
