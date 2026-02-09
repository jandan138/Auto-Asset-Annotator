# 第三章：施展第一个咒语

万事俱备，只欠东风。现在我们要念出那句咒语，唤醒沉睡的 Qwen-VL。

## 1. 启动命令

打开终端，确保你还在项目目录下，并且 Conda 环境已经激活。

输入这行命令（记得把路径换成你自己的）：

```bash
python -m auto_asset_annotator.main \
    --input_dir ./test_data \
    --output_dir ./test_output
```

**发生了什么？**

1.  **加载模型**：你会看到屏幕上开始打印加载进度条。这是最慢的一步，需要把几十 GB 的数据搬到显存里。耐心等待，如果你的显存不够，这时候可能会报错（OOM）。
2.  **扫描资产**：它会说 "Found 1 assets"（如果你只放了一个测试品）。
3.  **开始推理**：你会看到进度条开始走动。`Annotating: 0%| | 0/1 ...`
4.  **完成**：最后它会说 "Processing complete."

## 2. 查收成果

快去 `test_output` 文件夹看看！你应该能看到一个 `.json` 文件。

用记事本（或者 VS Code）打开它，你可能会看到这样的惊喜：

```json
{
    "my_first_item": {
        "category": "chair",
        "description": "This is a modern style dining chair...",
        "material": "The legs are made of oak wood...",
        "dimensions": "0.5 * 0.5 * 1.0",
        "placement": ["OnFloor"]
    }
}
```

看！它不仅认出了这是椅子，还看出了材质是橡木（Oak），甚至估算了尺寸。这就是 VLM 的魔力。

## 3. 如果失败了...

*   **报错 "CUDA out of memory"**：说明你的显卡显存太小，装不下这个模型。
    *   *解法*：尝试换个小点的模型（比如 Qwen2.5-VL-3B，如果有的话），或者去借台更好的机器。
*   **报错 "No images found"**：说明它没找到图片。
    *   *解法*：检查一下你的文件名，是不是叫 `front.jpg` 但配置里只写了 `front.png`？（后缀名也要匹配哦！）

恭喜你！你已经成功完成了第一次自动化标注。下一章，我们将学习如何通过修改“配方”来让它干更多复杂的活。
