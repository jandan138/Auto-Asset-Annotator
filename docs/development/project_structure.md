# 源码结构解析

```text
src/auto_asset_annotator/
├── __init__.py
├── main.py                  # [入口] CLI 参数解析与任务分发
├── config/                  # [配置层]
│   ├── __init__.py
│   └── settings.py          # 定义 Config 数据类 (Dataclasses)
├── core/                    # [核心层]
│   ├── __init__.py
│   ├── model.py             # 封装 ModelEngine，处理模型加载与推理
│   ├── pipeline.py          # 封装 AnnotationPipeline，处理业务流
│   └── prompt.py            # 封装 PromptFactory，管理提示词模板
└── utils/                   # [工具层]
    ├── __init__.py
    ├── file.py              # 文件扫描、路径查找逻辑
    └── image.py             # 图像加载、拼接逻辑
```

## 核心类说明

### `ModelEngine` (`core/model.py`)
负责与 HuggingFace Transformers 库交互。
*   `__init__`: 加载模型与 Processor。支持 `device_map="auto"` 自动多卡加载。
*   `inference`: 接收标准化的 `inputs_messages`（包含文本和图像 URL/路径），返回生成的文本。

### `AnnotationPipeline` (`core/pipeline.py`)
业务逻辑的编排者。
*   `process_asset`: 处理单个资产。
    1.  调用 `utils.file` 找到图片。
    2.  调用 `core.prompt` 生成 Prompt。
    3.  调用 `core.model` 进行推理。
    4.  解析 JSON 结果。

### `PromptFactory` (`core/prompt.py`)
静态工厂类，包含所有 Prompt 字符串模板。
