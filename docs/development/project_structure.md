# 源码结构解析

当前主线代码位于 `src/auto_asset_annotator/`，文档、脚本和历史产物都不属于运行时包的一部分。

```text
src/auto_asset_annotator/
├── __init__.py
├── main.py                  # CLI 入口：解析参数、覆盖配置、枚举资产、写出 JSON
├── config/
│   ├── __init__.py          # 导出 load_config
│   └── settings.py          # Config / ModelConfig / DataConfig / ProcessingConfig / PromptConfig
├── core/
│   ├── api_model.py         # OpenAI-compatible API backend：转换消息并发送 chat completions 请求
│   ├── model.py             # Backend factory、LocalHFEngine 与兼容别名 ModelEngine
│   ├── pipeline.py          # AnnotationPipeline：组装消息、调用推理、解析结构化文本
│   └── prompt.py            # PromptFactory 与 SUPPORTED_PROMPT_TYPES
└── utils/
    ├── file.py              # list_assets() / get_asset_images()
    └── image.py             # 图像读取与拼接辅助函数
```

## 模块职责

### `main.py`

- 解析 CLI 参数：`--config`、`--input_dir`、`--output_dir`、`--model_path`、`--model_backend`、`--api_base_url`、`--api_key_env`、`--prompt_type`、`--asset_list_file`、`--force`、`--retry_incomplete`、`--num_chunks`、`--chunk_index`
- 通过 `load_config()` 读取 `config/config.yaml`，再用 CLI 参数覆盖配置值
- 通过 `build_model_engine()` 选择 `local_hf` 或 `openai_compatible` 后端，再初始化 `AnnotationPipeline`
- 从 `asset_list_file` 或 `list_assets()` 获取待处理资产
- 在输出目录下写出 `{output_dir}/{category}/{asset_id}_annotation.json`

### `config/settings.py`

- 定义配置数据类
- `ModelConfig` 同时承载本地推理字段和 API 后端字段
- `Config.from_yaml()` 负责把 YAML 映射为运行时配置对象

### `core/api_model.py`

- `OpenAICompatibleAPIEngine` 负责校验 `api_base_url` / `api_key_env`
- 将本地图像路径转换为 data URL，保持与 OpenAI-compatible 多模态消息格式兼容
- 调用 `/v1/chat/completions`，提取文本响应，并处理轻量重试

### `core/model.py`

- `BaseModelEngine` 定义流水线依赖的统一 `inference()` 契约
- `LocalHFEngine` 保留原有本地 Hugging Face 推理逻辑
- `build_model_engine()` 根据 `ModelConfig.backend` 返回本地或 API 引擎
- `ModelEngine` 仍保留为 `LocalHFEngine` 的兼容别名

### `core/pipeline.py`

- `process_asset()` 负责单资产处理
- `get_asset_images()` 先按配置视角名查找，再回退到目录内全部图片
- 对 `extract` / `json` 命名的 prompt，调用 `parse_structured_text_enhanced()` 解析结果
- 解析成功后会覆盖 `category`、规范化 `dimensions` / `mass`；失败则返回 `raw_output`

### `core/prompt.py`

- `SUPPORTED_PROMPT_TYPES` 是 prompt 类型注册表
- `PromptFactory.compose_user_prompt()` 根据类型返回字符串或少数特例的字符串列表

### `utils/file.py`

- `list_assets()` 递归寻找包含图片的叶子目录，并返回相对路径
- `get_asset_images()` 支持命名视角、缩略图目录和回退扫描模式

## 当前运行链路

`CLI -> Config -> build_model_engine() -> backend inference -> AnnotationPipeline -> parsed JSON output`

这条链路是当前代码的真实实现：模型返回的是文本，属性提取类任务由流水线解析后再写成 JSON，而不是直接信任模型原样返回 JSON。

API 后端没有改动 `AnnotationPipeline` 的消息和解析逻辑，只是在 backend seam 上把本地图像路径转成 data URL 并转发到远程接口。`device_map`、`dtype`、`attn_implementation` 仍属于本地推理配置，API 路径会忽略它们。
