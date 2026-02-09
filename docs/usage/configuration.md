# 配置文件详解

配置文件默认位于 `config/config.yaml`。通过修改此文件，您可以控制模型参数、数据路径和处理逻辑。

## 完整配置示例

```yaml
model:
  # HuggingFace 模型 ID 或本地绝对路径
  name: "Qwen/Qwen2.5-VL-7B-Instruct" 
  
  # 设备映射策略，"auto" 会自动利用所有可见 GPU
  device_map: "auto" 
  
  # 数据精度，推荐 bfloat16 以获得最佳性能和精度平衡
  dtype: "bfloat16" 
  
  # 注意力机制实现，推荐 flash_attention_2 (需安装 flash-attn)
  attn_implementation: "flash_attention_2"
  
  # 生成参数
  temperature: 0.8       # 采样温度，越高越随机
  max_new_tokens: 512    # 最大生成长度

data:
  input_dir: "./data"    # 默认输入目录 (可被 CLI 覆盖)
  output_dir: "./output" # 默认输出目录 (可被 CLI 覆盖)
  
  # 视图映射规则 (详见 data_preparation.md)
  views:
    front: ["front.png", "0.png"]
    left: ["left.png", "1.png"]
    back: ["back.png", "2.png"]
    right: ["right.png", "3.png"]
  
  # 是否搜索子目录
  use_thumbnails_dir: false
  thumbnails_dir_name: "thumbnails"

processing:
  batch_size: 1          # 批处理大小 (目前 Pipeline 主要支持单图处理，保留字段)
  num_chunks: 1          # 默认分块数 (用于分布式)
  chunk_index: 0         # 默认分块索引

prompts:
  # 默认使用的 Prompt 类型
  default_type: "extract_object_attributes_prompt"
```

## 关键字段说明

### `model.name`
*   如果你已经下载了模型权重，请填写**绝对路径**，例如 `/data/models/Qwen2.5-VL-7B-Instruct`。
*   如果填写 HuggingFace ID，首次运行会自动下载。

### `model.device_map`
*   `"auto"`: 自动分配层到 CPU/GPU。
*   `"cuda"`: 强制使用第一块 GPU。
*   `"cpu"`: 仅使用 CPU (极慢，仅供调试)。

### `prompts.default_type`
可选值请参考 `introduction/features.md` 中的列表。
