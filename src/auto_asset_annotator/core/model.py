import torch  # 导入 PyTorch 库
from transformers import AutoProcessor, AutoModel  # 从 transformers 库导入 AutoProcessor 和 AutoModel
from qwen_vl_utils import process_vision_info  # 导入 qwen_vl_utils，用于处理视觉信息
from ..config.settings import ModelConfig  # 从配置模块导入 ModelConfig 类
from typing import List, Dict, Any  # 导入类型提示

class ModelEngine:  # 定义 ModelEngine 类，用于封装模型操作
    def __init__(self, config: ModelConfig):  # 初始化方法，接收模型配置
        self.config = config  # 保存配置对象
        print(f"[INFO] Loading model: {config.name}")  # 打印正在加载的模型名称
        
        # Try to import specific class if needed, otherwise use AutoModel
        try:  # 尝试导入 Qwen3VLMoeForConditionalGeneration
            from transformers import Qwen3VLMoeForConditionalGeneration
            model_class = Qwen3VLMoeForConditionalGeneration  # 如果成功，使用该类
        except ImportError:  # 如果导入失败
            try:  # 尝试导入 Qwen2_5_VLForConditionalGeneration
                 from transformers import Qwen2_5_VLForConditionalGeneration
                 model_class = Qwen2_5_VLForConditionalGeneration  # 如果成功，使用该类
            except ImportError:  # 如果都导入失败
                 from transformers import AutoModelForCausalLM
                 model_class = AutoModelForCausalLM  # 使用通用的 AutoModelForCausalLM

        print(f"[INFO] Using model class: {model_class.__name__}")  # 打印实际使用的模型类名

        self.model = model_class.from_pretrained(  # 加载预训练模型
            config.name,  # 模型名称或路径
            torch_dtype=getattr(torch, config.dtype),  # 设置数据类型（如 bfloat16）
            attn_implementation=config.attn_implementation,  # 设置注意力机制实现（如 flash_attention_2）
            device_map=config.device_map,  # 设置设备映射
            trust_remote_code=True  # 允许执行远程代码
        )
        self.processor = AutoProcessor.from_pretrained(config.name, trust_remote_code=True)  # 加载对应的处理器
        print("[INFO] Model loaded successfully.")  # 打印模型加载成功信息

    def inference(self, inputs_messages: List[Dict[str, Any]]) -> str:  # 定义推理方法
        """
        Run inference on a single message structure.
        """
        # Prepare text input
        text = self.processor.apply_chat_template(  # 应用聊天模板，将消息转换为文本
            inputs_messages, tokenize=False, add_generation_prompt=True  # 不进行分词，添加生成提示
        )
        
        # Prepare vision input
        image_inputs, video_inputs = process_vision_info(inputs_messages)  # 处理视觉信息（图像和视频）
        
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
            temperature=self.config.temperature  # 设置采样温度
        )
        
        generated_ids_trimmed = [  # 裁剪生成的 ID，去除输入部分的 token
            out_ids[len(in_ids) :] for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]
        
        output_text = self.processor.batch_decode(  # 解码生成的 ID 为文本
            generated_ids_trimmed, skip_special_tokens=True, clean_up_tokenization_spaces=False  # 跳过特殊 token，不清理分词空格
        )
        
        return output_text[0]  # 返回生成的文本（取第一个结果）
