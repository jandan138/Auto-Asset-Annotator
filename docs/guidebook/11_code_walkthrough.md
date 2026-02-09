# 核心代码导读 (Core Code Walkthrough)

本文档将带您深入阅读 Auto-Asset-Annotator 的核心代码文件，解析关键函数的实现细节。建议配合 IDE 阅读源码。

## 1. `src/auto_asset_annotator/main.py` - 程序入口

这是整个程序的指挥塔。

### 关键逻辑：分块处理 (Chunking)

```python
# List Assets
all_assets = list_assets(cfg.data.input_dir)

# Chunking logic
total_assets = len(all_assets)
if cfg.processing.num_chunks > 1:
    # 计算每个分块的大小（向上取整）
    chunk_size = (total_assets + cfg.processing.num_chunks - 1) // cfg.processing.num_chunks
    # 计算当前分块的切片范围
    start_idx = cfg.processing.chunk_index * chunk_size
    end_idx = min((cfg.processing.chunk_index + 1) * chunk_size, total_assets)
    # 获取子集
    assets_to_process = all_assets[start_idx:end_idx]
```
*   **解析**: 这段代码确保了当您启动多个进程（指定不同的 `chunk_index`）时，它们不会重复处理同一个资产。

### 关键逻辑：输出路径构建

```python
output_file = os.path.join(cfg.data.output_dir, f"{asset_name}_annotation.json")
# Ensure subdirectories exist
os.makedirs(os.path.dirname(output_file), exist_ok=True)
```
*   **解析**: `asset_name` 实际上是相对路径（如 `basket/asset_123`）。这里巧妙地利用 `os.path.join` 将相对路径拼接到输出根目录，从而自动保持了目录结构。

## 2. `src/auto_asset_annotator/core/pipeline.py` - 流水线

### 关键方法：`process_asset`

```python
def process_asset(self, asset_path: str, prompt_type: str = None) -> Dict[str, Any]:
    # 1. 查找图片
    images_map = get_asset_images(asset_path, self.config.data)
    image_paths = list(images_map.values())
    
    # 2. 组装 Prompt
    user_prompt = PromptFactory.compose_user_prompt(...)
    
    # 3. 构造消息
    messages = self._prepare_messages(user_prompt, image_paths)
    
    # 4. 推理
    result_text = self.engine.inference(messages)
    
    # 5. JSON 清洗
    if "json" in prompt_type:
        clean_text = result_text.strip()
        # 去除 markdown 代码块标记
        if clean_text.startswith("```json"): clean_text = clean_text[7:]
        if clean_text.endswith("```"): clean_text = clean_text[:-3]
        result = json.loads(clean_text)
```
*   **解析**: 
    *   步骤 1 使用配置中的规则（文件名匹配）找到所有图片。
    *   步骤 5 是至关重要的**容错层**。大模型经常会在 JSON 外面包裹 Markdown 标记，必须手动去除才能被 `json.loads` 解析。

## 3. `src/auto_asset_annotator/core/model.py` - 模型交互

### 关键方法：`__init__` (模型加载)

```python
try:
     from transformers import Qwen2_5_VLForConditionalGeneration
     model_class = Qwen2_5_VLForConditionalGeneration
except ImportError:
     from transformers import AutoModelForCausalLM
     model_class = AutoModelForCausalLM
```
*   **解析**: 这里展示了**兼容性设计**。它优先尝试加载特定的高性能模型类，如果环境中没有（或版本不对），则回退到通用的 `AutoModel`。这保证了代码能在不同版本的 `transformers` 库中运行。

### 关键方法：`inference`

```python
# 视觉信息预处理
image_inputs, video_inputs = process_vision_info(inputs_messages)

# 调用 Processor
inputs = self.processor(
    text=[text],
    images=image_inputs,
    ...
)
```
*   **解析**: `process_vision_info` 是 `qwen_vl_utils` 提供的工具，它能自动识别输入消息中的本地路径、URL 或 Base64 图片，并将其转换为模型需要的 Tensor 格式。

## 4. `src/auto_asset_annotator/utils/file.py` - 文件操作

### 关键方法：`list_assets`

```python
def list_assets(input_dir: str) -> List[str]:
    # 递归遍历所有子目录
    for root, dirs, files in os.walk(input_dir):
        # 只要目录下有图片，就视为一个资产
        has_images = any(f.lower().endswith(...) for f in files)
        if has_images:
            # 返回相对路径
            rel_path = os.path.relpath(root, input_dir)
            assets.append(rel_path)
            # 停止向下递归（假设资产是叶子节点）
            dirs[:] = []
```
*   **解析**: 这是支持嵌套目录的核心。通过 `os.walk` 和 `dirs[:] = []`，我们实现了“找到包含图片的文件夹就停止深入”的逻辑，防止将资产内部的 `thumbnails` 文件夹误判为另一个资产。
