# DLC Remote Job Submission / DLC 远程任务提交

本文档只描述当前仓库仍在维护的 DLC 提交流程：

- 本地或 DSW 执行 `scripts/dlc/submit_batch.py`
- 由它调用 `scripts/dlc/launch_job.sh`
- DLC worker 容器执行 `scripts/dlc/run_task.sh`
- 最终运行 `python -m auto_asset_annotator.main`

## 1. 当前调用链

```text
submit_batch.py
  -> launch_job.sh
    -> dlc submit pytorchjob
      -> run_task.sh
        -> python -m auto_asset_annotator.main
```

## 2. 快速开始

### 检查 DLC CLI

```bash
ls -l ./dlc
./dlc get jobs
```

### 提交批量任务

```bash
python scripts/dlc/submit_batch.py --total 4 --name asset_annotation \
    --command_args "--input_dir /path/to/assets --output_dir /path/to/results"
```

### 查看状态

```bash
./dlc get jobs
./dlc get job <job_id>
./dlc logs <job_id>
```

## 3. `submit_batch.py`

位置：`scripts/dlc/submit_batch.py`

职责：

- 校验 `--total`
- 为每个 chunk 组装一次 `bash scripts/dlc/launch_job.sh ...`
- 默认注入数据源 ID
- 对提交失败做最多 3 次指数退避重试

关键参数：

- `--total`: chunk 数量，必填
- `--name`: 任务名前缀，默认 `asset_annotation`
- `--data_sources`: 可选，自定义数据源 ID 列表
- `--command_args`: 传给 `run_task.sh` 的额外参数
- `--max-total`: 安全上限，默认 `100`

## 4. `launch_job.sh`

位置：`scripts/dlc/launch_job.sh`

职责：

- 读取工作空间、资源、镜像、代码根目录等环境变量
- 调用 `dlc submit pytorchjob`
- 把当前 chunk 信息和额外参数传给 `run_task.sh`

当前默认值来自脚本本身：

- `DLC_WORKSPACE_ID=270969`
- `DLC_RESOURCE_ID=quotalplclkpgjgv`
- `DLC_IMAGE=dsw-registry-vpc.cn-beijing.cr.aliyuncs.com/pai-training-algorithm/isaac-sim:isaacsim450-vnc-v8`
- `DLC_CODE_ROOT=/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator`

## 5. `run_task.sh`

位置：`scripts/dlc/run_task.sh`

职责：

- 在容器内查找 `.venv_dlc`，找不到时回退到 `.venv`
- 设置 `PYTHONUNBUFFERED`、`PYTHONPATH`、`MODEL_PATH`
- 支持这些模式：
  - `annotate`
  - `classify`
  - `extract`
  - `custom`
  - 默认的 `<chunk_id> <chunk_total>` 分块模式

当前主线维护的 DLC 提交流程使用的是 **分块模式**，因为 `launch_job.sh` 默认就是按 chunk 调用 `run_task.sh <chunk_id> <chunk_total> ...`。

上面列出的 `annotate`、`classify`、`extract`、`custom` 属于 `run_task.sh` 的直接/手动入口；它们可以单独调用，但不是这里主推的批量提交链路。

## 6. 常用提交示例

### 默认属性提取

```bash
python scripts/dlc/submit_batch.py --total 4 --name annotate_assets \
    --command_args "--input_dir /data/assets --output_dir /data/results"
```

### 指定分类 prompt

```bash
python scripts/dlc/submit_batch.py --total 4 --name classify_assets \
    --command_args "--input_dir /data/assets --output_dir /data/results --prompt_type classify_object_category_prompt"
```

### 基于失败列表重跑

```bash
python scripts/dlc/submit_batch.py --total 4 --name retry_failed \
    --command_args "--input_dir /data/assets --output_dir /data/results --asset_list_file archive/temp_lists/failed_assets.txt --force"
```

### 基于不完整结果重跑

```bash
python scripts/dlc/submit_batch.py --total 4 --name retry_incomplete \
    --command_args "--input_dir /data/assets --output_dir /data/results --retry_incomplete"
```

## 7. 生产使用注意事项

- `python -m auto_asset_annotator.main` 仍然是最终执行入口
- `--command_args` 只是把 CLI 参数透传给主程序
- 当前主线模型选择由 `auto_asset_annotator.main` 读取的 `config` 或 `--model_path` 决定；`run_task.sh` 导出的 `MODEL_PATH` 本身不会自动覆盖 `main.py` 使用的模型
- 当前主线输出是“模型返回 structured text，流水线解析后写 JSON”
- 历史修复列表统一使用 `archive/temp_lists/...` 路径

## 8. 常见问题

### `dlc` 不可执行

```bash
ls -l ./dlc
```

### 容器内找不到虚拟环境

`run_task.sh` 只会找：

- `.venv_dlc`
- `.venv`

因此提交前应先准备至少一个环境。

### 任务提交成功但没有输出

优先检查：

- `--input_dir` 是否正确挂载
- 资产目录下是否真的有图片
- `--output_dir` 是否可写
- 任务日志里是否出现 `No images found` 或模型加载错误

## 9. 边界说明

本页关注的是 **当前 DLC 提交与运行流程**，不是历史迁移叙事。迁移背景保留在变更记录中；这里以现有脚本行为为准。
