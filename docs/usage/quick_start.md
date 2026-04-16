# 快速开始

本页展示当前默认用法，适合首次确认安装、目录结构和输出位置是否正确。

当前仓库支持两种运行方式：

- `local_hf`：本地加载 Qwen-VL 权重。
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
