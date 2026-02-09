import yaml  # 导入 yaml 模块，用于解析 YAML 配置文件
import os  # 导入 os 模块，用于处理文件系统路径
from dataclasses import dataclass, field  # 导入 dataclass 和 field，用于定义数据类
from typing import Dict, Any, List, Optional  # 导入类型提示，用于静态类型检查

@dataclass  # 使用 dataclass 装饰器定义 ModelConfig 类，用于存储模型配置
class ModelConfig:
    name: str  # 模型名称或路径
    device_map: str = "auto"  # 设备映射策略，默认为 "auto"
    dtype: str = "bfloat16"  # 数据类型，默认为 "bfloat16"
    attn_implementation: str = "flash_attention_2"  # 注意力机制实现，默认为 "flash_attention_2"
    temperature: float = 0.8  # 生成温度，默认为 0.8
    max_new_tokens: int = 512  # 最大新生成 token 数量，默认为 512

@dataclass  # 使用 dataclass 装饰器定义 DataConfig 类，用于存储数据配置
class DataConfig:
    input_dir: str  # 输入目录路径
    output_dir: str  # 输出目录路径
    views: Dict[str, List[str]]  # 视图映射字典，键为视图名称，值为文件名模式列表
    use_thumbnails_dir: bool = False  # 是否使用缩略图子目录，默认为 False
    thumbnails_dir_name: str = "thumbnails"  # 缩略图子目录名称，默认为 "thumbnails"

@dataclass  # 使用 dataclass 装饰器定义 ProcessingConfig 类，用于存储处理配置
class ProcessingConfig:
    batch_size: int = 1  # 批处理大小，默认为 1
    num_chunks: int = 1  # 分块数量，默认为 1
    chunk_index: int = 0  # 当前分块索引，默认为 0

@dataclass  # 使用 dataclass 装饰器定义 PromptConfig 类，用于存储提示词配置
class PromptConfig:
    default_type: str = "extract_object_attributes_prompt"  # 默认提示词类型，默认为 "extract_object_attributes_prompt"

@dataclass  # 使用 dataclass 装饰器定义 Config 类，作为总配置类
class Config:
    model: ModelConfig  # 模型配置部分
    data: DataConfig  # 数据配置部分
    processing: ProcessingConfig  # 处理配置部分
    prompts: PromptConfig  # 提示词配置部分

    @classmethod  # 定义类方法，用于从 YAML 文件加载配置
    def from_yaml(cls, path: str) -> 'Config':
        if not os.path.exists(path):  # 检查配置文件是否存在
            raise FileNotFoundError(f"Config file not found at {path}")  # 如果不存在，抛出文件未找到异常
            
        with open(path, 'r', encoding='utf-8') as f:  # 以只读模式打开配置文件，指定编码为 utf-8
            data = yaml.safe_load(f)  # 使用 yaml.safe_load 解析 YAML 内容
            
        return cls(  # 返回 Config 实例，使用解析出的数据初始化各子配置
            model=ModelConfig(**data.get('model', {})),  # 初始化 ModelConfig
            data=DataConfig(**data.get('data', {})),  # 初始化 DataConfig
            processing=ProcessingConfig(**data.get('processing', {})),  # 初始化 ProcessingConfig
            prompts=PromptConfig(**data.get('prompts', {}))  # 初始化 PromptConfig
        )

def load_config(path: str = "config/config.yaml") -> Config:  # 定义加载配置的辅助函数，提供默认路径
    return Config.from_yaml(path)  # 调用 Config.from_yaml 方法加载配置
