# 快速开始 (Quick Start)

本教程将带你快速完成第一次自动化标注。

## 1. 准备数据

创建一个测试目录 `test_data`，并在其中放入一个资产文件夹：

```bash
mkdir -p test_data/my_chair
# 将你的测试图片复制进去，例如 front.png, left.png, back.png, right.png
cp /path/to/your/images/*.png test_data/my_chair/
```

## 2. 修改配置 (可选)

如果你使用的是默认的 `config/config.yaml`，确保 `views` 能够匹配你的文件名。如果你的图片叫 `0.png`, `1.png` 等，默认配置已经支持。

## 3. 运行标注

运行以下命令：

```bash
python -m auto_asset_annotator.main \
    --input_dir ./test_data \
    --output_dir ./test_output \
    --prompt_type extract_object_attributes_prompt
```

## 4. 查看结果

程序运行完成后，查看 `test_output` 目录：

```bash
ls test_output/
# 应该看到 my_chair_annotation.json
```

打开 `my_chair_annotation.json`，内容应类似：

```json
{
    "my_chair": {
        "category": "chair",
        "description": "A modern wooden dining chair with a curved backrest...",
        "material": "Oak wood frame, beige fabric cushion...",
        "dimensions": "0.5 * 0.5 * 0.9",
        "mass": 5.0,
        "placement": ["OnFloor"]
    }
}
```
