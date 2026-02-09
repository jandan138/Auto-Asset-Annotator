# Prompt 工程机制 (Prompt Engineering Mechanics)

在 Auto-Asset-Annotator 中，Prompt 不仅仅是一段文字，而是包含逻辑、约束和多模态输入的复杂结构。本文档解析 `PromptFactory` 背后的工程机制。

## 1. 结构化输出的艺术 (Structured Output)

为了让大模型稳定输出 JSON，我们在 Prompt 中应用了 **CoT (Chain of Thought)** 的变体——**“约束链 (Chain of Constraints)”**。

### 核心 Prompt 分析 (`extract_object_attributes_prompt`)

```python
attribute_query = (
    "Analyze the provided image and extract the following structured information. "
    "You MUST respond in strict JSON format with ALL fields required. Do not omit any field.\n\n"
    "Required JSON structure:\n"
    "{\n"
    '  "category": "object type...",\n'
    '  "description": "comprehensive description...",\n'
    '  "material": "describe all materials...",\n'
    # ...
    "}\n\n"
    "Important: \n"
    "1. Return ONLY valid JSON, no additional text\n"
    "2. ALL fields are mandatory\n"
    "5. Ensure proper JSON syntax with double quotes"
)
```

**设计要点**:
1.  **明确的角色设定 (Role Definition)**: 虽然未显式写出 `You are an expert...`，但通过指令式语言确立了任务边界。
2.  **Schema Injection (模式注入)**: 直接在 Prompt 中给出 JSON 的模板。这是最有效的让模型遵循格式的方法。
3.  **负面约束 (Negative Constraints)**: 明确指出 `"no additional text"`, `"Do not omit"`。
4.  **Few-Shot vs Zero-Shot**: 目前主要使用 **Zero-Shot (零样本)**，即直接给出指令而不给示例。这是因为 Qwen-VL 在指令遵循方面已经非常强大，且每个资产的差异巨大，固定的样本可能会引入偏见。

## 2. 多模态 Prompt 构建

Prompt 不仅包含文本，还包含图像序列。

```python
def _prepare_messages(self, user_prompt: str, image_paths: List[str]):
    content = []
    content.append({"type": "text", "text": user_prompt})
    
    for img_path in image_paths:
        content.append({"type": "image_url", "image": img_path})
        
    return [{"role": "user", "content": content}]
```

**机制**:
*   **多图输入**: 系统将所有视角的图片（Front, Left, Back...）作为一个列表传入。
*   **上下文融合**: 模型会自动融合这些图片的信息。例如，如果正视图看不清材质，模型会参考侧视图或特写图。
*   **顺序无关性**: 虽然我们按顺序传入，但 Prompt 中并未强调顺序的重要性（除非是 `find_canonical_front_view` 任务），模型主要关注整体特征。

## 3. 如何扩展新的 Prompt 类型

如果您需要增加新的标注任务（例如：检测物体是否有破损），可以按以下步骤扩展：

1.  **修改 `src/auto_asset_annotator/core/prompt.py`**:
    *   在 `SUPPORTED_PROMPT_TYPES` 列表中添加新类型名称。
    *   在 `compose_user_prompt` 方法中添加对应的 `elif` 分支。

2.  **编写 Prompt 模板**:
    ```python
    elif prompt_type == "detect_damage_prompt":
        return (
            "Analyze these images for any signs of physical damage.\n"
            "Output JSON: {\"has_damage\": boolean, \"damage_details\": string}"
        )
    ```

3.  **配置调用**:
    *   在运行命令时指定 `--prompt_type detect_damage_prompt`，或者修改 `config.yaml`。

## 4. 常见问题与调试

*   **JSON 解析失败**:
    *   **现象**: 日志出现 `[WARN] Failed to parse JSON`。
    *   **原因**: 模型可能输出了 `Here is the JSON:` 前缀，或者 JSON 语法错误（如末尾多余逗号）。
    *   **对策**: 
        *   优化 Prompt 中的“负面约束”。
        *   在 `pipeline.py` 中增强正则清洗逻辑。
        *   调整 `temperature` 参数（降低温度可提高格式稳定性）。

*   **幻觉 (Hallucination)**:
    *   **现象**: 描述了图片中不存在的细节（如“木质纹理”实际上是“塑料仿木”）。
    *   **原因**: 图片分辨率不足或模型过度联想。
    *   **对策**: 增加高分辨率图片；在 Prompt 中强调 `"describe only observable details"`。
