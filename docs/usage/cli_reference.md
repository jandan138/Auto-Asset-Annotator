# 命令行参考

程序入口为 `python -m auto_asset_annotator.main`。

## 基本用法

```bash
python -m auto_asset_annotator.main [OPTIONS]
```

## 参数列表

| 参数 | 类型 | 说明 |
| :--- | :--- | :--- |
| `--config` | Path | 配置文件路径，默认是 `config/config.yaml`。 |
| `--input_dir` | Path | 覆盖配置中的输入目录。 |
| `--output_dir` | Path | 覆盖配置中的输出目录。 |
| `--model_path` | String | 覆盖配置中的模型路径或模型名。 |
| `--prompt_type` | String | 覆盖配置中的 prompt 类型。 |
| `--asset_list_file` | Path | 使用资产列表文件，而不是扫描整个输入目录。文件内容应为相对 `--input_dir` 的资产路径，通常是 `category/asset_id`。 |
| `--force` | Flag | 即使输出文件已存在，也强制重新标注。 |
| `--retry_incomplete` | Flag | 仅重试 `material`、`dimensions`、`mass`、`placement` 中存在空值的结果。 |
| `--num_chunks` | Int | 总分块数，用于并行任务切片。 |
| `--chunk_index` | Int | 当前作业处理的块索引，从 `0` 开始。 |
| `--model_backend` | String | 显式选择 `local_hf` 或 `openai_compatible`。 |
| `--api_base_url` | String | `openai_compatible` 后端的 API base URL。 |
| `--api_key_env` | String | `openai_compatible` 后端读取 API key 的环境变量名。 |

## 常见命令

### 默认标注

```bash
python -m auto_asset_annotator.main --input_dir ./data --output_dir ./output
```

### 指定 prompt 类型

```bash
python -m auto_asset_annotator.main \
  --prompt_type classify_object_category_prompt \
  --input_dir ./data \
  --output_dir ./output_categories
```

### 使用资产列表文件

```bash
python -m auto_asset_annotator.main \
  --input_dir /path/to/assets \
  --asset_list_file archive/temp_lists/failed_assets.txt \
  --output_dir ./output
```

### 强制重跑

```bash
python -m auto_asset_annotator.main \
  --input_dir ./data \
  --output_dir ./output \
  --force
```

### 仅重试物理属性不完整的资产

```bash
python -m auto_asset_annotator.main \
  --input_dir ./data \
  --output_dir ./output \
  --retry_incomplete
```

### 分块并行处理

```bash
python -m auto_asset_annotator.main --num_chunks 4 --chunk_index 0
python -m auto_asset_annotator.main --num_chunks 4 --chunk_index 1
python -m auto_asset_annotator.main --num_chunks 4 --chunk_index 2
python -m auto_asset_annotator.main --num_chunks 4 --chunk_index 3
```

在 DLC 中，维护中的批量调用链会把这些参数组装为：

```bash
python -m auto_asset_annotator.main --num_chunks <total> --chunk_index <index> [other flags...]
```

常见 DLC 重跑标志仍然是普通 CLI 参数：

```bash
python -m auto_asset_annotator.main \
  --input_dir /data/assets \
  --output_dir /data/results \
  --asset_list_file archive/temp_lists/failed_assets.txt \
  --force

python -m auto_asset_annotator.main \
  --input_dir /data/assets \
  --output_dir /data/results \
  --retry_incomplete
```

运维侧优先使用 `scripts/dlc/submit_annotate.sh`、`scripts/dlc/submit_retry_failed.sh`、`scripts/dlc/submit_retry_incomplete.sh`、`scripts/dlc/submit_asset_list.sh`，而不是手写 `--command_args`。

## 行为说明

- 如果输出文件不存在，资产会被处理。
- 如果输出文件包含 `raw_output`，资产会在后续运行时自动重试。
- 如果指定 `--retry_incomplete`，则会检查 `material`、`dimensions`、`mass`、`placement` 是否为空并按需重试。
- JSON 文件由程序解析 structured text 后写入，不是直接透传模型返回的 JSON。
