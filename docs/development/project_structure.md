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
│   ├── model.py             # ModelEngine：加载模型与 processor，执行推理
│   ├── pipeline.py          # AnnotationPipeline：组装消息、调用推理、解析结构化文本
│   └── prompt.py            # PromptFactory 与 SUPPORTED_PROMPT_TYPES
└── utils/
    ├── file.py              # list_assets() / get_asset_images()
    └── image.py             # 图像读取与拼接辅助函数
```

## 模块职责

### `main.py`

- 解析 CLI 参数：`--config`、`--input_dir`、`--output_dir`、`--model_path`、`--prompt_type`、`--asset_list_file`、`--force`、`--retry_incomplete`、`--num_chunks`、`--chunk_index`
- 通过 `load_config()` 读取 `config/config.yaml`，再用 CLI 参数覆盖配置值
- 初始化 `ModelEngine` 和 `AnnotationPipeline`
- 从 `asset_list_file` 或 `list_assets()` 获取待处理资产
- 在输出目录下写出 `{output_dir}/{category}/{asset_id}_annotation.json`

### `config/settings.py`

- 定义配置数据类
- `Config.from_yaml()` 负责把 YAML 映射为运行时配置对象

### `core/model.py`

- `ModelEngine.__init__()` 负责选择并加载模型类与 `AutoProcessor`
- `ModelEngine.inference()` 使用 chat template、`process_vision_info()` 和 `generate()` 返回文本结果

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

`CLI -> Config -> ModelEngine -> AnnotationPipeline -> parsed JSON output`

这条链路是当前代码的真实实现：模型返回的是文本，属性提取类任务由流水线解析后再写成 JSON，而不是直接信任模型原样返回 JSON。
