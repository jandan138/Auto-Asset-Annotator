# 如何适配新的 VLM 模型

目前项目深度集成了 Qwen-VL 系列，但架构上支持扩展到其他 HuggingFace 兼容的多模态模型（如 LLaVA, Yi-VL 等）。

## 修改 `ModelEngine`

主要修改点在 `src/auto_asset_annotator/core/model.py`。

你需要创建一个新的 Engine 类，或者修改现有的 `ModelEngine` 以适配不同模型的输入格式。

### 关键适配点

1.  **加载逻辑 (`__init__`)**:
    不同模型可能需要不同的 `AutoModel` 类。例如 Qwen 使用 `Qwen2_5_VLForConditionalGeneration`。

2.  **输入处理 (`process_vision_info`)**:
    `qwen_vl_utils.process_vision_info` 是 Qwen 专用的。其他模型通常只需要简单的 `processor(images=..., text=...)`。

### 示例：适配通用 AutoModel

```python
# 伪代码示例
class GenericModelEngine:
    def __init__(self, config):
        self.model = AutoModelForVision2Seq.from_pretrained(config.name, ...)
        self.processor = AutoProcessor.from_pretrained(config.name)

    def inference(self, inputs_messages):
        # 1. 提取图像和文本
        images = [load_image(msg['image']) for msg in inputs_messages[0]['content'] if 'image' in msg]
        prompt = inputs_messages[0]['content'][0]['text']
        
        # 2. 构造输入
        inputs = self.processor(text=prompt, images=images, return_tensors="pt")
        
        # 3. 生成
        out = self.model.generate(**inputs)
        return self.processor.decode(out[0])
```

完成修改后，在 `main.py` 中根据配置实例化对应的 Engine 即可。
