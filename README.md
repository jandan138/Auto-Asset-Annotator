# Auto-Asset-Annotator

基于 Qwen2.5-VL 的 3D 资产自动标注流水线。当前仓库对应的主流程是：命令行读取配置，加载模型，`AnnotationPipeline` 组织图像与提示词，模型返回结构化文本，流水线解析后写入 JSON 标注结果。

## Current Status

- Total assets annotated: 52,907
- Structured annotation fields are complete at 100%
- `output/` contains the stable structured results

当前状态：50,091 个原始资产和 2,816 个回填资产都已完成标注，`description`、`material`、`dimensions`、`mass`、`placement` 五个字段完整率均为 100%。

## Quick Start

```bash
pip install -r requirements.txt
pip install -e .
python -m auto_asset_annotator.main --input_dir /path/to/assets --output_dir /path/to/results
```

常用变体：

```bash
python -m auto_asset_annotator.main --prompt_type classify_object_category_prompt --input_dir /path/to/assets --output_dir /path/to/results
python -m auto_asset_annotator.main --asset_list_file archive/temp_lists/failed_assets.txt --output_dir ./output
python -m auto_asset_annotator.main --input_dir /path/to/assets --output_dir /path/to/results --retry_incomplete
```

## Output Behavior

属性抽取默认使用 `extract_object_attributes_prompt`。这个 prompt 会要求模型返回带有 `Category`、`Description`、`Material`、`Dimensions`、`Mass`、`Placement` 标题的 structured text，而不是直接输出 JSON。

`AnnotationPipeline` 会对这段 structured text 做解析、规范化 `dimensions` 和 `mass`，然后由 `main.py` 将结果写成 `{output_dir}/{category}/{asset_id}_annotation.json`。如果解析失败，会写入包含 `raw_output` 的 JSON，后续重跑时可自动重试。

## Documentation

- 项目概览: `docs/introduction/overview.md`
- 安装部署: `docs/installation/linux_deployment.md`
- 快速开始: `docs/usage/quick_start.md`
- CLI 说明: `docs/usage/cli_reference.md`
- 开发说明: `docs/development/project_structure.md`
- 常见问题: `docs/troubleshooting/common_issues.md`
