# 如何添加自定义 Prompt

如果现有的 Prompt 类型（如属性提取、分类）不能满足需求，你可以按照以下步骤添加新的 Prompt。

## 步骤 1: 定义 Prompt 字符串

打开 `src/auto_asset_annotator/core/prompt.py`。

在 `PromptFactory.compose_user_prompt` 方法中，添加一个新的 `elif` 分支。

```python
# src/auto_asset_annotator/core/prompt.py

SUPPORTED_PROMPT_TYPES = [
    # ... 现有类型 ...
    "my_new_custom_prompt",  # <--- 1. 在这里注册新类型名称
]

class PromptFactory:
    @staticmethod
    def compose_user_prompt(...):
        # ...
        
        elif prompt_type == "my_new_custom_prompt":  # <--- 2. 添加处理逻辑
            return (
                f"You are given {image_number} views of an object.\n"
                "Please describe its artistic style in one word (e.g., Minimalist, Baroque).\n"
                "Output ONLY the style word."
            )
```

## 步骤 2: 在配置中使用

修改 `config/config.yaml` 或使用 CLI 参数调用新类型：

```bash
python -m auto_asset_annotator.main --prompt_type my_new_custom_prompt ...
```

## 提示词编写技巧 (Prompt Engineering)

*   **明确输出格式**：如果需要程序化处理，务必强调 "Return JSON only" 或 "Output ONLY the integer"。
*   **多视图描述**：Qwen-VL 能够理解多张图片。在 Prompt 中明确告诉模型 "You are presented with N distinct views..." 有助于模型建立空间感。
*   **思维链 (CoT)**：对于复杂推理，可以要求模型 "Let's think step by step"，但注意这会增加输出长度，可能需要更复杂的后处理解析逻辑。
