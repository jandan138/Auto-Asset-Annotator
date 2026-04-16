from ..config.settings import ModelConfig  # 从配置模块导入 ModelConfig 类
from typing import List, Dict, Any, Protocol  # 导入类型提示


class BaseModelEngine(Protocol):
    def inference(self, inputs_messages: List[Dict[str, Any]]) -> str: ...


class LocalHFEngine:  # 定义 LocalHFEngine 类，用于封装本地模型操作
    def __init__(self, config: ModelConfig):  # 初始化方法，接收模型配置
        import torch  # 导入 PyTorch 库
        from transformers import (
            AutoModel,
            AutoProcessor,
        )  # 从 transformers 库导入本地模型组件

        try:
            from transformers import AutoModelForCausalLM
        except ImportError:
            AutoModelForCausalLM = None

        self.config = config  # 保存配置对象
        self._torch = torch
        print(f"[INFO] Loading model: {config.name}")  # 打印正在加载的模型名称

        # Prefer explicit multimodal classes first, then a generation-capable
        # generic fallback, and only use AutoModel as the broadest last resort.
        model_classes = []

        if "Qwen3" in config.name:
            try:
                from transformers import Qwen3VLMoeForConditionalGeneration

                model_classes.append(Qwen3VLMoeForConditionalGeneration)
            except ImportError:
                pass

        try:
            from transformers import Qwen2_5_VLForConditionalGeneration

            model_classes.append(Qwen2_5_VLForConditionalGeneration)
        except ImportError:
            pass

        if AutoModelForCausalLM is not None:
            model_classes.append(AutoModelForCausalLM)
        model_classes.append(AutoModel)

        model_class = None
        model = None
        last_error = None

        for candidate_class in model_classes:
            try:
                candidate_model = candidate_class.from_pretrained(  # 加载预训练模型
                    config.name,  # 模型名称或路径
                    torch_dtype=getattr(
                        torch, config.dtype
                    ),  # 设置数据类型（如 bfloat16）
                    attn_implementation=config.attn_implementation,  # 设置注意力机制实现（如 flash_attention_2）
                    device_map=config.device_map,  # 设置设备映射
                    trust_remote_code=True,  # 允许执行远程代码
                )
            except Exception as exc:
                last_error = exc
                continue

            if not hasattr(candidate_model, "generate"):
                if candidate_class is AutoModel:
                    raise RuntimeError(
                        f"Loaded model '{config.name}' does not support generation"
                    )

                last_error = RuntimeError(
                    f"Loaded model class {candidate_class.__name__} does not support generation"
                )
                continue

            model_class = candidate_class
            model = candidate_model
            break

        if model is None:
            raise RuntimeError(
                f"Failed to load a generation-capable model for '{config.name}'"
            ) from last_error

        print(
            f"[INFO] Using model class: {model_class.__name__}"
        )  # 打印实际使用的模型类名

        self.model = model
        self.processor = AutoProcessor.from_pretrained(
            config.name, trust_remote_code=True
        )  # 加载对应的处理器
        print("[INFO] Model loaded successfully.")  # 打印模型加载成功信息

    def inference(self, inputs_messages: List[Dict[str, Any]]) -> str:  # 定义推理方法
        """
        Run inference on a single message structure.
        """
        from qwen_vl_utils import (
            process_vision_info,
        )  # 导入 qwen_vl_utils，用于处理视觉信息

        # Prepare text input
        text = self.processor.apply_chat_template(  # 应用聊天模板，将消息转换为文本
            inputs_messages,
            tokenize=False,
            add_generation_prompt=True,  # 不进行分词，添加生成提示
        )

        # Prepare vision input
        image_inputs, video_inputs = process_vision_info(
            inputs_messages
        )  # 处理视觉信息（图像和视频）

        # Process inputs
        inputs = self.processor(  # 使用处理器处理文本和视觉输入
            text=[text],  # 文本输入列表
            images=image_inputs,  # 图像输入
            videos=video_inputs,  # 视频输入
            padding=True,  # 启用填充
            return_tensors="pt",  # 返回 PyTorch 张量
        )
        inputs = inputs.to(self.model.device)  # 将输入移动到模型所在的设备（GPU/CPU）

        # Generate
        generated_ids = self.model.generate(  # 调用模型生成方法
            **inputs,  # 解包输入参数
            max_new_tokens=self.config.max_new_tokens,  # 设置最大生成 token 数
            temperature=self.config.temperature,  # 设置采样温度
        )

        generated_ids_trimmed = [  # 裁剪生成的 ID，去除输入部分的 token
            out_ids[len(in_ids) :]
            for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]

        output_text = self.processor.batch_decode(  # 解码生成的 ID 为文本
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,  # 跳过特殊 token，不清理分词空格
        )

        return output_text[0]  # 返回生成的文本（取第一个结果）


def build_model_engine(config: ModelConfig) -> BaseModelEngine:
    if config.backend == "local_hf":
        return LocalHFEngine(config)
    if config.backend == "openai_compatible":
        try:
            from .api_model import OpenAICompatibleAPIEngine
        except ModuleNotFoundError as exc:
            raise ValueError(
                "openai_compatible backend is not available in this installation"
            ) from exc

        return OpenAICompatibleAPIEngine(config)
    raise ValueError(f"Unsupported model backend: {config.backend}")


ModelEngine = LocalHFEngine
