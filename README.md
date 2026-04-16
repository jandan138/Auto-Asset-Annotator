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

默认配置现在同时支持两条路径，但仓库中 checked-in 的 `config/config.yaml` 保持为可直接运行的 `local_hf` 默认值：

- `local_hf`：加载本地 Hugging Face/Qwen-VL 权重。
- `openai_compatible`：把图片转成 data URL 后调用兼容 OpenAI Chat Completions 的多模态 API。仓库中的示例目标模型是 `gemini-2.5-flash-image`。

API 后端是显式示例路径，不是默认运行模式。使用 API 后端前，必须同时配置真实的 `api_base_url` 和 `NEWAPI_API_KEY`，不要把密钥写入仓库文件：

```bash
export NEWAPI_API_KEY="<your-api-key>"
python -m auto_asset_annotator.main \
  --model_backend openai_compatible \
  --model_path gemini-2.5-flash-image \
  --api_base_url https://your-openai-compatible-host \
  --api_key_env NEWAPI_API_KEY \
  --input_dir /path/to/assets \
  --output_dir /path/to/results
```

仅导出 `NEWAPI_API_KEY` 而保留占位 host 不能运行 API 路径。

如果要使用 checked-in 默认本地模型，直接运行即可；如果之前切到了 API 模式，也可用 CLI 覆盖切回本地：

```bash
python -m auto_asset_annotator.main \
  --model_backend local_hf \
  --model_path /cpfs/shared/simulation/zhuzihou/models/Qwen2.5-VL-7B-Instruct \
  --input_dir /path/to/assets \
  --output_dir /path/to/results
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

## Backend Notes

`openai_compatible` 后端复用同一条 `CLI -> Config -> Engine -> AnnotationPipeline -> parser` 链路，只替换 `ModelEngine` 的推理实现。它会读取 `model.api_base_url`、`model.api_key_env`、`model.api_timeout_seconds`、`model.api_max_retries`，并将本地图像路径编码成 data URL 后提交到 `/v1/chat/completions`。

`device_map`、`dtype`、`attn_implementation` 只对 `local_hf` 生效；切换到 `openai_compatible` 时这些字段会被忽略。

## Documentation

- 项目概览: `docs/introduction/overview.md`
- 安装部署: `docs/installation/linux_deployment.md`
- 快速开始: `docs/usage/quick_start.md`
- CLI 说明: `docs/usage/cli_reference.md`
- DLC 运维流程: `docs/dlc/README.md`
- 开发说明: `docs/development/project_structure.md`
- 常见问题: `docs/troubleshooting/common_issues.md`

For maintained Alibaba Cloud PAI-DLC operations, use the wrapper-first workflow documented in `docs/dlc/README.md`.
