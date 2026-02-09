# Auto-Asset-Annotator (3D 资产自动标注工具)

[English](./README_EN.md) | **中文**

基于 **Qwen-VL** 多模态大模型构建的自动化 3D 资产标注流水线。该工具能够批量处理 3D 资产渲染图，自动生成属性描述、分类标签、材质分析等结构化数据。

---

## 📚 文档目录

我们提供了详尽的中文文档，帮助您在 Linux 服务器上快速部署和使用。

### 1. [项目介绍 (Introduction)](docs/introduction/overview.md)
*   [项目概览与架构](docs/introduction/overview.md)
*   [功能特性与 Prompt 类型](docs/introduction/features.md)

### 2. [安装部署 (Installation)](docs/installation/linux_deployment.md)
*   [硬件与软件依赖](docs/installation/requirements.md)
*   [Linux 服务器部署指南 (Conda/Pip)](docs/installation/linux_deployment.md) **(推荐阅读)**

### 3. [使用指南 (Usage)](docs/usage/quick_start.md)
*   [快速开始](docs/usage/quick_start.md)
*   [数据准备与目录规范](docs/usage/data_preparation.md)
*   [配置文件详解 (config.yaml)](docs/usage/configuration.md)
*   [命令行参数手册 (CLI)](docs/usage/cli_reference.md)

### 4. [开发与扩展 (Development)](docs/development/project_structure.md)
*   [源码结构解析](docs/development/project_structure.md)
*   [如何添加自定义 Prompt](docs/development/custom_prompts.md)
*   [如何适配新模型](docs/development/extending_models.md)

### 5. [常见问题 (Troubleshooting)](docs/troubleshooting/common_issues.md)
*   [显存不足 (OOM)、路径错误等解决方案](docs/troubleshooting/common_issues.md)

---

## 🚀 极速上手

### 安装
```bash
pip install -r requirements.txt
pip install -e .
```

### 运行
```bash
python -m auto_asset_annotator.main \
    --input_dir /path/to/assets \
    --output_dir /path/to/results
```

## 许可证
本项目采用 MIT License。
