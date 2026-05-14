# GRScenes test0 标注前调研记录

**日期**: 2026-05-14
**状态**: 调研完成，尚未执行标注
**目标数据集**: `/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets`

## 结论

目标数据集已经包含每个资产自己的扁平标注文件，但核心标注字段为空。当前仓库的既有 `output/` 结果可以复用一部分，剩余资产应只补跑缺失部分，不建议全量重跑，也不建议直接把标注输出写到目标目录。

推荐流程：

1. 建立临时 staging wrapped output 目录。
2. 将当前仓库 `output/` 中与目标数据集精确匹配的完整结果复制到 staging。
3. 只对目标数据集中缺少既有结果且有图片的资产运行标注，输出也写入 staging。
4. 对 staging 做完整校验。
5. 最后一次性将 staging 结果同步回目标数据集中每个 asset 内部的扁平 `{asset_id}_annotation.json`。

## 数据集现状

目标目录结构是 `category/asset_id` 两层资产目录。

| 项目 | 数量 |
|------|------|
| 类别数 | 79 |
| 二级 asset 目录数 | 53,171 |
| 目标内置 `{asset_id}_annotation.json` 文件数 | 53,171 |
| 扁平 schema 标注文件数 | 53,171 |
| wrapped schema 标注文件数 | 0 |
| invalid JSON 数 | 0 |
| `raw_output` 数 | 0 |
| 至少一个核心字段非空的资产数 | 0 |

所有目标内置标注文件的核心字段当前为空：

| 字段 | 空值数 |
|------|------|
| `description` | 53,171 |
| `material` | 53,171 |
| `dimensions` | 53,171 |
| `mass` | 53,171 |
| `placement` | 53,171 |

图片情况：

| 项目 | 数量 |
|------|------|
| asset 根目录有 `.png/.jpg/.jpeg` 图片 | 53,167 |
| asset 根目录缺图片 | 4 |
| `thumbnails/` 目录 | 0 |

缺图片资产：

```text
cabinet/b98d6ccbeb75dfdeb60e27649a5b055a
other/d41d8cd98f00b204e9800998ecf8427e
person/351316cbb083f9f4df0cccd60cbfa848
person/d41d8cd98f00b204e9800998ecf8427e
```

其中 `person/d41d8cd98f00b204e9800998ecf8427e` 与 `other/d41d8cd98f00b204e9800998ecf8427e` 存在重复 asset id 场景，且 `person/...` 缺图片，不应自动跨类别复用 `other/...` 的结果。

## 与当前仓库输出的覆盖关系

当前仓库 `output/` 中有 52,907 个 wrapped annotation 文件。按目标数据集的 `category/asset_id` 精确匹配：

| 项目 | 数量 |
|------|------|
| 目标 asset 总数 | 53,171 |
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

## 建议执行方案

### 1. 准备 staging

建议使用目标数据集旁边的临时目录，例如：

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_staging/grscenes_wrapped_output
```

staging 保持当前 pipeline 的 wrapped output 格式，便于复用现有校验脚本和 DLC 工作流。

### 2. 复用既有结果

从当前仓库 `output/` 中筛选出与目标数据集 `category/asset_id` 精确匹配、无 `raw_output`、核心字段完整的结果，复制到 staging。

不要默认做 uid fallback。若未来需要 fallback，必须满足：

- 源端和目标端该 asset id 都唯一。
- 源 wrapped key 与源路径一致。
- 类别差异经过人工确认。
- 审计记录明确标出 match mode。

本次调研中可安全 uid fallback 数为 0。

### 3. 只补跑缺失资产

生成 residual asset list，内容必须是相对目标 `--input_dir` 的 `category/asset_id` 路径。

本次应自动补跑的资产范围是 8,269 个有图片、且不在当前 `output/` 的唯一 asset id。`person/d41d8cd98f00b204e9800998ecf8427e` 因缺图片和重复 id 歧义，应单独列为 exception，不进入自动补跑。

### 4. 标注输出仍写入 staging

示例命令形态：

```bash
python -m auto_asset_annotator.main \
  --input_dir /cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets \
  --output_dir /cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_staging/grscenes_wrapped_output \
  --asset_list_file /path/to/residual_assets.txt
```

DLC 执行时也应使用 explicit asset list workflow，不要全量扫描运行。

### 5. 同步回目标扁平 JSON

需要一个 dry-run 默认开启、路径可配置的新同步工具，将 staging wrapped output 填回：

```text
GRScenes_assets/{category}/{asset_id}/{asset_id}_annotation.json
```

同步规则建议：

- 默认只填空字段。
- 非空字段不覆盖，除非显式传入 `--overwrite`。
- 跳过 `raw_output`。
- `placement` 从字符串规范化为目标扁平 JSON 中的列表。
- 输出 JSONL 或 CSV audit manifest，记录 target path、source path、match mode、old values、new values、skip reason。

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

- 全量扫描 53,171 个目标 asset。
- 确认 `description/material/dimensions/mass/placement` 是否仍有空值。
- 输出 exception report，至少包含 4 个缺图片资产和任何补跑失败资产。

## 当前不建议的做法

- 不建议全量重跑 53,171 个资产，因为 44,901 个可以从当前 `output/` 复用。
- 不建议直接将 `--output_dir` 指向目标 `GRScenes_assets`。
- 不建议直接使用现有 `scripts/fill_annotations.py --apply`，因为该脚本目标路径硬编码，且缺少本次所需的完整 preflight、fallback、审计和目标外部路径保护。
- 不建议自动跨类别使用 uid fallback，当前数据中已有重复 id 和类别歧义。
