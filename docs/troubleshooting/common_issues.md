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

1. 检查输入目录是否真的是“资产目录包含图片，且命中后停止继续向下遍历该分支”的结构
2. 检查 `config/config.yaml` 里的 `data.views` 是否和实际文件名一致
3. 如果你启用了 `use_thumbnails_dir: true`，优先确认 `thumbnails/` 目录是否存在；即使不存在，当前代码也会回退到资产根目录继续查找
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

### 6. Gemma4 processor 没有图片张量

**现象**：processor-only smoke 只输出 `input_ids` / `attention_mask`，没有 `pixel_values` 或 `image_position_ids`。

**常见日志**：

```text
processor_class: TokenizersBackend
keys: ['attention_mask', 'input_ids']
missing image tensor keys
```

**原因**：当前 Python 环境的 Transformers 不足以支持 Gemma4 多模态 processor。仓库 `.venv_dlc` 中的 `transformers 5.2.0` 已确认会出现这个问题。

**处理**：

1. 使用已验证的 Genesis-LLM QLoRA env：`/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python`
2. 确认 `transformers.__version__` 是 `5.8.0.dev0` 或等价支持 Gemma4 多模态类的版本
3. 先跑 `docs/usage/gemma4_local_smoke.md` 中的 processor-only smoke，再跑真实模型 smoke

### 7. Gemma4 bitsandbytes FP4 断言失败

**现象**：真实图片推理进入 Gemma4 vision tower 后失败。

**常见日志**：

```text
FP4 quantization state not initialized
AssertionError
```

**原因**：Unsloth 4-bit Gemma4 checkpoint 需要先加载 Unsloth patch。没有 patch 时，bitsandbytes 的 FP4 quantization state 会在 vision branch 初始化失败。

**处理**：

1. 使用当前 `local_gemma4_multimodal` backend，不要绕过 backend 手写推理。
2. 确认环境中能导入 `unsloth`。
3. 手写脚本必须在任何 Transformers import 前 `import unsloth`。
4. 设置 `UNSLOTH_COMPILE_LOCATION` 到 run-local cache，避免污染仓库根目录。

### 8. 仓库根目录出现 `unsloth_compiled_cache/`

**现象**：`git status --short` 出现 `?? unsloth_compiled_cache/`。

**原因**：Unsloth 默认把编译缓存写到当前工作目录。

**处理**：

1. 不要提交这个目录。
2. 将后续 smoke 的 `UNSLOTH_COMPILE_LOCATION` 指到 run-local cache，例如 `/cpfs/user/zhuzihou/tmp/auto_asset_annotator_smoke/<run_id>/cache/unsloth_compiled_cache`。
3. 当前 backend 默认会选择当前工作树之外的绝对路径；若仍出现 repo-root cache，优先检查是否手写脚本绕过了 backend。

### 9. 输出格式和原始数据集 annotation 不一致

**现象**：Auto-Asset 输出是 `{ "category/asset_id": {...} }`，而 GRScenes 原始 annotation 是直接对象并包含 `uid`、`asset_type`、`usd_size` 等字段。

**解释**：这是两个不同 schema。Auto-Asset 输出与仓库现有 `./output/...` 结果一致，但不等于 GRScenes metadata schema。

**处理**：

- 只做 smoke 或标注结果保存时，保留 Auto-Asset 输出格式。
- 如果要回填 GRScenes 原始 metadata，先按 `docs/usage/output_schema.md` 做 schema merge，不要直接覆盖。

## 二、历史修复工作流

这些命令主要用于已经完成的大规模生产结果的维护，不是日常第一次运行的必经步骤。

### 1. 基于失败列表重跑

```bash
python -m auto_asset_annotator.main \
    --input_dir /path/to/assets \
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
