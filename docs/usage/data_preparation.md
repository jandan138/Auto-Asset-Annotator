# 数据准备指南

为了确保 Auto-Asset-Annotator 能正确读取您的 3D 资产渲染图，请遵循以下目录结构和命名规范。

## 目录结构

项目期望每个 3D 资产都有一个独立的文件夹，所有资产文件夹位于同一个父目录下。

```text
/path/to/assets_library/       <-- 输入目录 (--input_dir)
├── asset_id_001/              <-- 资产文件夹
│   ├── front.png              <-- 视图文件
│   ├── left.png
│   ├── back.png
│   └── right.png
├── asset_id_002/
│   ├── 00_front.jpg
│   ├── 01_left.jpg
│   └── ...
└── ...
```

## 视图命名与映射

不同团队渲染资产时的命名习惯可能不同（如 `front.png` vs `view_0.jpg`）。您**不需要**批量重命名文件，只需在 `config/config.yaml` 中配置 `views` 映射即可。

### 配置示例

打开 `config/config.yaml`，找到 `data.views` 部分：

```yaml
data:
  views:
    # 逻辑名称: [文件名匹配模式列表]
    front: ["front.png", "0.png", "cam_00.jpg"] 
    left:  ["left.png", "1.png", "cam_01.jpg"]
    back:  ["back.png", "2.png", "cam_02.jpg"]
    right: ["right.png", "3.png", "cam_03.jpg"]
```

**工作原理**：
1.  对于每个资产文件夹，程序会尝试寻找 `front` 视图。
2.  它会依次检查是否存在 `front.png`，如果不存在，检查 `0.png`，以此类推。
3.  找到第一个匹配的文件作为该视图的输入。

### 缩略图子目录 (Legacy 模式)

如果您的图像位于资产目录下的子文件夹（如 `thumbnails/`）中，请开启以下配置：

```yaml
data:
  use_thumbnails_dir: true
  thumbnails_dir_name: "thumbnails"
```

此时目录结构应为：
```text
asset_id_001/
└── thumbnails/
    ├── front.png
    └── ...
```

## 图像格式要求

*   **格式**: 支持 `.png`, `.jpg`, `.jpeg`, `.bmp`, `.webp`。
*   **分辨率**: 推荐 512x512 或更高。VLM 会自动缩放，但过低的分辨率会影响细节识别（如材质纹理）。
*   **背景**: 推荐使用**纯色背景**（灰色或白色）或透明背景，以避免背景干扰模型识别。
