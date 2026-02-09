# 命令行参考手册 (CLI Reference)

`auto_asset_annotator.main` 是程序的入口点。所有配置文件的参数都可以通过命令行参数进行覆盖。

## 基本用法

```bash
python -m auto_asset_annotator.main [OPTIONS]
```

## 参数列表

| 参数 | 缩写 | 类型 | 默认值 | 说明 |
| :--- | :--- | :--- | :--- | :--- |
| `--config` | 无 | Path | `config/config.yaml` | 指定配置文件路径。 |
| `--input_dir` | 无 | Path | (from config) | 覆盖配置文件中的输入目录。 |
| `--output_dir` | 无 | Path | (from config) | 覆盖配置文件中的输出目录。 |
| `--model_path` | 无 | Str | (from config) | 覆盖模型路径或名称。 |
| `--prompt_type` | 无 | Str | (from config) | 指定本次运行的任务类型 (如 `classify_object_category_prompt`)。 |
| `--num_chunks` | 无 | Int | 1 | 将总任务划分为 N 个块 (用于并行计算)。 |
| `--chunk_index` | 无 | Int | 0 | 当前进程只处理第 K 个块 (从 0 开始)。 |

## 常见使用场景

### 1. 简单运行
```bash
python -m auto_asset_annotator.main --input_dir /data/assets --output_dir /data/results
```

### 2. 切换任务类型
只进行分类，不生成详细属性：
```bash
python -m auto_asset_annotator.main \
    --prompt_type classify_object_category_prompt \
    --input_dir /data/assets \
    --output_dir /data/results/categories
```

### 3. 分布式并行处理 (Slurm/Kubernetes)
假设你有 100 万个资产，想用 4 台机器并行处理。

**机器 1 (处理 0-25%):**
```bash
python -m auto_asset_annotator.main --num_chunks 4 --chunk_index 0
```

**机器 2 (处理 25-50%):**
```bash
python -m auto_asset_annotator.main --num_chunks 4 --chunk_index 1
```

**机器 3 (处理 50-75%):**
```bash
python -m auto_asset_annotator.main --num_chunks 4 --chunk_index 2
```

**机器 4 (处理 75-100%):**
```bash
python -m auto_asset_annotator.main --num_chunks 4 --chunk_index 3
```
