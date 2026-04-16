# 快速开始

本页展示当前默认用法，适合首次确认安装、目录结构和输出位置是否正确。

## 1. 准备输入目录

输入目录通常按 `类别/资产ID/图片文件` 组织，例如：

```text
test_data/
  chair/
    chair_0001/
      front.png
      left.png
      back.png
      right.png
```

## 2. 运行默认标注命令

默认配置文件是 `config/config.yaml`，默认 prompt 类型是 `extract_object_attributes_prompt`。最常见的启动方式是：

```bash
python -m auto_asset_annotator.main --input_dir ./test_data --output_dir ./test_output
```

如果不传 `--prompt_type`，程序会使用配置中的默认 prompt。

## 3. 查看输出

完成后，程序会在输出目录下写入：

```text
test_output/
  chair/
    chair_0001_annotation.json
```

## 4. 输出说明

属性提取模式下，输出 JSON 不是模型直接返回的 JSON。实际流程是：

1. 模型返回带标题的 structured text。
2. `AnnotationPipeline` 在代码中解析 structured text。
3. `main.py` 将解析后的结果写入 JSON 文件。

示例：

```json
{
  "chair/chair_0001": {
    "category": "chair",
    "description": "A chair with ...",
    "material": "wooden frame, fabric seat",
    "dimensions": "0.5 * 0.5 * 0.9",
    "mass": "5.0",
    "placement": "OnFloor"
  }
}
```

如果解析失败，结果会保存 `raw_output`，后续可继续重试。
