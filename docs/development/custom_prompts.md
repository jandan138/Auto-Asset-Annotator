# 如何添加自定义 Prompt

当前 prompt 注册表在 `src/auto_asset_annotator/core/prompt.py`。

## 当前已注册的 `SUPPORTED_PROMPT_TYPES`

```python
[
    "find_canonical_front_view_prompt",
    "is_symmetric_object_prompt",
    "classify_object_category_prompt",
    "classify_object_category_with_background_prompt",
    "describe_object_prompt_MMScan",
    "describe_object_with_background_prompt",
    "polish_description_prompt_MMScan",
    "extract_object_attributes_prompt",
    "object_cognition_QA_with_background_prompt",
]
```

注意：注册表中的名字不等于所有路径都拥有同等成熟度。文档应以 `PromptFactory.compose_user_prompt()` 的现有实现为准。

更具体地说，`SUPPORTED_PROMPT_TYPES` 里有些名字属于注册表项、背景类特殊路径或只部分实现的分支。它们未必都适合作为“直接传 `--prompt_type <name>` 给当前主线 `main.py` 就能稳定跑通”的同等级入口。

当前通过主线 pipeline 直接使用时，最可靠的还是那些已经被 `PromptFactory.compose_user_prompt()` 明确实现、并且返回格式与 `AnnotationPipeline` 当前调用方式匹配的 prompt 类型。

## 添加新 Prompt 的步骤

### 1. 注册名字

先把类型名加入 `SUPPORTED_PROMPT_TYPES`。

### 2. 实现模板

在 `PromptFactory.compose_user_prompt()` 中增加对应的 `elif` 分支，返回 prompt 字符串；少数背景类任务也可以返回字符串列表，但要确保调用链真的支持这种格式。

示例：

```python
SUPPORTED_PROMPT_TYPES = [
    # ... existing prompt types ...
    "my_new_custom_prompt",
]

elif prompt_type == "my_new_custom_prompt":
    return (
        f"You are given {image_number} views of an object.\n"
        "Describe its dominant style in one short phrase.\n"
        "Output only the phrase."
    )
```

### 3. 通过配置或 CLI 使用

```bash
python -m auto_asset_annotator.main --prompt_type my_new_custom_prompt \
    --input_dir /path/to/assets --output_dir /path/to/results
```

## 解析行为规则

`AnnotationPipeline.process_asset()` 里有一个很重要的命名约定：

- **prompt 名称里包含 `extract` 或 `json`**
- 就会触发 `parse_structured_text_enhanced()` 解析流程

这意味着：

- `extract_object_attributes_prompt` 会被当作结构化输出任务
- 任何你新加的 `extract_*` 或 `*_json_*` 风格命名 prompt，也会自动进入解析分支

如果你的新 prompt 只是自由文本描述或分类结果，就不要随意把名字命名成 `extract` / `json`，否则流水线会尝试解析它。

## 当前主线提示词风格

当前默认 prompt `extract_object_attributes_prompt` 并不要求模型直接输出 JSON。它要求模型输出带明确字段头的 **structured text**，例如：

- `Category:`
- `Description:`
- `Material:`
- `Dimensions:`
- `Mass:`
- `Placement:`

随后由流水线解析并写成 JSON。这是当前最稳定的主线模式。

## 编写建议

- 想要分类结果时，要求输出单个词或短语
- 想要结构化字段时，优先要求固定表头文本，而不是直接信任模型生成 JSON
- 写新 prompt 时先想清楚是否需要进入解析分支
- 如果新增字段，记得同步评估 `parse_structured_text_enhanced()` 及其底层解析逻辑是否也要扩展
