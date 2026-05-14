# 如何扩展模型加载

当前主线实现围绕 `src/auto_asset_annotator/core/model.py` 展开，主维护路径仍然优先服务于本地 **Qwen** 系列加载，但真实类选择顺序已经比早期版本更宽。

## 当前加载路径

`LocalHFEngine.__init__()` 的实际流程是：

1. 读取 `ModelConfig`
2. 如果 `config.name` 包含 `Qwen3`，先尝试导入 `transformers.Qwen3VLMoeForConditionalGeneration`
3. 再尝试导入 `transformers.Qwen2_5_VLForConditionalGeneration`
4. 如果显式多模态类不可用，则回退到 `AutoModelForCausalLM`
5. 最后才尝试 `AutoModel`
6. 用同一个 `config.name` 调用 `from_pretrained(...)`
7. 再用 `AutoProcessor.from_pretrained(...)` 加载 processor

也就是说，当前代码的主维护路径仍然偏向 Qwen，但真实加载顺序已经是：

- 名字命中时优先尝试 `Qwen3VLMoeForConditionalGeneration`
- 其次尝试 `Qwen2.5-VL`
- 然后是 `AutoModelForCausalLM`
- 最后才是 `AutoModel`

## 当前配置字段

`ModelEngine` 直接消费这些配置项：

- `model.name`
- `model.device_map`
- `model.dtype`
- `model.attn_implementation`
- `model.temperature`
- `model.max_new_tokens`

其中：

- `torch_dtype` 通过 `getattr(torch, config.dtype)` 解析
- `attn_implementation` 直接传给 `from_pretrained()`
- `trust_remote_code=True` 同时用于模型和 processor

## 扩展时要注意什么

### 1. 不只是改模型类

当前推理逻辑依赖两件事：

- `processor.apply_chat_template(...)`
- `qwen_vl_utils.process_vision_info(...)`

这说明 `ModelEngine.inference()` 目前是 **Qwen 风格多模态输入链路**。如果你接入别的 HuggingFace VLM，通常不仅要替换 `from_pretrained()` 的模型类，还要一起审视：

- 输入消息格式
- 图像预处理方式
- 文本模板构造方式
- 解码方式

### 2. 不要过度声明“支持任意模型”

仓库当前并没有一个通用适配层来正式支持 Llava、Yi-VL 或其他多模态家族。更准确的说法是：

- 代码对 **Qwen2.5-VL** 最匹配
- 对部分兼容 HuggingFace 的模型有一定改造空间
- 但非 Qwen 模型通常需要修改 `inference()`，不能只改配置就宣称支持

### 3. Qwen3 是补充分支，不是当前默认生产路径

如果你把 `model.name` 指向 Qwen3 且环境中可导入 `Qwen3VLMoeForConditionalGeneration`，当前代码会尝试该分支；否则仍会落回通用类。文档和代码都不应把这表述成“完整验证过的主线支持”。

## 建议的扩展方式

### 方案 A：继续沿用 `ModelEngine`

适用于仍然兼容当前 Qwen 输入链路的模型。

- 在 `__init__()` 中补充更明确的类选择逻辑
- 保持 `inference()` 的消息格式和 processor 调用不变

### 方案 B：新增独立 engine

适用于输入格式、processor 接口或生成方式明显不同的模型。

- 新建一个 engine 类
- 在 `build_model_engine()` 这个 backend 选择缝里接入，而不是把 provider 选择逻辑继续堆进 `main.py`
- 避免把大量分支堆进现有 `ModelEngine`

## 最小检查清单

扩展后至少确认：

- `from_pretrained()` 能正确加载模型和 processor
- `inference()` 能接收 `AnnotationPipeline` 生成的消息结构
- 返回值仍然是字符串
- `extract` / `json` prompt 仍能走当前解析链路
- 未显式要求时，不要运行重型全量标注命令来验证

## Gemma4 接入记录

Gemma4 不走 `local_hf`。仓库为它保留单独的 `local_gemma4_multimodal` backend，原因是：

- `local_hf` 的推理链路依赖 `qwen_vl_utils.process_vision_info()`
- Gemma4 的 Hugging Face 多模态模板使用 `{"type": "image", "image": ...}` content block
- 当前 pipeline 仍然输出 `{"type": "image_url", "image": ...}`，转换应放在 Gemma4 engine 内，不能改 pipeline 以免影响 API backend

Gemma4 base model 已物化到固定 release 路径：

```text
/cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8
```

Gemma4 在 live smoke 和质量 gate 通过前仍然只应作为 probe 路径。通过这些 gate 后，获准的生产任务应引用这个不可变 release 路径；`/cpfs/user/zhuzihou/models/gemma4/current` 只适合手动调试或临时 probe。

Genesis-LLM 的 LoRA adapter 已单独放在：

```text
/cpfs/user/zhuzihou/models/gemma4/adapters/genesis-llm-fullscale-v0-gpu2-seed42-epoch3
```

默认不要启用该 adapter。它来自 Genesis-LLM 的 text-to-physics 训练链路，不是经过验证的四视角图片资产标注 adapter。只有当 Gemma4 base live smoke 通过后，才把它作为 A/B 对照候选。
