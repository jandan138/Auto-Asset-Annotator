# 硬件与软件依赖

在部署 **Auto-Asset-Annotator** 前，请先确认运行环境满足当前项目的基础要求。

## 软件要求

- 操作系统：Linux 为主要运行环境。
- Python：`>=3.10`
- `pip`：用于安装 `requirements.txt` 和项目本身。
- 可用的 PyTorch 运行环境：CPU 可用于验证安装，GPU 更适合实际推理。

`pyproject.toml` 当前声明的 Python 要求为 `>=3.10`，安装和文档应以此为准。

## Python 依赖

当前安装面与 `pyproject.toml` 对齐，核心依赖包括：

- `transformers`
- `torch`
- `torchvision`
- `pillow`
- `natsort`
- `tqdm`
- `qwen-vl-utils`
- `pyyaml`
- `accelerate`

标准安装命令见 `docs/installation/linux_deployment.md`。

## 硬件建议

- GPU：推荐 NVIDIA GPU。实际显存需求取决于所用 Qwen2.5-VL 模型规模。
- CPU：建议至少 8 核，用于数据扫描与图像处理。
- 内存：建议 32GB 或更高。
- 存储：需要为 Python 环境、模型权重和输出结果预留足够空间。

## 说明

- 本项目默认配置指向本地模型路径，生产使用通常应在有 GPU 的 Linux 服务器上进行。
- 仅做安装验证时，可以先执行轻量导入检查，而不要立即运行完整标注任务。
