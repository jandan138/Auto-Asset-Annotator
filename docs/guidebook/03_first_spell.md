# 第三章：施展第一个咒语

现在，我们来看主线入口命令。真正点火的咒语其实很简单：

```bash
python -m auto_asset_annotator.main \
    --input_dir ./test_data \
    --output_dir ./test_output
```

## 1. 念出咒语后，会发生什么？

程序会依次做这些事：

1. 读取 `config/config.yaml`
2. 用命令行参数覆盖配置里的输入、输出或 prompt 类型
3. 初始化 `ModelEngine`
4. 扫描资产目录，或者读取 `--asset_list_file`
5. 对每个资产收集图片、拼出 prompt、调用模型
6. 如果 prompt 名里带 `extract` 或 `json`，就把模型返回的 **structured text** 解析成字段
7. 最后把结果写成 JSON

## 2. 你会在输出目录里看到什么？

主线输出长这样：

```json
{
    "chair/example_asset": {
        "category": "chair",
        "description": "...",
        "material": "...",
        "dimensions": "0.5 * 0.5 * 1.0",
        "mass": "3.2",
        "placement": "OnFloor"
    }
}
```

注意两个关键点：

- 模型并不是直接被要求输出最终 JSON
- 默认属性提取 prompt 先输出带字段头的结构化文本，再由流水线解析并写成 JSON

## 3. 如果解析失败呢？

别慌。系统不会直接把失败吞掉，而是会保存：

```json
{
    "chair/example_asset": {
        "raw_output": "模型原始输出文本..."
    }
}
```

这样你可以：

- 复查模型到底说了什么
- 用同一条命令再次运行，让它自动重试失败项

## 4. 常见卡点

- `CUDA out of memory`：显存装不下模型
- `No images found`：图片命名或目录结构没有被当前配置识别
- 输出里只有 `raw_output`：说明模型没有按预期的结构化格式回答

第一次看到 JSON 成功落盘时，你就已经完成了这条流水线的最小闭环。
