from PIL import Image  # 导入 PIL 库中的 Image 模块，用于图像处理
from typing import List, Union  # 导入类型提示
import os  # 导入 os 模块，用于处理文件系统路径

def concatenate_images(  # 定义拼接图像的函数
    images_input: Union[List[str], List[Image.Image]],  # 输入可以是文件路径列表或 PIL Image 对象列表
    row_number: int = 2  # 指定行数，默认为 2
) -> Image.Image:  # 返回拼接后的 PIL Image 对象
    """
    Concatenate a list of images into a grid.
    """
    if not images_input:  # 如果输入列表为空
        raise ValueError("Input list cannot be empty")  # 抛出值错误异常
    
    # Convert input to PIL Images
    images = []  # 初始化图像列表
    first_item = images_input[0]  # 获取第一个元素
    
    if isinstance(first_item, str):  # 如果第一个元素是字符串（路径）
        # Input is a list of file paths
        for path in images_input:  # 遍历输入列表
            if not isinstance(path, str):  # 检查是否所有元素都是字符串
                 raise TypeError("All items must be strings when first item is a string")  # 抛出类型错误异常
            images.append(Image.open(path))  # 打开图像并添加到列表
    elif isinstance(first_item, Image.Image):  # 如果第一个元素是 PIL Image 对象
        # Input is a list of PIL Images
        for img in images_input:  # 遍历输入列表
            if not isinstance(img, Image.Image):  # 检查是否所有元素都是 PIL Image 对象
                raise TypeError("All items must be PIL Image objects when first item is an Image")  # 抛出类型错误异常
            images.append(img)  # 添加到列表
    else:  # 如果类型不支持
        raise TypeError(f"Unsupported input type: {type(first_item)}. Expected str or PIL.Image.Image")  # 抛出类型错误异常
    
    # Validate that all images have the same size (or resize them? Original code asserts strict equality)
    # Ideally we should probably resize to match the first one, but let's stick to original logic for now
    # but maybe add a gentle resize if they differ slightly? 
    # For now, let's keep it strict but print useful error.
    base_size = images[0].size  # 获取基准尺寸（第一张图的尺寸）
    if any(img.size != base_size for img in images):  # 检查是否有图片尺寸与基准不一致
        # Optional: Resize to base_size instead of raising error?
        # images = [img.resize(base_size) for img in images]
        # For strictness:
        raise ValueError(f"All images must have the same size. Expected {base_size}, but found variations.")  # 抛出值错误异常
    
    # Calculate grid dimensions
    image_width, image_height = base_size  # 获取单张图片的宽和高
    num_images_per_row = len(images) // row_number + (1 if len(images) % row_number > 0 else 0)  # 计算每行的图片数量
    
    new_image_width = image_width * num_images_per_row  # 计算新图片的宽度
    new_image_height = image_height * row_number  # 计算新图片的高度

    # Create the output image
    new_image = Image.new('RGB', (new_image_width, new_image_height))  # 创建新的 RGB 图像
    
    # Place images in the grid
    for idx, image in enumerate(images):  # 遍历所有图片
        row = idx // num_images_per_row  # 计算当前图片的行索引
        col = idx % num_images_per_row  # 计算当前图片的列索引
        position = (col * image_width, row * image_height)  # 计算粘贴位置
        new_image.paste(image, position)  # 将图片粘贴到新图像上
        
    return new_image  # 返回拼接后的图像

def load_image(path: str) -> Image.Image:  # 定义加载图像的函数
    if not os.path.exists(path):  # 如果文件不存在
        raise FileNotFoundError(f"Image not found: {path}")  # 抛出文件未找到异常
    return Image.open(path)  # 打开并返回图像
