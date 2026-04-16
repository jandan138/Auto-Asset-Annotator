# 核心代码导读 (Core Code Walkthrough)

这份导读只讲当前仍在主线生效的代码路径。

## 1. `src/auto_asset_annotator/main.py`

这是总控入口。

### 配置覆盖

`main()` 先读 `config/config.yaml`，再用 CLI 覆盖：

- `--input_dir`
- `--output_dir`
- `--model_path`
- `--prompt_type`
- `--asset_list_file`
- `--num_chunks`
- `--chunk_index`

### 资产来源

资产列表有两条路：

- 传了 `--asset_list_file`：按文件逐行读取
- 没传：调用 `list_assets(cfg.data.input_dir)`

### 输出路径构建

```python
output_file = os.path.join(cfg.data.output_dir, f"{asset_name}_annotation.json")
os.makedirs(os.path.dirname(output_file), exist_ok=True)
```

如果 `asset_name` 是 `chair/abc123`，最终输出就会变成：

```text
{output_dir}/chair/abc123_annotation.json
```

### 重试逻辑

`main.py` 当前会重试三类情况：

- 输出文件中存在 `raw_output`
- 传了 `--retry_incomplete` 且物理属性字段有空值
- 传了 `--force`

## 2. `src/auto_asset_annotator/core/pipeline.py`

### `process_asset()`

这是主业务函数，顺序非常直：

1. 找图
2. 生成 prompt
3. 组装消息
4. 调模型
5. 解析结果

### 为什么说当前主线是“结构化文本解析”？

因为判断逻辑是：

```python
if "json" in prompt_type.lower() or "extract" in prompt_type.lower():
    result = self.parse_structured_text_enhanced(result_text)
```

也就是说，只要 prompt 名命中这个规则，流水线就会尝试把模型文本解析成字段字典，而不是做简单的 JSON 反序列化。

### 解析后处理

解析成功后还有两步很关键：

- 用输入目录相对路径的首段覆盖 `category`
- 对 `dimensions` 和 `mass` 做数值规范化

## 3. `src/auto_asset_annotator/core/model.py`

### 模型类选择

当前加载顺序是：

1. `Qwen2_5_VLForConditionalGeneration`
2. `AutoModelForCausalLM`
3. 如果模型名含 `Qwen3`，再尝试 `Qwen3VLMoeForConditionalGeneration`

这就是为什么文档里应该写“Qwen2.5-VL first”，而不是笼统地写成“通用任意多模态模型加载器”。

### 推理输入

`inference()` 会：

- 用 chat template 生成文本
- 用 `process_vision_info()` 提取图像输入
- 调 processor 得到 tensor
- 调 `generate()` 拿到输出 token
- 解码为文本

## 4. `src/auto_asset_annotator/utils/file.py`

### `list_assets()`

它会递归遍历目录，只要一个目录里有图片，就把它认作资产，并停止继续向下找。这能避免把资产内部的子目录误识别成新的资产。

### `get_asset_images()`

它先按 `config.data.views` 里定义的命名规则找图。如果一张命名视角都没找到，就回退到目录内所有图片的自然排序列表。

## 5. 一句话总结代码骨架

这个仓库当前最重要的骨架不是“模型怎么回答”，而是：

- 如何稳定找到资产图片
- 如何稳定把 prompt 和图片送进 Qwen
- 如何稳定把结构化文本解析成 JSON

读懂这三层，整个项目就读懂了大半。
