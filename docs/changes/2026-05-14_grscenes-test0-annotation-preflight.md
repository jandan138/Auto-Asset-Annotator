# GRScenes test0 标注前调研记录

**日期**: 2026-05-14
**状态**: 调研完成；后续 Gemma4 全量 DLC 重标注已完成，并已通过受控同步工具写回目标数据集 metadata
**目标数据集**: `/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets`

## 结论

目标数据集已经包含每个资产自己的扁平标注文件，但核心标注字段为空。旧仓库 `output/` 中的 Qwen 小模型结果质量不足，当前决策是使用 Gemma4 对目标数据集做全量重新标注，同时保留旧输出用于对比。

推荐流程执行结果：

1. 已生成显式 `category/asset_id` 全量 asset list，共 `53,167` 条。
2. 已使用 `scripts/dlc/submit_gemma4_reannotate.sh --dry-run` 校验 DLC worker command。
3. 已完成单资产真实 DLC probe，确认 worker runtime、日志和 JSON 输出。
4. 已完成小批量多类别 probe。
5. 已完成全量 DLC run，输出写入新的 `annotation_runs/20260515T015209Z_gemma4_full_v1/output`。
6. 已使用 `scripts/sync_grscenes_annotations.py` 将语义字段同步回 `GRScenes_assets/{category}/{asset_id}/{asset_id}_annotation.json`，并在 run 目录下保存 backup/audit。

当前结果摘要：

```text
DLC chunks: 64 Succeeded, 0 Failed
Gemma4 output JSON: 53,167
Dataset target JSON: 53,167
Post-sync bad_json: 0
Post-sync uid_or_category_mismatch: 0
Post-sync empty description/material/dimensions/mass/placement: 0
Backup files: 53,167
```

## 数据集现状

目标目录结构是 `category/asset_id` 两层资产目录。

| 项目 | 数量 |
|------|------|
| 类别数 | 79 |
| 二级 asset 目录数 | 53,167 |
| 目标内置 `{asset_id}_annotation.json` 文件数 | 53,167 |
| 扁平 schema 标注文件数 | 53,167 |
| wrapped schema 标注文件数 | 0 |
| invalid JSON 数 | 0 |
| `raw_output` 数 | 0 |
| 至少一个核心字段非空的资产数 | 0 |

2026-05-14 调研时，所有目标内置标注文件的核心字段为空：

| 字段 | 空值数 |
|------|------|
| `description` | 53,167 |
| `material` | 53,167 |
| `dimensions` | 53,167 |
| `mass` | 53,167 |
| `placement` | 53,167 |

图片情况：

| 项目 | 数量 |
|------|------|
| asset 根目录有 `.png/.jpg/.jpeg` 图片 | 53,167 |
| asset 根目录缺图片 | 0 |
| `thumbnails/` 目录 | 0 |

2026-05-14 复核结果：当前目标目录内 `53,167` 个资产均存在精确的 `front.png / left.png / back.png / right.png` 四视角图；未发现需要依赖 `0.png/1.png/2.png/3.png` fallback 的资产。早期记录中的 4 个缺图资产当前已不在目标目录内。

## 与当前仓库输出的覆盖关系

当前仓库 `output/` 中有 52,907 个 wrapped annotation 文件。按目标数据集的 `category/asset_id` 精确匹配：

| 项目 | 数量 |
|------|------|
| 目标 asset 总数 | 53,167 |
| 与当前 `output/` 精确匹配 | 44,901 |
| 精确匹配缺失 | 8,270 |

按纯 asset id 统计：

| 项目 | 数量 |
|------|------|
| 目标唯一 asset id | 53,168 |
| 当前 `output/` 唯一 asset id | 52,905 |
| 共同唯一 asset id | 44,899 |
| 目标中不存在于当前 `output/` 的唯一 asset id | 8,269 |
| 当前 `output/` 中不在目标数据集的唯一 asset id | 8,006 |
| 共同 id 但类别集合不一致 | 1 |

边界判断：

| 项目 | 数量 |
|------|------|
| 精确匹配可作为首选复用候选 | 44,901 |
| 精确缺失路径 | 8,270 |
| 可安全 uid fallback 的路径 | 0 |
| uid 不存在于当前 `output/` 的路径 | 8,269 |
| 重复/歧义路径 | 1 |

因此 residual list 应使用 `category/asset_id` 路径，而不是裸 asset id。

## 为什么不能直接原地跑

当前主流程输出约定是：

```text
{output_dir}/{category}/{asset_id}_annotation.json
```

目标数据集需要填充的位置是：

```text
GRScenes_assets/{category}/{asset_id}/{asset_id}_annotation.json
```

两者目录层级不同。直接将 `--output_dir` 指到 `GRScenes_assets` 会把文件写到错误位置，不能直接填回每个 asset 内部的扁平标注文件。

另外，`--retry_incomplete` 只检查 `--output_dir` 中已有的 wrapped output 文件，不会检查目标数据集内部的扁平 JSON。因此目标目录里虽然字段全空，但不能靠直接指定 `--retry_incomplete` 自动识别。

## Gemma4 全量重标建议执行方案

### 1. 生成显式全量 asset list

不要依赖默认扫描代表“每个目录”。当前 `list_assets()` 与二级目录全集一致，但全量生产仍应固定使用显式 list：

```bash
DATA_ROOT=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets
RUN_ID=$(date -u +%Y%m%dT%H%M%SZ)_gemma4_full_v1
RUN_ROOT=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/$RUN_ID
mkdir -p "$RUN_ROOT/input" "$RUN_ROOT/output" "$RUN_ROOT/logs" "$RUN_ROOT/cache"
find "$DATA_ROOT" -mindepth 2 -maxdepth 2 -type d -printf '%P\n' | LC_ALL=C sort > "$RUN_ROOT/input/all_assets.txt"
wc -l "$RUN_ROOT/input/all_assets.txt"
head "$RUN_ROOT/input/all_assets.txt"
tail "$RUN_ROOT/input/all_assets.txt"
```

期望行数：`53,167`。

### 2. 只读校验四视角图

```bash
while read -r rel; do
  for view in front.png left.png back.png right.png; do
    test -f "$DATA_ROOT/$rel/$view" || echo "$rel missing $view"
  done
done < "$RUN_ROOT/input/all_assets.txt"
```

当前复核结果为空输出，即没有缺图资产。

### 3. DLC dry-run

```bash
RUN_ID=$RUN_ID \
ASSET_LIST_FILE="$RUN_ROOT/input/all_assets.txt" \
TOTAL=64 NAME=gemma4_grscenes_full_v1 \
bash scripts/dlc/submit_gemma4_reannotate.sh --dry-run
```

全量建议 `TOTAL=64`，约 `831` assets/chunk；如果更重视失败重试粒度且 quota 允许，可用 `TOTAL=96`，约 `554` assets/chunk。保持 `TOTAL <= 100`，避免触发 `submit_batch.py` 默认安全上限。

### 4. 单资产真实 probe

全量提交前必须先用一个资产列表跑真实 DLC probe：

```bash
printf '%s\n' 'basket/6c68230d67112b1dfd2bd7fa9322c756' > "$RUN_ROOT/input/one_asset.txt"
DLC_WORKSPACE_ID=270969 \
DLC_RESOURCE_ID=quota1r947pmazvk \
RUN_ID=${RUN_ID}_probe \
ASSET_LIST_FILE="$RUN_ROOT/input/one_asset.txt" \
TOTAL=1 NAME=gemma4_grscenes_probe \
bash scripts/dlc/submit_gemma4_reannotate.sh --submit
```

### 5. 同步回目标扁平 JSON（已完成）

已新增 dry-run 默认开启、路径可配置的同步工具，将 staging wrapped output 填回：

```text
GRScenes_assets/{category}/{asset_id}/{asset_id}_annotation.json
```

同步规则建议：

- 默认只填空字段。
- 非空字段不覆盖，除非显式传入 `--overwrite`。
- 跳过 `raw_output`。
- `placement` 从字符串规范化为目标扁平 JSON 中的列表。
- 输出 JSONL audit manifest，记录 target path、source path、old values、new values、skip reason。

实际同步记录：

```text
RUN_ROOT=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T015209Z_gemma4_full_v1
SOURCE=$RUN_ROOT/output
TARGET=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets
BACKUP=$RUN_ROOT/backups/dataset_annotations_before_sync_20260515T085255Z
DRY_RUN_AUDIT=$RUN_ROOT/logs/sync_dry_run_audit.jsonl
APPLY_AUDIT=$RUN_ROOT/logs/sync_apply_audit.jsonl
APPLY_SUMMARY=$RUN_ROOT/logs/sync_apply_summary.json
```

## 必要校验

执行任何写入前：

- 目标路径、category、uid 一致性检查。
- 目标 JSON 可解析性检查。
- 重复 uid map。
- 源 wrapped key 与源路径一致性检查。
- 源 `raw_output`、空字段、dimensions/mass 格式检查。
- exact / missing / exception 的类别分布。

补跑标注后：

- expected residual list 与 staging 产物做 left-join。
- 检查缺失输出文件。
- 检查 `raw_output`。
- 检查空核心字段。
- 检查 dimensions/mass 格式。
- 检查 placement 可转换为目标列表格式。

最终同步后：

- 全量扫描 53,167 个目标 asset。
- 确认 `description/material/dimensions/mass/placement` 是否仍有空值。
- 输出 exception report，包含任何补跑失败资产或后续新增缺图资产。

## 当前不建议的做法

- 不建议把 Gemma4 全量重标输出写入旧 `output/`、`output_reannotate/` 或数据集原目录；应使用 `annotation_runs/<run_id>/output`。
- 不建议直接将 `--output_dir` 指向目标 `GRScenes_assets`。
- 不建议直接使用旧 `scripts/fill_annotations.py --apply`，因为该脚本目标路径硬编码。当前应使用 `scripts/sync_grscenes_annotations.py`。
- 不建议自动跨类别使用 uid fallback，当前数据中已有重复 id 和类别歧义。
