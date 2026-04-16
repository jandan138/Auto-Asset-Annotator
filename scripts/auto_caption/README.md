# auto_caption 工具说明

`scripts/auto_caption/` 是一组**独立的实验/辅助脚本**，不是当前主维护的生产标注入口。

## 这套脚本是什么

当前目录下的脚本围绕：

- `gr100_object_caption_by_Qwen3VL.py`
- `qwen_utils.py`

它们更接近早期或专项用途的自动 caption / 属性抽取工具，使用的是 **Qwen3-VL** 风格代码路径，并带有自己的一套 prompt 与图像处理逻辑。

## 它不是什么

它**不是**当前仓库主要维护的 annotation pipeline。主线生产流程在：

- `src/auto_asset_annotator/main.py`
- `src/auto_asset_annotator/core/pipeline.py`
- `src/auto_asset_annotator/core/model.py`
- `src/auto_asset_annotator/core/prompt.py`

如果你的目标是运行当前维护中的批量标注系统，应使用：

```bash
python -m auto_asset_annotator.main --input_dir /path/to/assets --output_dir /path/to/results
```

## 当前目录脚本的特点

- 直接依赖 `Qwen3VLMoeForConditionalGeneration`
- 使用本目录下的 `qwen_utils.py`
- 面向特定数据布局，例如对象目录中的 `thumbnails/`
- 输出位置和主线 pipeline 不同

## 使用前提醒

- 先确认你需要的确实是这套独立工具，而不是主线 pipeline
- 相关 prompt 类型可在 `scripts/auto_caption/qwen_utils.py` 中查看
- 由于这些脚本会直接加载大模型，未明确需要时不要把它们当作轻量验证命令
