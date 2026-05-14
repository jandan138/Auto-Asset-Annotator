# 项目概览

**Auto-Asset-Annotator** 是一个面向 3D 资产渲染图的批量标注工具。它通过命令行入口读取配置、加载多模态模型、执行单资产标注流水线，并将结果写成 JSON 文件，适合大规模资产库的离线处理。

## 核心流程

当前代码中的主流程是：`CLI -> Config -> ModelEngine -> AnnotationPipeline -> parsed JSON output`

1. `src/auto_asset_annotator/main.py` 解析 CLI 参数并加载 `config/config.yaml`。
2. `build_model_engine()` 根据配置选择本地 `local_hf`、本地 `local_gemma4_multimodal` 或远程 `openai_compatible` 后端并执行推理。
3. `AnnotationPipeline` 发现资产图片、构造 prompt、调用模型、解析返回结果。
4. `main.py` 将最终结果保存为 `{output_dir}/{category}/{asset_id}_annotation.json`。

## 结果生成方式

属性提取模式不是直接信任模型返回的 JSON。当前实现会要求模型返回带显式标题的 structured text，然后由 `AnnotationPipeline.parse_structured_text_enhanced()` 在代码里解析、清洗和归一化，再由 `main.py` 写入 JSON 文件。

如果解析失败，流水线不会伪造成功结果，而是保存：

```json
{
  "category/asset_id": {
    "raw_output": "unparsed model output text..."
  }
}
```

## 主要能力

- 批量扫描输入目录中的资产子目录。
- 按 `data.views` 解析 `front.png` / `0.png` 这类多视图文件名。
- 主维护路径支持属性提取、分类、描述等常用 prompt 类型；仓库中也保留了正视图选择、对称性判断和少量特殊 prompt 注册项，但它们的端到端维护程度不完全相同。
- 支持断点续跑、失败重试、空物理属性重试和分块并行处理。
- 输出稳定的 JSON 文件，便于后续检索、统计或数据回填。

输出格式的详细约定见 `docs/usage/output_schema.md`。Gemma4 本地多模态 smoke 的环境、命令和真实输出样例见 `docs/usage/gemma4_local_smoke.md`。

## 模块分工

- `main.py`: CLI、配置覆盖、资产列表加载、输出写盘。
- `core/model.py`: 模型加载与推理。
- `core/pipeline.py`: 图像发现、prompt 生成、structured text 解析与字段归一化。
- `core/prompt.py`: `SUPPORTED_PROMPT_TYPES` 与 prompt 模板。
- `utils/file.py`: 资产目录扫描与视图文件发现。
