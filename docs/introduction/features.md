# 功能特性详解

本文档详细介绍 **Auto-Asset-Annotator** 支持的核心功能及技术特性。

## 1. 支持的模型

本项目针对 **Qwen-VL** 系列模型进行了深度优化，但也保留了良好的扩展性。

*   **Qwen2.5-VL-7B-Instruct** (推荐)：当前性价比最高的选择，具备强大的指令遵循能力和 OCR 能力。
*   **Qwen2.5-VL-72B-Instruct**：适用于对精度要求极高的场景。
*   **Qwen-VL-Chat (Legacy)**：支持旧版模型，需注意 transformers 版本兼容性。

## 2. 标注任务类型 (Prompt Types)

通过 `config.yaml` 或 CLI 参数 `--prompt_type` 可切换不同的标注模式：

### 2.1 属性提取 (`extract_object_attributes_prompt`)
这是最常用的模式，输出严格的 JSON 格式。提取字段包括：
*   `category`: 物品类别（如 "chair", "bottle"）。
*   `description`: 3-4 句的详细外观描述。
*   `material`: 材质分析（包含部位对应关系，如 "wooden legs", "fabric seat"）。
*   `dimensions`: 估算的尺寸 (长*宽*高)。
*   `mass`: 估算的质量。
*   `placement`: 建议的放置位置（如 `OnFloor`, `OnTable`）。

### 2.2 物品分类 (`classify_object_category_prompt`)
专注于类别识别，输出单一的类别名称。适用于构建资产标签体系。

### 2.3 详细描述 (`describe_object_prompt_MMScan`)
生成一段流畅的自然语言描述，覆盖物理外观、材质、比例、状态、功能用途和设计特征。

### 2.4 对称性检测 (`is_symmetric_object_prompt`)
判断物体是否具有旋转对称性（如圆柱体、球体）。输出 `0` (是) 或 `1` (否)。

### 2.5 正视图寻找 (`find_canonical_front_view_prompt`)
从一组多视图图像中，识别出最符合 "Canonical Front View"（标准正视图）的那一张图片的索引。

## 3. 高级特性

### 3.1 灵活的视图映射
无需重命名原始文件。通过配置文件，你可以定义如何找到需要的视图：
```yaml
views:
  front: ["front.png", "cam_00.jpg"]  # 尝试匹配列表中任意一个
  left:  ["left.png", "cam_01.jpg"]
```

### 3.2 分布式分块处理 (Chunking)
针对百万级数据集，工具内置了分片逻辑。
*   `--num_chunks 100`: 将任务分为 100 份。
*   `--chunk_index 5`: 当前节点只处理第 6 份数据。
这意味着你可以轻松编写 Slurm 脚本或 Kubernetes Job 来并行处理海量数据。

### 3.3 自动重试与容错
*   自动跳过已存在的标注文件（断点续传）。
*   自动检测损坏的图像文件并跳过。
*   JSON 解析失败时保留原始文本输出，防止数据丢失。
