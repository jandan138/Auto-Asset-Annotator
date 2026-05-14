# 配置文件详解

默认配置文件位于 `config/config.yaml`。`main.py` 会先加载这个文件，再用 CLI 参数覆盖其中的部分字段。

## 当前配置示例

```yaml
model:
  backend: "local_hf"
  name: "/cpfs/shared/simulation/zhuzihou/models/Qwen2.5-VL-7B-Instruct"
  api_base_url: null
  api_key_env: "NEWAPI_API_KEY"
  api_timeout_seconds: 120
  api_max_retries: 2
  device_map: "auto"
  dtype: "bfloat16"
  attn_implementation: "eager"
  temperature: 0.1
  max_new_tokens: 2048

data:
  input_dir: "./data"
  output_dir: "./output"
  views:
    front: ["front.png", "0.png"]
    left: ["left.png", "1.png"]
    back: ["back.png", "2.png"]
    right: ["right.png", "3.png"]
  use_thumbnails_dir: false
  thumbnails_dir_name: "thumbnails"

processing:
  batch_size: 1
  num_chunks: 1
  chunk_index: 0

prompts:
  default_type: "extract_object_attributes_prompt"
```

## `model` 段

`model.backend` 控制推理实现。目前有三种取值：

- `local_hf`：本地 Hugging Face/Qwen-VL 推理。
- `local_gemma4_multimodal`：本地 Gemma4 image-text 推理，使用独立 Gemma4 processor 链路。
- `openai_compatible`：远程 OpenAI-compatible Chat Completions 多模态推理。

checked-in 默认配置使用 `local_hf`，这样仓库在未改动配置时仍保持本地可运行。

如果要切换到 `openai_compatible` 示例路径，可把 `model` 段改成下面这样：

```yaml
model:
  backend: "openai_compatible"
  name: "gemini-2.5-flash-image"
  api_base_url: "https://your-openai-compatible-host"
  api_key_env: "NEWAPI_API_KEY"
  api_timeout_seconds: 120
  api_max_retries: 2
  device_map: "auto"
  dtype: "bfloat16"
  attn_implementation: "eager"
  temperature: 0.1
  max_new_tokens: 2048
```

这里的 `api_base_url` 必须替换成真实 host，并且环境中必须存在 `NEWAPI_API_KEY`；只配置其中一个都不能运行 API 后端。不要把真实 API key 写入 `config/config.yaml`。

如果要切换到 Gemma4 本地多模态路径，可把 `model` 段改成下面这样：

```yaml
model:
  backend: "local_gemma4_multimodal"
  name: "/cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8"
  api_base_url: null
  api_key_env: "NEWAPI_API_KEY"
  api_timeout_seconds: 120
  api_max_retries: 2
  device_map: "auto"
  dtype: "bfloat16"
  attn_implementation: "eager"
  temperature: 0.1
  max_new_tokens: 2048
```

Gemma4 会加载本地大模型。未明确做 live smoke/probe 时，不要用这个配置启动真实标注命令。

Gemma4 backend 需要支持 Gemma4 多模态类的 Transformers 版本；本仓库依赖下限是 `transformers>=5.5.0`。如果运行环境缺少这些类，backend 会在加载前报出当前安装的 Transformers 版本。

当前已验证的 Gemma4 smoke runtime 是：

```text
/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python
```

该环境来自 Genesis-LLM QLoRA 运行记录，包含 `transformers 5.8.0.dev0`、Unsloth、bitsandbytes 和 Torch `2.10.0+cu128`。仓库 `.venv_dlc` 中的 `transformers 5.2.0` 不足以完成 Gemma4 多模态图片输入；processor-only smoke 会缺少 `pixel_values` / `image_position_ids`。

### `model.name`

模型名称或本地模型路径。

- 在 `local_hf` 下，它是本地权重目录。
- 在 `local_gemma4_multimodal` 下，它是 Gemma4 base 模型 release 目录。
- 在 `openai_compatible` 下，它是远程模型名，例如 `gemini-2.5-flash-image`。

### `model.backend`

模型后端选择。checked-in 默认值是 `local_hf`；文档中的 `openai_compatible` 和 `local_gemma4_multimodal` 配置都是显式示例。

### `model.api_base_url`

`openai_compatible` 后端必填。请求会被发送到 `{api_base_url}/v1/chat/completions`。

### `model.api_key_env`

`openai_compatible` 后端必填。程序会从这个环境变量读取 Bearer token。

### `model.api_timeout_seconds`

API 请求超时时间，单位为秒。

### `model.api_max_retries`

API 请求最大重试次数。当前实现会对部分瞬时 HTTP/网络错误做轻量重试。

### `model.device_map`

传给本地模型加载逻辑的设备映射策略。当前默认值是 `"auto"`。

当 `model.backend` 为 `openai_compatible` 时，这个字段会被忽略。

### `model.dtype`

本地模型推理使用的数据类型。当前默认值是 `"bfloat16"`。

当 `model.backend` 为 `openai_compatible` 时，这个字段会被忽略。

### `model.attn_implementation`

本地模型注意力实现方式。checked-in `config/config.yaml` 当前使用 `"eager"`；代码级 dataclass fallback 仍然是 `"flash_attention_2"`。

当 `model.backend` 为 `openai_compatible` 时，这个字段会被忽略。

### `model.temperature`

生成温度。checked-in `config/config.yaml` 当前使用 `0.1`；代码级 dataclass fallback 仍然是 `0.8`。无论本地还是 API 后端，都会透传到对应的生成请求中。

### `model.max_new_tokens`

单次生成的最大 token 数。checked-in `config/config.yaml` 当前使用 `2048`；代码级 dataclass fallback 仍然是 `512`。API 后端会将它映射为 `max_tokens`。

### API 后端补充说明

`openai_compatible` 后端会把 `AnnotationPipeline` 生成的本地图像路径编码成 data URL，再按 OpenAI-compatible 消息格式发送给远程接口。除 `backend`、`name`、`api_base_url`、`api_key_env`、`api_timeout_seconds`、`api_max_retries`、`temperature`、`max_new_tokens` 外，其余 `model` 字段都应视为本地推理配置。

### Gemma4 后端补充说明

`local_gemma4_multimodal` 后端会把 `AnnotationPipeline` 生成的 `image_url` blocks 转换成 Hugging Face Gemma4 的 `image` blocks，并让 processor 负责 token/media 对齐。它不复用 `local_hf`，因为 `local_hf` 是 Qwen 风格视觉预处理路径。

Unsloth 4-bit Gemma4 checkpoint 需要先加载 Unsloth patch。当前 backend 会在发现路径名包含 `unsloth`、本地 `config.json` 含 `unsloth_fixed: true`，或 `quantization_config` 是 4-bit bitsandbytes 时自动导入 Unsloth，并把默认 `UNSLOTH_COMPILE_LOCATION` 放到当前工作树之外。手动 smoke 时仍建议显式设置：

```bash
export UNSLOTH_COMPILE_LOCATION=/cpfs/user/zhuzihou/tmp/auto_asset_annotator_smoke/<run_id>/cache/unsloth_compiled_cache
```

Gemma4 base 模型固定路径：

```text
/cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8
```

Genesis-LLM adapter 固定路径：

```text
/cpfs/user/zhuzihou/models/gemma4/adapters/genesis-llm-fullscale-v0-gpu2-seed42-epoch3
```

默认不要启用 Genesis adapter；它需要在 Gemma4 base 通过 live smoke 后再做 A/B 对比。

Gemma4 本地 smoke 的完整 runbook：`docs/usage/gemma4_local_smoke.md`。

## `data` 段

### `data.input_dir` 和 `data.output_dir`

默认输入目录和输出目录，可分别被 `--input_dir`、`--output_dir` 覆盖。

### `data.views`

视图名到文件名模式列表的映射。`utils/file.py` 会按这个顺序在每个资产目录中查找对应图片。

### `data.use_thumbnails_dir`

是否优先进入资产目录下的缩略图子目录查找图片。当前默认值为 `false`。

### `data.thumbnails_dir_name`

缩略图子目录名称，默认是 `"thumbnails"`。

## `processing` 段

- `num_chunks`: 将任务切成多少块。
- `chunk_index`: 当前进程处理哪一块，从 `0` 开始。

## `prompts` 段

### `prompts.default_type`

默认 prompt 类型。当前默认值是 `extract_object_attributes_prompt`。如果 CLI 传入 `--prompt_type`，会覆盖这里的设置。
