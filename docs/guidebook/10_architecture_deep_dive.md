# 架构深度解析 (Architecture Deep Dive)

本文档旨在深入剖析 Auto-Asset-Annotator 的系统架构与设计理念，帮助开发者理解各模块如何协同工作以实现高效的 3D 资产自动化标注。

## 1. 核心设计理念

本项目遵循 **Pipeline（流水线）** 设计模式，将复杂的标注任务拆解为清晰的独立阶段。核心理念包括：

*   **模块化 (Modularity)**: 模型引擎、提示词生成、文件扫描等功能严格解耦。
*   **配置驱动 (Config-Driven)**: 所有可变参数（路径、模型参数、Prompt 类型）均通过 `config.yaml` 管理，无需修改代码即可调整行为。
*   **鲁棒性 (Robustness)**: 针对大模型输出的不确定性，内置了 JSON 解析重试与容错机制。
*   **可扩展性 (Scalability)**: 支持分块（Chunking）处理，便于在集群环境并行调度。

## 2. 系统数据流 (Data Flow)

整个系统的数据流转过程如下：

```mermaid
graph LR
    A[Raw Assets (Images)] --> B(File Scanner);
    B --> C{Annotation Pipeline};
    D[Config] --> C;
    E[Prompt Factory] --> C;
    C --> F(Model Engine);
    F --> G[JSON Parser];
    G --> H[Output JSON Files];
```

### 关键阶段详解

1.  **扫描 (Scanning)**: `utils.file.list_assets` 递归扫描输入目录，识别包含图像文件的资产文件夹。
2.  **组装 (Composition)**: `AnnotationPipeline` 为每个资产收集多视角图片（Front, Left, Back, Right），并调用 `PromptFactory` 生成对应的 Prompt。
3.  **推理 (Inference)**: `ModelEngine` 将图像和文本 Prompt 打包发送给 Qwen-VL 模型。
4.  **解析 (Parsing)**: 获取模型的文本输出，剔除 Markdown 标记（如 \`\`\`json），解析为 Python 字典。
5.  **持久化 (Persistence)**: 将结果保存为标准 JSON 文件，保持与输入目录一致的层级结构。

## 3. 模块架构

### 3.1 主控模块 (`main.py`)
*   **职责**: 程序的入口点。
*   **功能**:
    *   解析命令行参数（覆盖 Config）。
    *   初始化全局组件（Engine, Pipeline）。
    *   执行分块逻辑（计算当前 Job 需要处理哪些资产）。
    *   管理主循环进度条 (tqdm)。

### 3.2 流水线模块 (`core/pipeline.py`)
*   **职责**: 业务逻辑的编排者。
*   **类**: `AnnotationPipeline`
*   **核心方法**: `process_asset(asset_path, prompt_type)`
    *   它不关心模型怎么跑，只关心“给我结果”。
    *   它负责将文件路径转换为模型可理解的输入格式（Message List）。

### 3.3 模型引擎 (`core/model.py`)
*   **职责**: 与底层 AI 框架 (Transformers) 的交互层。
*   **类**: `ModelEngine`
*   **特点**:
    *   封装了 `AutoProcessor` 和 `AutoModel`。
    *   自动处理多模态输入（将图片 URL/路径 转换为 Tensor）。
    *   屏蔽了不同模型（Qwen2.5-VL vs Qwen3-VL）的加载细节。

### 3.4 提示词工厂 (`core/prompt.py`)
*   **职责**: 生成结构化的 Prompt。
*   **类**: `PromptFactory`
*   **设计**: 静态方法 `compose_user_prompt` 根据 `prompt_type` 返回不同的模板。支持动态插入变量（如图片数量、场景信息）。

## 4. 并行处理机制 (Parallelism)

为了处理数万级别的资产，项目原生支持基于索引的分块（Chunking）：

*   **原理**: 将资产列表排序后，根据 `num_chunks` 和 `chunk_index` 切片。
    *   例如：1000 个资产，`num_chunks=10`，`chunk_index=0` 处理 0-99，`chunk_index=1` 处理 100-199。
*   **优势**: 可以轻松在 Slurm、Kubernetes 或多台服务器上并行启动多个实例，互不干扰。

## 5. 目录结构设计

项目采用“就地输出”或“镜像输出”策略：

*   **输入**: 任意深度的目录结构（如 `category/subcategory/asset_id`）。
*   **输出**: 自动镜像该结构到 `output_dir`（如 `output/category/subcategory/asset_id_annotation.json`）。
*   **意义**: 极大方便了后续的数据清洗和入库工作，无需重新建立索引。
