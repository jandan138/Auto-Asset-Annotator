import os  # 导入 os 模块，用于处理文件系统路径
import glob  # 导入 glob 模块，用于文件模式匹配
from typing import Dict, List, Optional  # 导入类型提示
from natsort import natsorted  # 导入 natsort 库，用于自然排序
from ..config.settings import DataConfig  # 导入 DataConfig 类

def find_file_by_patterns(directory: str, patterns: List[str]) -> Optional[str]:  # 定义根据模式查找文件的函数
    """
    Find the first file in directory matching one of the patterns.
    """
    for pattern in patterns:  # 遍历所有模式
        # Check if pattern is a direct filename first
        full_path = os.path.join(directory, pattern)  # 构造完整路径
        if os.path.exists(full_path):  # 如果文件存在
            return full_path  # 返回完整路径
        
        # Check glob
        matches = glob.glob(os.path.join(directory, pattern))  # 尝试使用 glob 匹配
        if matches:  # 如果有匹配结果
            return matches[0] # Return first match  # 返回第一个匹配结果
            
    return None  # 如果都未找到，返回 None

def get_asset_images(asset_path: str, config: DataConfig) -> Dict[str, str]:  # 定义获取资产图片的函数
    """
    Discover image paths for a given asset directory based on configuration.
    Returns a dictionary mapping view names (e.g. 'front') to absolute file paths.
    """
    images = {}  # 初始化图片字典
    
    # Determine the search directory
    search_dir = asset_path  # 默认搜索目录为资产路径
    if config.use_thumbnails_dir:  # 如果配置了使用缩略图目录
        search_dir = os.path.join(asset_path, config.thumbnails_dir_name)  # 构造缩略图目录路径
        if not os.path.exists(search_dir):  # 如果缩略图目录不存在
            # Fallback or strict? Let's try to look in root if thumbnails missing? 
            # Original code skips if thumbnails dir missing.
            # But let's check root just in case user config is mixed.
            if not os.path.exists(search_dir):  # 再次检查（逻辑有点冗余，保持原意）
                search_dir = asset_path  # 回退到资产根目录
    
    if not os.path.exists(search_dir):  # 如果搜索目录不存在
        return {}  # 返回空字典

    # 1. Try to find specific named views from config
    for view_name, patterns in config.views.items():  # 遍历配置中的视图映射
        found_path = find_file_by_patterns(search_dir, patterns)  # 查找匹配的文件
        if found_path:  # 如果找到了
            images[view_name] = found_path  # 添加到图片字典
            
    # 2. If no specific views found, or we want to support the "sequence" mode from original script
    # The original script took first 24 images with interval.
    # If we found nothing specific, let's grab all png/jpgs and sort them.
    if not images:  # 如果没有找到任何特定视图
        all_files = os.listdir(search_dir)  # 列出目录下所有文件
        image_files = [f for f in all_files if f.lower().endswith(('.png', '.jpg', '.jpeg'))]  # 筛选图片文件
        sorted_files = natsorted(image_files)  # 对图片文件进行自然排序
        
        # If we have images, we can map them to generic names or just list them
        # For the pipeline, we probably need a list of images. 
        # But the prompt generation often assumes specific views or just a count.
        # Let's map them to '0', '1', '2'... if we fallback to this.
        for i, f in enumerate(sorted_files):  # 遍历排序后的文件
            images[str(i)] = os.path.join(search_dir, f)  # 使用索引作为键，完整路径作为值

    return images  # 返回图片字典

def list_assets(input_dir: str) -> List[str]:
    """
    Recursively list all subdirectories in input_dir that contain images and look like assets.
    Returns relative paths from input_dir.
    """
    if not os.path.exists(input_dir):
        return []
    
    assets = []
    input_dir = os.path.abspath(input_dir)
    
    for root, dirs, files in os.walk(input_dir):
        # Check if this directory contains images
        has_images = any(f.lower().endswith(('.png', '.jpg', '.jpeg')) for f in files)
        
        if has_images:
            # It's an asset.
            # Get relative path from input_dir
            rel_path = os.path.relpath(root, input_dir)
            if rel_path != ".":
                assets.append(rel_path)
            
            # Don't look inside an asset for more assets (usually assets are leaf nodes in terms of content)
            # This prevents finding thumbnails folder inside an asset folder as a separate asset
            dirs[:] = []
            
    return natsorted(assets)
