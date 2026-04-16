# 如何扩展模型加载

当前主线实现围绕 `src/auto_asset_annotator/core/model.py` 展开，优先服务于 **Qwen2.5-VL** 本地权重加载。

## 当前加载路径

`ModelEngine.__init__()` 的实际流程是：

1. 读取 `ModelConfig`
2. 优先尝试导入 `transformers.Qwen2_5_VLForConditionalGeneration`
3. 如果该类不可用，则回退到 `AutoModelForCausalLM`
4. 仅当 `config.name` 中包含 `Qwen3` 且前一步仍是通用回退类时，再尝试 `Qwen3VLMoeForConditionalGeneration`
5. 用同一个 `config.name` 调用 `from_pretrained(...)`
6. 再用 `AutoProcessor.from_pretrained(...)` 加载 processor

也就是说，当前代码的默认和优先路径是：

- **Qwen2.5-VL first**
- 通用 `AutoModelForCausalLM` 作为兼容回退
- Qwen3 仅作为名字命中时的附加分支，而不是当前主维护路径

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
- 在 `main.py` 中根据配置决定实例化哪种 engine
- 避免把大量分支堆进现有 `ModelEngine`

## 最小检查清单

扩展后至少确认：

- `from_pretrained()` 能正确加载模型和 processor
- `inference()` 能接收 `AnnotationPipeline` 生成的消息结构
- 返回值仍然是字符串
- `extract` / `json` prompt 仍能走当前解析链路
- 未显式要求时，不要运行重型全量标注命令来验证
