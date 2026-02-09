# Linux 服务器部署指南

本指南将引导您在 Linux 服务器上从零开始搭建运行环境。

## 1. 准备环境

建议使用 Anaconda 或 Miniconda 来管理 Python 环境，避免与系统环境冲突。

### 1.1 安装 Miniconda (如果尚未安装)
```bash
mkdir -p ~/miniconda3
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh
~/miniconda3/bin/conda init bash
source ~/.bashrc
```

### 1.2 创建虚拟环境
```bash
# 创建名为 annotator 的环境，使用 Python 3.10
conda create -n annotator python=3.10 -y

# 激活环境
conda activate annotator
```

## 2. 安装依赖

### 2.1 安装 PyTorch
根据您的 CUDA 版本选择合适的命令。以下以 CUDA 12.1 为例：
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```
*如需确认服务器 CUDA 版本，请运行 `nvidia-smi`。*

### 2.2 安装 Flash Attention (可选但推荐)
Flash Attention 可以显著提升推理速度并降低显存占用。
```bash
pip install flash-attn --no-build-isolation
```

### 2.3 安装项目依赖
进入项目根目录：
```bash
cd /path/to/Auto-Asset-Annotator

# 安装依赖
pip install -r requirements.txt

# 以编辑模式安装本项目 (方便后续修改代码)
pip install -e .
```

## 3. 模型下载与缓存配置

### 3.1 设置 HuggingFace 镜像 (国内服务器)
如果您在国内服务器，下载 HuggingFace 模型可能较慢，建议设置镜像：
```bash
export HF_ENDPOINT=https://hf-mirror.com
```

### 3.2 设置模型缓存路径
如果您的 `~/.cache` 空间不足，建议指定缓存路径到大容量磁盘：
```bash
export HF_HOME=/data/shared/huggingface
```
*(建议将上述 export 命令添加到 `~/.bashrc` 中)*

### 3.3 预下载模型 (可选)
您可以使用 Python 脚本预先下载模型，避免运行时下载：
```python
from huggingface_hub import snapshot_download
snapshot_download(repo_id="Qwen/Qwen2.5-VL-7B-Instruct")
```

## 4. 验证安装

运行以下命令检查环境是否配置成功：

```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); import auto_asset_annotator; print('Package loaded successfully')"
```

如果输出 `CUDA available: True` 和 `Package loaded successfully`，则说明安装成功。
