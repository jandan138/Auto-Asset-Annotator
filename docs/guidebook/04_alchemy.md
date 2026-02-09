# 第四章：炼金术的秘密

默认的咒语虽然好用，但有时候我们会有特殊需求。比如，我不想知道材质，我只想知道它是什么类别；或者我想让它写一段优美的描述文字。

这时候，我们需要调整“炼金配方”。

## 1. 魔法卷轴：Prompt (提示词)

Prompt 就是你对模型说的话。我们的工具里预置了好几种 Prompt，你可以通过 `--prompt_type` 参数来切换。

### 常用的 Prompt 类型

*   **`extract_object_attributes_prompt` (默认)**
    *   **效果**：像填表一样，提取材质、尺寸、分类等信息。
    *   **输出**：JSON 格式。
*   **`classify_object_category_prompt`**
    *   **效果**：只回答一个词，比如 "Chair" 或 "Sofa"。
    *   **用途**：快速给资产打标签。
*   **`describe_object_prompt_MMScan`**
    *   **效果**：写一段小作文。“这是一把优雅的椅子，椅背呈弧形...”
    *   **用途**：用于生成商品介绍或图生文检索。

### 怎么切换？

很简单，加个参数就行：

```bash
python -m auto_asset_annotator.main \
    ... \
    --prompt_type classify_object_category_prompt
```

## 2. 炼金配方表：Config 文件

除了命令行参数，还有一个更强大的控制中心：`config/config.yaml`。

用文本编辑器打开它，你会看到很多设置。

### 调节“创造力”：Temperature

```yaml
model:
  temperature: 0.8
```

*   **Temperature (温度)** 控制模型的随机性。
*   **0.1**：模型变得非常严谨、死板。每次回答几乎都一样。适合做分类任务。
*   **1.0**：模型变得非常奔放、有创造力，但也可能开始胡言乱语。适合写诗或创意描述。
*   **0.8**：默认值，是严谨与活泼的平衡点。

### 调节“视力”：Views

如果你突然决定把图片的命名规则从 `front.png` 改成 `zhengmian.jpg`，不需要改代码，只需要改这里：

```yaml
data:
  views:
    front: ["zhengmian.jpg", "front.png"]
```

## 3. 小练习

试着修改 `config.yaml`，把 `temperature` 改成 `0.1`，然后运行一遍 `describe_object_prompt_MMScan`。看看生成的描述是不是变得更“无聊”但更准确了？

掌握了这些，你就是初级炼金术士了！
