import argparse  # 导入 argparse 模块，用于解析命令行参数
import os  # 导入 os 模块，用于处理文件系统路径和操作系统功能
import json  # 导入 json 模块，用于处理 JSON 数据的序列化和反序列化
from tqdm import tqdm  # 从 tqdm 库导入 tqdm，用于显示进度条
from .config import load_config  # 从当前包的 config 模块导入 load_config 函数，用于加载配置
from .core.model import ModelEngine  # 从当前包的 core.model 模块导入 ModelEngine 类，用于模型推理
from .core.pipeline import AnnotationPipeline  # 从当前包的 core.pipeline 模块导入 AnnotationPipeline 类，用于执行标注流程
from .utils.file import list_assets  # 从当前包的 utils.file 模块导入 list_assets 函数，用于列出资产目录

def main():  # 定义主函数
    parser = argparse.ArgumentParser(description="Auto Asset Annotator using Qwen3-VL")  # 创建 ArgumentParser 对象，设置描述信息
    parser.add_argument("--config", default="config/config.yaml", help="Path to configuration file")  # 添加 --config 参数，指定配置文件路径，默认为 config/config.yaml
    parser.add_argument("--input_dir", help="Override input directory")  # 添加 --input_dir 参数，用于覆盖配置文件中的输入目录
    parser.add_argument("--output_dir", help="Override output directory")  # 添加 --output_dir 参数，用于覆盖配置文件中的输出目录
    parser.add_argument("--model_path", help="Override model path")  # 添加 --model_path 参数，用于覆盖模型路径
    parser.add_argument("--prompt_type", help="Override prompt type")  # 添加 --prompt_type 参数，用于覆盖提示词类型
    parser.add_argument("--asset_list_file", help="Override asset list file")
    parser.add_argument("--force", action="store_true", help="Force re-annotation even if file exists and is valid")
    
    # Chunking args for batch jobs
    parser.add_argument("--num_chunks", type=int, help="Total number of chunks")  # 添加 --num_chunks 参数，指定总的分块数量，用于批处理任务
    parser.add_argument("--chunk_index", type=int, help="Current chunk index (0-based)")  # 添加 --chunk_index 参数，指定当前处理的分块索引（从 0 开始）

    args = parser.parse_args()  # 解析命令行参数

    # Load Config
    try:  # 尝试加载配置
        cfg = load_config(args.config)  # 调用 load_config 函数加载配置文件
    except FileNotFoundError:  # 捕获文件未找到异常
        print(f"Config file not found at {args.config}. Please create it or specify correct path.")  # 打印错误信息，提示配置文件未找到
        return  # 退出程序

    # Override Config with CLI args
    if args.input_dir:  # 如果命令行参数指定了输入目录
        cfg.data.input_dir = args.input_dir  # 覆盖配置中的输入目录
    if args.output_dir:  # 如果命令行参数指定了输出目录
        cfg.data.output_dir = args.output_dir  # 覆盖配置中的输出目录
    if args.model_path:  # 如果命令行参数指定了模型路径
        cfg.model.name = args.model_path  # 覆盖配置中的模型名称/路径
    if args.prompt_type:  # 如果命令行参数指定了提示词类型
        cfg.prompts.default_type = args.prompt_type  # 覆盖配置中的默认提示词类型
    if args.asset_list_file:
        cfg.data.asset_list_file = args.asset_list_file
    
    if args.num_chunks is not None:  # 如果命令行参数指定了分块数量
        cfg.processing.num_chunks = args.num_chunks  # 覆盖配置中的分块数量
    if args.chunk_index is not None:  # 如果命令行参数指定了分块索引
        cfg.processing.chunk_index = args.chunk_index  # 覆盖配置中的分块索引

    # Initialize Engine
    print(f"Initializing Model Engine with model: {cfg.model.name}")  # 打印正在初始化的模型名称
    try:  # 尝试初始化模型引擎
        engine = ModelEngine(cfg.model)  # 创建 ModelEngine 实例
    except Exception as e:  # 捕获初始化过程中的异常
        print(f"Failed to load model: {e}")  # 打印模型加载失败的错误信息
        return  # 退出程序

    pipeline = AnnotationPipeline(cfg, engine)  # 创建 AnnotationPipeline 实例，传入配置和引擎

    # List Assets
    if hasattr(cfg.data, "asset_list_file") and cfg.data.asset_list_file:
        print(f"[INFO] Loading asset list from {cfg.data.asset_list_file}")
        with open(cfg.data.asset_list_file, 'r') as f:
            all_assets = [line.strip() for line in f if line.strip()]
        print(f"[INFO] Loaded {len(all_assets)} assets from list.")
    else:
        print(f"Scanning for assets in {cfg.data.input_dir}...")  # 打印正在扫描资产目录的信息
        all_assets = list_assets(cfg.data.input_dir)  # 调用 list_assets 函数获取所有资产列表
        print(f"Found {len(all_assets)} total assets.")  # 打印找到的资产总数

    # Chunking logic
    total_assets = len(all_assets)  # 获取资产总数
    if cfg.processing.num_chunks > 1:  # 如果分块数量大于 1，则执行分块逻辑
        chunk_size = (total_assets + cfg.processing.num_chunks - 1) // cfg.processing.num_chunks  # 计算每个分块的大小（向上取整）
        start_idx = cfg.processing.chunk_index * chunk_size  # 计算当前分块的起始索引
        end_idx = min((cfg.processing.chunk_index + 1) * chunk_size, total_assets)  # 计算当前分块的结束索引（防止越界）
        assets_to_process = all_assets[start_idx:end_idx]  # 获取当前分块需要处理的资产列表
        print(f"Processing chunk {cfg.processing.chunk_index}/{cfg.processing.num_chunks}: {len(assets_to_process)} assets ({start_idx} to {end_idx})")  # 打印当前分块的处理信息
    else:  # 如果不分块
        assets_to_process = all_assets  # 处理所有资产

    # Process Loop
    os.makedirs(cfg.data.output_dir, exist_ok=True)  # 创建输出目录，如果已存在则忽略
    
    for asset_name in tqdm(assets_to_process, desc="Annotating"):  # 使用 tqdm 遍历需要处理的资产，显示进度条
        asset_path = os.path.join(cfg.data.input_dir, asset_name)  # 构造资产的完整路径
        output_file = os.path.join(cfg.data.output_dir, f"{asset_name}_annotation.json")  # 构造输出文件的路径
        
        # Ensure subdirectories exist for output_file
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Check if exists
        should_process = True
        if os.path.exists(output_file) and not args.force:
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    content = json.load(f)
                    # Check if it's a "failed" file (has raw_output)
                    if isinstance(content, dict) and len(content) == 1 and isinstance(list(content.values())[0], dict) and "raw_output" in list(content.values())[0]:
                        should_process = True
                        print(f"[INFO] Retrying previously failed asset: {asset_name}")
                    else:
                        should_process = False
            except Exception:
                # If file is corrupted or empty, reprocess
                should_process = True
        
        if not should_process:
             continue

        result = pipeline.process_asset(asset_path, cfg.prompts.default_type)  # 调用 pipeline 处理资产，获取结果
        
        if result:  # 如果处理成功并返回结果
            # Save result
            final_output = {asset_name: result} # Wrap like original script? Or just result? Original: attributes_results[object_id] = attributes[0]  # 将结果包装在字典中，以资产名称为键
            
            with open(output_file, 'w', encoding='utf-8') as f:  # 以写模式打开输出文件，指定编码为 utf-8
                json.dump(final_output, f, indent=4)  # 将结果写入 JSON 文件，缩进为 4 个空格

    print("Processing complete.")  # 打印处理完成信息

if __name__ == "__main__":  # 如果是直接运行脚本
    main()  # 调用主函数
