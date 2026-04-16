# 第一章：搭建你的魔法工坊

施法之前，先把工坊搭好。这个项目的主线依赖并不神秘：**Python 3.10+、PyTorch、Transformers、Qwen 的视觉工具链，以及一块能装下模型的 GPU**。

## 1. 核心能量源：GPU

Qwen2.5-VL-7B 不是轻量玩具，加载和推理都需要显卡。

- 你需要一台带 NVIDIA GPU 的机器
- `device_map="auto"` 会尽量帮你把模型放到可用设备上
- `attn_implementation` 当前配置默认是 `eager`，目的是减少对额外 `flash-attn` 依赖的要求

## 2. 准备 Python 环境

你可以用 Conda，也可以用自己习惯的 venv。关键不是宗教，而是把依赖隔离开。

```bash
conda create -n annotator python=3.10 -y
conda activate annotator
```

## 3. 安装工具箱

进入仓库根目录后执行：

```bash
pip install -r requirements.txt
pip install -e .
```

这会安装当前主线依赖，包括：

- `transformers`
- `torch`
- `torchvision`
- `pillow`
- `natsort`
- `tqdm`
- `qwen-vl-utils`
- `pyyaml`
- `accelerate`

## 4. 准备模型

主线配置里的模型路径是：

```text
/cpfs/shared/simulation/zhuzihou/models/Qwen2.5-VL-7B-Instruct
```

第一次部署时，可以用仓库自带脚本准备模型：

```bash
python scripts/download_model.py
```

但请记住：**模型加载是重操作**。如果你只是读文档、修代码或做轻量验证，不要顺手运行标注命令。

## 5. 工坊自检

可以用一个轻量检查确认环境至少能导入包：

```bash
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); import auto_asset_annotator; print('Package loaded successfully')"
```

看到包能导入，说明工坊已经能点火了。下一章，我们准备原材料。
