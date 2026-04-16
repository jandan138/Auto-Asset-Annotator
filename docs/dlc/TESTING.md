# DLC 测试说明

这份说明聚焦当前仍有意义的测试方式：

- 不运行重型全量标注
- 先做脚本级和参数级验证
- 需要实跑时，只对小样本资产执行

## 1. 本地轻量验证

### 查看提交脚本帮助

```bash
python scripts/dlc/submit_batch.py --help
```

### 查看 worker 脚本帮助

```bash
bash scripts/dlc/run_task.sh
```

这两步不会加载模型，但能快速确认脚本入口、参数说明和基本可执行性。

## 2. 本地模拟 worker 命令

如果你需要验证参数拼接是否正确，可以在本地模拟 `run_task.sh` 的几种模式。

### 默认标注模式

```bash
bash scripts/dlc/run_task.sh annotate \
    --input_dir /path/to/test_assets \
    --output_dir ./test_output
```

### 分类模式

```bash
bash scripts/dlc/run_task.sh classify \
    --input_dir /path/to/test_assets \
    --output_dir ./test_output
```

### 分块模式

```bash
bash scripts/dlc/run_task.sh 0 4 \
    --input_dir /path/to/test_assets \
    --output_dir ./test_output
```

注意：这些命令在真正执行时会加载模型，因此只应用在你明确需要小样本验证的时候。

## 3. DLC 提交前检查项

提交前建议至少确认：

1. `./dlc get jobs` 能返回结果
2. `scripts/dlc/launch_job.sh` 使用的 `DLC_CODE_ROOT` 与实际挂载路径一致
3. 代码根目录下存在 `.venv_dlc` 或 `.venv`
4. 如果你要换模型，测试命令里要显式传 `--model_path`，或者确认 `config/config.yaml` 中的 `model.name` 已指向目标模型
5. `run_task.sh` 打印的 `MODEL_PATH` 只代表 shell 环境变量；当前 `main.py` 不会仅凭这个变量自动改用另一套模型
6. `--input_dir` / `--output_dir` 指向 DLC 容器可访问路径

## 4. 小样本 DLC 验证示例

如果你确实需要做一次端到端验证，建议只提交极小 chunk 数和极小资产集：

```bash
python scripts/dlc/submit_batch.py --total 1 --name dlc_smoke_test \
    --command_args "--input_dir /data/test_assets --output_dir /data/test_results"
```

如果需要验证非默认模型，显式把模型路径透传给主程序：

```bash
python scripts/dlc/submit_batch.py --total 1 --name dlc_model_smoke_test \
    --command_args "--input_dir /data/test_assets --output_dir /data/test_results --model_path /path/to/model"
```

或者基于一个明确列表：

```bash
python scripts/dlc/submit_batch.py --total 1 --name dlc_retry_test \
    --command_args "--input_dir /data/assets --output_dir /data/test_results --asset_list_file archive/temp_lists/failed_assets.txt --force"
```

## 5. 建议记录什么

做 DLC 验证时，建议记录：

- 提交命令
- Job ID
- 输入输出路径
- 运行模式（annotate / classify / chunk）
- 日志中的关键状态变化
- 是否成功产出 JSON

## 6. 本页与历史测试报告的关系

历史上某次完整 DLC 迁移验证的具体 Job ID、镜像变更和一次性排障细节，属于历史记录，不再作为当前操作说明的主体。本页只保留对今天仍然有指导意义的测试方式和路径。
