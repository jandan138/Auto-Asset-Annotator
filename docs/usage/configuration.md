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

`model.backend` 控制推理实现。目前有两种取值：

- `local_hf`：本地 Hugging Face/Qwen-VL 推理。
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

### `model.name`

模型名称或本地模型路径。

- 在 `local_hf` 下，它是本地权重目录。
- 在 `openai_compatible` 下，它是远程模型名，例如 `gemini-2.5-flash-image`。

### `model.backend`

模型后端选择。checked-in 默认值是 `local_hf`；文档中的 `openai_compatible` 配置是显式 API 示例。

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

本地模型注意力实现方式。当前配置为 `"eager"`，配置文件中也保留了 `flash_attention_2` 的注释示例。

当 `model.backend` 为 `openai_compatible` 时，这个字段会被忽略。

### `model.temperature`

生成温度。无论本地还是 API 后端，都会透传到对应的生成请求中。

### `model.max_new_tokens`

单次生成的最大 token 数。API 后端会将它映射为 `max_tokens`。

### API 后端补充说明

`openai_compatible` 后端会把 `AnnotationPipeline` 生成的本地图像路径编码成 data URL，再按 OpenAI-compatible 消息格式发送给远程接口。除 `backend`、`name`、`api_base_url`、`api_key_env`、`api_timeout_seconds`、`api_max_retries`、`temperature`、`max_new_tokens` 外，其余 `model` 字段都应视为本地推理配置。

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
