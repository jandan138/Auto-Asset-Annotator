# 功能特性详解

本文档概述当前代码实际支持的功能范围，重点以 `src/auto_asset_annotator/core/prompt.py` 中的 `SUPPORTED_PROMPT_TYPES` 为准。

## 支持的 Prompt Types

当前 `SUPPORTED_PROMPT_TYPES` 中列出以下 9 种 prompt 类型。这里的列表表示这些名字已在 prompt 注册表中出现，但不代表每一项都已经具备同等成熟度的端到端文档化使用路径。

- `find_canonical_front_view_prompt`
- `is_symmetric_object_prompt`
- `classify_object_category_prompt`
- `classify_object_category_with_background_prompt`
- `describe_object_prompt_MMScan`
- `describe_object_with_background_prompt`
- `polish_description_prompt_MMScan`
- `extract_object_attributes_prompt`
- `object_cognition_QA_with_background_prompt`

## 属性提取

### `extract_object_attributes_prompt`

这是默认的标注模式。该模式下，模型会返回带标题的 structured text，随后由流水线解析成 JSON，而不是要求模型直接生成严格 JSON。

解析后的字段包括：

- `category`: 类别名。最终值由资产目录路径的一级分类目录覆盖写入。
- `description`: 3-4 句的客观外观与功能描述。
- `material`: 材质与部位对应说明。
- `dimensions`: 长 * 宽 * 高，流水线会做格式归一化。
- `mass`: 质量数值，流水线会做格式归一化。
- `placement`: 可能的放置位置，如 `OnFloor`、`OnTable`、`OnObject`。

如果 structured text 无法被解析，输出会退化为包含 `raw_output` 的 JSON 文件，方便后续重试。

## 主要可用的任务类型

### `classify_object_category_prompt`

输出单一类别名称，适合快速构建资产类别标签。

### `describe_object_prompt_MMScan`

输出 3-5 句详细描述，强调可观察的外观、材质、比例、状态和用途。

### `find_canonical_front_view_prompt`

从多视图图像中选出标准正视图索引。

### `is_symmetric_object_prompt`

判断资产是否近似旋转对称，输出 `0` 或 `1`。

## 注册表已列出但不应视为当前主要端到端能力的路径

以下 prompt 名称仍然出现在 `SUPPORTED_PROMPT_TYPES` 中，因此文档需要保留覆盖；但基于当前 `PromptFactory.compose_user_prompt()` 的实现状态，它们不应被表述为和主路径同等成熟、可直接按当前主流程使用的功能。

### `classify_object_category_with_background_prompt`

当前代码为它保留了专门分支，并返回多段 prompt 输入，用于带背景和目标框的分类场景。但这条路径依赖不同于主流程的输入组织方式，文档中不应把它表述为当前默认或主要的端到端运行路径。

### `describe_object_with_background_prompt`

当前仅在注册表中列名；本页只将其视为保留名称，不把它表述为已完整实现并文档化的主功能。

### `polish_description_prompt_MMScan`

当前仅在注册表中列名；本页只将其视为保留名称，不把它表述为已完整实现并文档化的主功能。

### `object_cognition_QA_with_background_prompt`

当前仅在注册表中列名；本页只将其视为保留名称，不把它表述为已完整实现并文档化的主功能。

## 运行特性

- 视图发现由 `data.views` 驱动，不要求统一重命名原图。
- 当 `use_thumbnails_dir` 为 `true` 时，可优先读取资产子目录中的缩略图目录。
- 已存在且有效的输出默认会被跳过。
- 带 `raw_output` 的失败样本会在后续运行时自动重试。
- 使用 `--retry_incomplete` 时，会重试 `material`、`dimensions`、`mass`、`placement` 中为空的结果。
- 使用 `--num_chunks` 和 `--chunk_index` 时，可将大批量任务切片分发到多机或多作业执行。
