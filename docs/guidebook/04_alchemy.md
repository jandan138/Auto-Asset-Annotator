# 第四章：炼金术的秘密

同一批图片，换一种 prompt，模型就会做另一种活。这就是这座工坊真正的炼金术。

## 1. 魔法卷轴：Prompt 类型

当前注册在 `SUPPORTED_PROMPT_TYPES` 里的类型有 9 个，但真正主线常用的，是下面这几类：

- `extract_object_attributes_prompt`
  作用：提取类别、描述、材质、尺寸、质量、摆放方式
  返回：**structured text**，随后被流水线解析成 JSON
- `classify_object_category_prompt`
  作用：只返回一个类别名
- `describe_object_prompt_MMScan`
  作用：生成一段较完整的客观描述
- `find_canonical_front_view_prompt`
  作用：找标准正视图索引
- `is_symmetric_object_prompt`
  作用：判断物体是否近似各向对称

## 2. 最重要的炼金规则：命名会触发解析

在 `AnnotationPipeline.process_asset()` 里，存在一个非常实用也非常危险的约定：

- prompt 名字里包含 `extract`
- 或者包含 `json`

就会自动进入结构化解析分支。

所以：

- 你想要字段化结果时，可以利用这个约定
- 你只想要自由文本时，就别把 prompt 名起成 `extract_xxx`

## 3. 配方表：`config/config.yaml`

当前主线配置大致如下：

```yaml
model:
  name: "/cpfs/shared/simulation/zhuzihou/models/Qwen2.5-VL-7B-Instruct"
  device_map: "auto"
  dtype: "bfloat16"
  attn_implementation: "eager"
  temperature: 0.1
  max_new_tokens: 2048

prompts:
  default_type: "extract_object_attributes_prompt"
```

这些参数里：

- `temperature` 越低，回答通常越稳
- `max_new_tokens` 决定模型最多能写多长
- `default_type` 决定你不传 `--prompt_type` 时的默认任务

## 4. 一个切换 prompt 的例子

```bash
python -m auto_asset_annotator.main \
    --input_dir ./test_data \
    --output_dir ./test_output \
    --prompt_type classify_object_category_prompt
```

这时输出通常就不再是字段字典，而会更接近一个简短类别结果。

## 5. 炼金术士的经验

- 想让机器好解析，优先要求固定字段头，而不是生硬要求纯 JSON
- 想让结果更稳定，先降温度，再改 prompt
- 想增加新字段，别忘了同时检查解析器是否也要升级

掌握这些之后，你就不只是会“用模型”，而是真的开始会“调模型”了。
