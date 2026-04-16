# 配置文件详解

默认配置文件位于 `config/config.yaml`。`main.py` 会先加载这个文件，再用 CLI 参数覆盖其中的部分字段。

## 当前配置示例

```yaml
model:
  name: "/cpfs/shared/simulation/zhuzihou/models/Qwen2.5-VL-7B-Instruct"
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

### `model.name`

模型名称或本地模型路径。当前仓库默认值是本地 Qwen2.5-VL-7B-Instruct 权重目录。

### `model.device_map`

传给模型加载逻辑的设备映射策略。当前默认值是 `"auto"`。

### `model.dtype`

模型推理使用的数据类型。当前默认值是 `"bfloat16"`。

### `model.attn_implementation`

注意力实现方式。当前配置为 `"eager"`，配置文件中也保留了 `flash_attention_2` 的注释示例。

### `model.temperature`

生成温度。当前默认值为 `0.1`，偏向更稳定的输出。

### `model.max_new_tokens`

单次生成的最大 token 数。当前默认值为 `2048`。

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
