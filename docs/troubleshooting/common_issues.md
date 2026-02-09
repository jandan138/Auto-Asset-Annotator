# 常见问题排查 (Troubleshooting)

## 1. 显存不足 (CUDA Out of Memory)

**现象**: 报错 `RuntimeError: CUDA out of memory.`

**解决方案**:
1.  **降低 `batch_size`**: 虽然当前 Pipeline 主要是一次处理一个资产，但如果你修改了代码进行 Batch 推理，请减小 Batch Size。
2.  **启用 Flash Attention**: 确保安装了 `flash-attn` 并在 config 中设置 `attn_implementation: "flash_attention_2"`。
3.  **更换更小的模型**: 如果显卡只有 16GB，尝试使用 `Qwen2.5-VL-7B` 而不是更大的版本，或者使用量化版本（如 GPTQ/AWQ，需代码适配）。

## 2. 找不到图像 (No images found)

**现象**: 日志显示 `[WARN] No images found for asset_xxx. Skipping.`

**解决方案**:
1.  检查 `config.yaml` 中的 `views` 配置。确保文件名匹配模式（如 `front.png`）与你实际的文件名一致。
2.  检查是否误开启了 `use_thumbnails_dir: true`，但图片实际在根目录下。
3.  检查路径权限。确保运行用户对数据目录有读取权限。

## 3. JSON 解析失败

**现象**: 日志显示 `[WARN] Failed to parse JSON for asset_xxx. Saving raw text.`

**解决方案**:
这是因为模型生成的不是合法的 JSON（可能包含 Markdown 代码块或额外的解释性文字）。
*   程序会自动尝试去除 ` ```json ` 标记，但如果模型“话多”了，仍可能失败。
*   **临时解决**: 查看输出的 `raw_output` 字段，手动修正。
*   **长期解决**: 优化 Prompt（在 `prompt.py` 中），强调 "Do not output any explanation" 或 "Strict JSON format"。

## 4. `AttributeError: 'NoneType' object has no attribute 'group'` (transformers 相关)

**现象**: 在加载 Qwen 模型时报错。

**解决方案**:
这通常是因为 `transformers` 版本过低，不支持 Qwen-VL。
请升级 transformers：
```bash
pip install --upgrade transformers
```
或者按照 `requirements.txt` 指定的版本安装。
