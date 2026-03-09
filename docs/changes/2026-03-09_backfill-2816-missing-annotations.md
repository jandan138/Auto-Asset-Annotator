# 补标注 2,816 个缺失资产

**日期**: 2026-03-09
**状态**: 已完成

## 问题发现

目标目录 `GRScenes_assets` 包含 52,907 个资产，但标注输出目录仅有 50,091 个标注文件，差异 **2,816** 个。

## 根因分析

| 项目 | 详情 |
|------|------|
| 标注完成时间 | 2026-02-28 ~ 2026-03-06 |
| 缺失资产图片创建时间 | **2026-03-08** |
| 根因 | 这 2,816 个资产在标注完成后才被添加到 GRScenes_assets |

标注流程本身无 bug，`list_assets()` 能正确发现所有资产。纯粹是时间差问题。

## 缺失资产分布

| 类别 | 缺失数 | 目标总数 | 已标注数 |
|------|--------|----------|----------|
| wall | 1,461 | 15,961 | 14,500 |
| ground | 1,079 | 10,107 | 9,028 |
| other | 162 | 12,210 | 12,048 |
| ceiling | 51 | 1,610 | 1,559 |
| column | 29 | 401 | 372 |
| plate | 14 | 426 | 412 |
| tray | 3 | 44 | 41 |
| pillow | 3 | 651 | 648 |
| threshold | 2 | 53 | 51 |
| person | 2 | 107 | 105 |
| mirror | 2 | 72 | 70 |
| bottle | 1 | 1,698 | 1,697 |
| cabinet | 1 | 1,278 | 1,277 |
| chair | 1 | 227 | 226 |
| cup | 1 | 549 | 548 |
| decoration | 1 | 377 | 376 |
| electric_cooker | 1 | 26 | 25 |
| picture | 1 | 273 | 272 |
| table | 1 | 211 | 210 |

## 解决方案

资产列表文件：`scripts/missing_assets_20260309.txt`（2,816 行，每行一个 category/asset_uuid）

### 方案A：DLC 分布式（推荐，4 workers）

```bash
cd /cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator

python scripts/dlc/submit_batch.py --total 4 --name backfill_2816 \
    --command_args "--input_dir /cpfs/shared/simulation/zhuzihou/dev/usd-scene-physics-prep/GRScenes-test1/GRScenes_assets --output_dir /cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/output --asset_list_file /cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/scripts/missing_assets_20260309.txt"
```

每个 worker 处理约 704 个资产。DLC 会自动传入 `--num_chunks 4 --chunk_index N`。

### 方案B：单机运行

```bash
cd /cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator

python -m auto_asset_annotator.main \
    --input_dir /cpfs/shared/simulation/zhuzihou/dev/usd-scene-physics-prep/GRScenes-test1/GRScenes_assets \
    --output_dir ./output \
    --asset_list_file scripts/missing_assets_20260309.txt
```

### 注意事项

- `--asset_list_file` 路径在 DLC 方案中必须使用**绝对路径**（容器内工作目录为 CODE_ROOT）
- 无需 `--force` 参数，因为这些资产没有已有输出文件
- prompt_type 使用默认的 `extract_object_attributes_prompt`

## 验证计划

补标注完成后执行：

```bash
# 1. 确认总输出文件数达到 52,907
find output/ -name "*_annotation.json" | wc -l

# 2. 确认无 raw_output 失败文件
python scripts/find_failed_assets.py --output_dir ./output

# 3. 按重点类别复核
for cat in wall ground other ceiling column; do
  count=$(find output/$cat -name '*_annotation.json' | wc -l)
  echo "$cat: $count"
done
# 预期: wall=15961, ground=10107, other=12210, ceiling=1610, column=401
```

## DLC 任务执行结果

| Job ID | Display Name | 状态 | 耗时 (秒) |
|--------|-------------|------|-----------|
| dlc46svt571lx0yi | backfill_2816_0_4 (chunk 0) | Succeeded | 4,539 |
| dlc4qs2kpbgat4ov | backfill_2816_1_4 (chunk 1) | Succeeded | 3,903 |
| dlc50rnyhxp8z9ju | backfill_2816_2_4 (chunk 2) | Succeeded | 3,510 |
| dlc5ar9c91grt6xu | backfill_2816_3_4 (chunk 3) | Succeeded | 3,502 |

4 个 DLC 任务全部成功完成。

## 验证结果

### 总标注文件数

- **实际**: 52,907
- **预期**: 52,907
- **结果**: PASS

### 缺失列表检查

- 缺失列表总数: 2,816
- 仍然缺失 (无文件): **0**
- 含 `raw_output` (解析失败): **1**
  - `mirror/04dabe7c98a5f0b15d7aa62ce7b52547` -- 模型返回了垃圾输出（大量重复换行符）

### 全局失败检查

- 整个输出目录中失败资产总数: **1**（即上述 mirror 资产）

### 重点类别数量验证

| 类别 | 实际数量 | 预期数量 | 结果 |
|------|---------|---------|------|
| wall | 15,961 | 15,961 | PASS |
| ground | 10,107 | 10,107 | PASS |
| other | 12,210 | 12,210 | PASS |
| ceiling | 1,610 | 1,610 | PASS |
| column | 401 | 401 | PASS |

### 最终统计

- 2,816 个缺失资产中 2,815 个成功标注（**99.96%**）
- 整体数据集: 52,907 个标注文件，52,906 个有效，1 个含 `raw_output`
- 整体成功率: **99.998%**

## 时间线

| 时间 | 事件 |
|------|------|
| 2026-02-28 ~ 03-06 | 首次标注完成（50,091 个） |
| 2026-03-08 | 2,816 个新资产图片添加到 GRScenes_assets |
| 2026-03-09 | 发现差异 → 调研根因 → 生成缺失列表 → 提交 DLC 补标注 |
| 2026-03-09 | 4 个 DLC 任务全部完成，验证通过 |

## 下一步

1. 单个失败资产 `mirror/04dabe7c98a5f0b15d7aa62ce7b52547` 可单独重试，但该资产图片可能本身有问题导致模型产生垃圾输出
2. 如果 52,906/52,907 (99.998%) 的成功率可接受，可运行 `fill_annotations.py` 将标注填充到目标目录
