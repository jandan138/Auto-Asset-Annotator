# Linux 服务器部署指南

本文档描述标准 Linux 安装流程，并将模型下载与环境变量配置单独列出，避免和基础安装步骤混在一起。

## 1. 创建 Python 环境

可使用 `venv`、Conda 或其他环境管理工具。下面以 Conda 为例：

```bash
conda create -n annotator python=3.10 -y
conda activate annotator
```

## 2. 安装项目

进入仓库根目录后执行：

```bash
pip install -r requirements.txt
pip install -e .
```

这两步分别安装运行依赖和当前项目包本身。

## 3. 验证安装

```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); import auto_asset_annotator; print('Package loaded successfully')"
```

如果输出中出现 `Package loaded successfully`，说明包已可导入。

## 4. 模型下载

标准安装完成后，如需预下载模型，可运行：

```bash
python scripts/download_model.py
```

这一步与基础 Python 安装分离，便于先完成环境配置再准备模型权重。

## 5. 环境变量与缓存说明

如需使用镜像或自定义缓存目录，可在运行前设置环境变量：

```bash
export HF_ENDPOINT=https://hf-mirror.com
export HF_HOME=/data/shared/huggingface
```

这些变量属于运行环境配置，不是标准安装步骤的一部分。

## 6. 注意事项

- 不要把模型下载步骤和基础依赖安装混为一步，便于排查问题。
- 如需启用其他注意力实现，需同时确认对应依赖和运行环境可用。
- 文档中的安装命令不会触发模型加载；真正加载模型发生在执行标注命令时。
