# 常见问题排查 (Troubleshooting)

本页区分两类问题：

- **日常运行问题**：当前主线用户最常遇到的情况
- **历史修复工作流**：为清理旧结果而保留的补救路径

## 一、日常运行问题

### 1. 显存不足 (`CUDA out of memory`)

**现象**：模型加载或推理时报 `RuntimeError: CUDA out of memory`。

**当前建议**：

1. 确认当前模型路径是否仍指向 `Qwen2.5-VL-7B-Instruct`
2. 保持 `attn_implementation: "eager"`，除非你已经确认环境支持 `flash_attention_2`
3. 使用更合适的 GPU 机器，或自行切换到更小且已适配的模型

### 2. 找不到图像 (`No images found`)

**现象**：日志出现 `[WARN] No images found for ... Skipping.`

**排查顺序**：

1. 检查输入目录是否真的是“资产叶子目录包含图片”的结构
2. 检查 `config/config.yaml` 里的 `data.views` 是否和实际文件名一致
3. 如果你启用了 `use_thumbnails_dir: true`，确认 `thumbnails/` 目录确实存在
4. 记住：如果命名视角一个都没找到，代码会回退到目录中的全部 `.png/.jpg/.jpeg`

### 3. 输出里出现 `raw_output`

**现象**：输出 JSON 没有结构化字段，而是保存了 `raw_output`

**这表示什么**：

- 模型完成了推理
- 但其输出没有被 `parse_structured_text_enhanced()` 成功解析

**可行处理**：

1. 直接重跑同一命令，程序会自动重试已有 `raw_output` 的资产
2. 检查是否误用了一个会触发解析、但实际并非结构化输出的 prompt 名
3. 如果你在开发新 prompt，优先调整字段头和输出约束，而不是直接要求纯 JSON

### 4. 需要只补跑字段不完整的结果

当前支持的正式方式是：

```bash
python -m auto_asset_annotator.main \
    --input_dir /path/to/assets \
    --output_dir /path/to/results \
    --retry_incomplete
```

`main.py` 会检查 `material`、`dimensions`、`mass`、`placement` 是否为空，只重跑不完整项。

### 5. 需要强制全量重跑

```bash
python -m auto_asset_annotator.main \
    --input_dir /path/to/assets \
    --output_dir /path/to/results \
    --force
```

## 二、历史修复工作流

这些命令主要用于已经完成的大规模生产结果的维护，不是日常第一次运行的必经步骤。

### 1. 基于失败列表重跑

```bash
python -m auto_asset_annotator.main \
    --asset_list_file archive/temp_lists/failed_assets.txt \
    --output_dir ./output \
    --force
```

### 2. 生成失败列表

```bash
python scripts/find_failed_assets.py \
    --output_dir ./output \
    --save_list archive/temp_lists/failed_assets.txt
```

### 3. 生成不完整列表

```bash
python scripts/find_incomplete_assets.py \
    --output_dir ./output \
    --save_list archive/temp_lists/incomplete_assets.txt
```

### 4. 使用剩余列表补默认值

```bash
python scripts/fill_defaults.py \
    --output_dir ./output \
    --asset_list archive/temp_lists/remaining_incomplete.txt
```

## 三、依赖相关问题

### `transformers` / Qwen 类导入失败

如果加载模型时报错，先检查当前环境的 `transformers` 版本是否与仓库依赖兼容，并确认本地环境能导入：

- `Qwen2_5_VLForConditionalGeneration`
- `AutoProcessor`
- `qwen_vl_utils`

最稳妥的做法是重新按仓库依赖安装：

```bash
pip install -r requirements.txt
pip install -e .
```
