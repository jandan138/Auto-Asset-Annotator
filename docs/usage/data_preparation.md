# 数据准备指南

为了让程序稳定发现资产和视图图片，输入目录应遵循当前代码所期望的目录形状。

## 输入目录结构

期望的目录布局如下：

```text
{input_dir}/
  {category}/
    {asset_id}/
      front.png
      left.png
      back.png
      right.png
```

例如：

```text
data/
  chair/
    000123/
      front.png
      left.png
      back.png
      right.png
  lamp/
    000456/
      0.png
      1.png
      2.png
      3.png
```

`utils/file.py:list_assets()` 会递归扫描 `input_dir`，把包含图片文件的叶子目录视为一个资产，并返回相对路径，例如 `chair/000123`。

## 视图文件发现规则

默认配置中的 `data.views` 为：

```yaml
views:
  front: ["front.png", "0.png"]
  left: ["left.png", "1.png"]
  back: ["back.png", "2.png"]
  right: ["right.png", "3.png"]
```

程序会按顺序尝试这些命名模式。如果一个资产目录里找不到这些命名视图，`get_asset_images()` 会退回到读取该目录中全部 `.png`、`.jpg`、`.jpeg` 文件并按自然顺序排序。

## 缩略图子目录模式

若配置中启用了：

```yaml
use_thumbnails_dir: true
thumbnails_dir_name: "thumbnails"
```

则会优先在资产目录下的 `thumbnails/` 子目录中查找视图文件。

## 输出目录结构

每个资产的输出文件写入位置为：

```text
{output_dir}/{category}/{asset_id}_annotation.json
```

例如：

```text
output/
  chair/
    000123_annotation.json
  lamp/
    000456_annotation.json
```

JSON 内部的顶层键仍然使用资产相对路径，例如 `chair/000123`。

## 文件格式说明

- 当前代码识别的图片扩展名为 `.png`、`.jpg`、`.jpeg`。
- 同一个资产目录建议只放该资产对应的渲染图，避免把无关图片混入回退扫描结果。
- 如果使用类别目录，输出也会自动按类别分层保存，便于后续处理。
