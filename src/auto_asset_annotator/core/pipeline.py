import os  # 导入 os 模块，用于处理文件系统路径
import json  # 导入 json 模块，用于处理 JSON 数据
import time  # 导入 time 模块，用于计时
from typing import Dict, Any, List  # 导入类型提示
from .model import ModelEngine  # 导入 ModelEngine 类，用于模型推理
from .prompt import PromptFactory  # 导入 PromptFactory 类，用于生成提示词
from ..config.settings import Config  # 导入 Config 类，用于获取配置
from ..utils.file import get_asset_images  # 导入 get_asset_images 函数，用于获取资产图片
from ..utils.image import concatenate_images  # 导入 concatenate_images 函数，用于拼接图片（暂未启用）

class AnnotationPipeline:  # 定义 AnnotationPipeline 类，用于管理标注流程
    def __init__(self, config: Config, engine: ModelEngine):  # 初始化方法
        self.config = config  # 保存配置对象
        self.engine = engine  # 保存模型引擎对象

    def process_asset(self, asset_path: str, prompt_type: str = None) -> Dict[str, Any]:  # 处理单个资产的方法
        """
        Process a single asset.
        """
        if prompt_type is None:  # 如果未指定提示词类型
            prompt_type = self.config.prompts.default_type  # 使用配置中的默认类型
            
        asset_id = os.path.basename(asset_path)  # 从路径中获取资产 ID（文件夹名）
        print(f"[INFO] Processing asset: {asset_id}")  # 打印正在处理的资产信息

        # 1. Find Images
        images_map = get_asset_images(asset_path, self.config.data)  # 根据配置查找资产的所有图片
        if not images_map:  # 如果没有找到图片
            print(f"[WARN] No images found for {asset_id}. Skipping.")  # 打印警告并跳过
            return None  # 返回 None
        
        # Sort images by view name or key to ensure deterministic order if needed, 
        # or just use the values.
        # The prompt generation usually expects a list of images.
        # If we have named views (front, left...), we should probably just use them all.
        image_paths = list(images_map.values())  # 获取所有图片的路径列表
        
        # 2. Compose Prompt
        # Object info for prompt (e.g. category extraction from ID)
        # Original code: object_pre_label_info = object_id.split('-')[:-1] 
        # We can simulate this or make it generic.
        object_info = asset_id.split('-')[:-1]  # 尝试从资产 ID 中提取对象信息（假设 ID 格式为 name-uuid）
        if not object_info:  # 如果提取失败（例如没有横杠）
            object_info = ["object", asset_id] # Fallback  # 使用默认值作为后备
            
        user_prompt = PromptFactory.compose_user_prompt(  # 调用工厂方法生成用户提示词
            image_number=len(image_paths),  # 图片数量
            prompt_type=prompt_type,  # 提示词类型
            image_merge=False, # Make configurable if needed  # 是否合并图片（目前设为 False，可配置）
            object_additional_info=object_info  # 对象的额外信息
        )

        # 3. Prepare Inputs (Text + Images)
        # This logic mimics _prepare_inputs_text_and_image
        messages = self._prepare_messages(user_prompt, image_paths)  # 准备模型输入的完整消息结构

        # 4. Inference
        start_time = time.time()  # 记录开始时间
        try:  # 尝试进行推理
            result_text = self.engine.inference(messages)  # 调用引擎进行推理，获取文本结果
            
            # Parse JSON if expected
            if "json" in prompt_type.lower() or "extract" in prompt_type.lower():  # 如果提示词类型暗示需要 JSON 输出
                try:  # 尝试解析 JSON
                    # Clean up code blocks if present
                    clean_text = result_text.strip()  # 去除首尾空白字符
                    if clean_text.startswith("```json"):  # 如果以 ```json 开头
                        clean_text = clean_text[7:]  # 去除 ```json
                    if clean_text.endswith("```"):  # 如果以 ``` 结尾
                        clean_text = clean_text[:-3]  # 去除 ```
                    
                    result_data = json.loads(clean_text)  # 解析 JSON 字符串
                    result = result_data  # 将解析结果作为最终结果
                except json.JSONDecodeError:  # 如果解析失败
                    print(f"[WARN] Failed to parse JSON for {asset_id}. Saving raw text.")  # 打印警告
                    result = {"raw_output": result_text}  # 保存原始文本
            else:  # 如果不需要 JSON
                result = result_text  # 直接使用文本结果

        except Exception as e:  # 捕获推理过程中的异常
            print(f"[ERROR] Inference failed for {asset_id}: {e}")  # 打印错误信息
            return None  # 返回 None
            
        print(f"[INFO] Finished {asset_id} in {time.time() - start_time:.2f}s")  # 打印处理完成及耗时信息
        return result  # 返回处理结果

    def _prepare_messages(self, user_prompt: str, image_paths: List[str]) -> List[Dict[str, Any]]:  # 内部方法，准备消息列表
        content = []  # 初始化内容列表
        content.append({"type": "text", "text": user_prompt})  # 添加文本提示词
        
        for img_path in image_paths:  # 遍历所有图片路径
            content.append({"type": "image_url", "image": img_path})  # 添加图片 URL（路径）
            
        return [{  # 返回消息列表
            "role": "user",  # 角色为用户
            "content": content  # 内容列表
        }]
