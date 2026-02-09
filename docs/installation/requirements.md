# 硬件与软件依赖

在部署 **Auto-Asset-Annotator** 之前，请确保您的环境满足以下要求。

## 硬件要求

由于 VLM 模型通常显存占用较大，建议使用 NVIDIA GPU。

*   **GPU**: NVIDIA GPU，显存要求取决于所选模型：
    *   **Qwen2.5-VL-7B**: 至少 16GB VRAM (推荐 24GB+，如 A10, 3090, 4090)。
    *   **Qwen2.5-VL-72B**: 至少 80GB VRAM (如 A100, H100)，或使用多卡推理。
*   **CPU**: 建议 8 核以上，以加快图像预处理速度。
*   **RAM**: 建议 32GB 以上。
*   **存储**: 预留至少 50GB 用于存放模型权重和环境依赖。

## 软件依赖

*   **操作系统**: Linux (Ubuntu 20.04/22.04 推荐), Windows (支持但主要用于开发).
*   **Python**: 3.8 - 3.11
*   **CUDA**: 11.8 或 12.1 (推荐)
*   **PyTorch**: 2.1.0 或更高版本

### 核心 Python 库
项目依赖的具体版本定义在 `requirements.txt` 中：
*   `transformers`: 模型加载与推理的核心库。
*   `torch`: 深度学习框架。
*   `pillow`: 图像处理。
*   `qwen-vl-utils`: Qwen 官方提供的视觉处理工具。
*   `accelerate`: 优化模型加载和多卡推理。
