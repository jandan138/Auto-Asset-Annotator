# 输出格式与 Schema 说明

本页说明 Auto-Asset-Annotator 当前写出的 JSON 格式，以及它和 GRScenes 原始资产 metadata 的差异。

## 当前 Auto-Asset 输出格式

属性抽取默认使用 `extract_object_attributes_prompt`。模型不会直接输出最终 JSON；模型先返回带标题的 structured text，`AnnotationPipeline` 再解析并归一化字段，最后由 `main.py` 写 JSON。

文件路径：

```text
{output_dir}/{category}/{asset_id}_annotation.json
```

JSON 顶层结构：

```json
{
  "category/asset_id": {
    "category": "category",
    "description": "object description",
    "material": "material description",
    "dimensions": "length * width * height",
    "mass": "mass",
    "placement": "OnTable"
  }
}
```

示例：

```json
{
  "basket/040600389fdab577a5376c28e6c5eb15": {
    "category": "basket",
    "description": "The object is a red plastic shopping basket with a hexagonal pattern on its sides and bottom.",
    "material": "The main material is red plastic covering the entire basket. The handles are made of black plastic.",
    "dimensions": "0.30 * 0.30 * 0.15",
    "mass": "0.2",
    "placement": "OnTable"
  }
}
```

## 字段含义

| 字段 | 类型 | 来源 | 说明 |
| --- | --- | --- | --- |
| `category` | string | 输出路径/资产相对路径 | pipeline 会用输入目录下第一层类别覆盖模型返回的 category。 |
| `description` | string | 模型 structured text | 物体外观、形状、颜色、状态、用途等描述。 |
| `material` | string | 模型 structured text | 材质描述，通常包含部件和材质对应关系。 |
| `dimensions` | string | 模型 structured text + normalize | 当前保存为字符串，格式通常是 `L * W * H`，不含单位。 |
| `mass` | string | 模型 structured text + normalize | 当前保存为字符串，通常是不含单位的 kg 估计值。 |
| `placement` | string | 模型 structured text | 当前保存为字符串，例如 `OnTable` 或 `OnTable, OnFloor`。 |

## 顶层 key 规则

当使用 `--asset_list_file` 时，列表里的每一行应是相对 `--input_dir` 的资产路径，例如：

```text
basket/6c68230d67112b1dfd2bd7fa9322c756
```

输出 JSON 顶层 key 会保留这条相对路径：

```json
{
  "basket/6c68230d67112b1dfd2bd7fa9322c756": {
    "category": "basket"
  }
}
```

这和仓库现有 `./output/...` 结果一致。

## 失败输出格式

如果模型返回文本无法被 parser 解析，pipeline 会保存 raw text：

```json
{
  "category/asset_id": {
    "raw_output": "unparsed model output text..."
  }
}
```

后续再次运行同一输出目录时，`main.py` 会识别这种 previously failed output，并自动重试该资产。重跑时仍要确保该资产在当前扫描范围内：要么它仍存在于 `--input_dir` 的遍历结果里，要么它被显式写入当前 `--asset_list_file`。

## 与 GRScenes 原始 metadata 的差异

GRScenes 原始资产目录中的 annotation 文件通常不是 Auto-Asset 输出格式。它更像资产 metadata：

```json
{
  "uid": "6c68230d67112b1dfd2bd7fa9322c756",
  "category": "basket",
  "description": "",
  "material": "",
  "dimensions": "",
  "mass": "",
  "placement": [],
  "asset_type": "rigid",
  "glb_size": null,
  "usd_size": 6.062491416931152,
  "urdf_size": null,
  "orientation": 0,
  "usd_material_softlink": true
}
```

关键差异：

| 项目 | Auto-Asset 输出 | GRScenes 原始 metadata |
| --- | --- | --- |
| 顶层结构 | `{ "category/asset_id": {...} }` | 直接对象 `{...}` |
| `uid` | 不写入 | 必有 |
| `asset_type` / size / orientation | 不写入 | 保留资产结构信息 |
| `placement` | string | list |
| 目标用途 | 标注结果输出 | 数据集资产 metadata |

因此，Auto-Asset 输出不能无脑覆盖 GRScenes 原始 annotation。若需要回填，应做显式转换和合并。

## 回填 GRScenes metadata 的建议规则

如果后续需要把 Auto-Asset 结果合并回 GRScenes 原始 metadata，建议采用保守策略：

1. 读取原始 metadata。
2. 读取 Auto-Asset 输出中唯一顶层 key 的 value。
3. 只更新语义字段：`description`、`material`、`dimensions`、`mass`、`placement`。
4. 保留原始结构字段：`uid`、`asset_type`、`glb_size`、`usd_size`、`urdf_size`、`orientation`、`usd_material_softlink`。
5. 将 `placement` 从字符串拆成 list，例如 `"OnTable, OnFloor"` -> `["OnTable", "OnFloor"]`。
6. 先运行 dry-run 并保存 audit manifest。
7. 写入数据集前在数据集外保存原始目标 JSON 备份。
8. 抽样人工检查后，再决定是否覆盖数据集原文件。

当前受控同步工具：

```bash
python scripts/sync_grscenes_annotations.py \
  --source-dir /path/to/annotation_runs/<run_id>/output \
  --target-dir /path/to/dataset/GRScenes_assets \
  --audit-jsonl /path/to/annotation_runs/<run_id>/logs/sync_dry_run_audit.jsonl
```

真实写入时必须显式加 `--apply` 并提供数据集外部备份目录：

```bash
python scripts/sync_grscenes_annotations.py \
  --source-dir /path/to/annotation_runs/<run_id>/output \
  --target-dir /path/to/dataset/GRScenes_assets \
  --audit-jsonl /path/to/annotation_runs/<run_id>/logs/sync_apply_audit.jsonl \
  --summary-json /path/to/annotation_runs/<run_id>/logs/sync_apply_summary.json \
  --backup-dir /path/to/annotation_runs/<run_id>/backups/dataset_annotations_before_sync \
  --apply
```

默认策略是只填空字段，不覆盖非空字段。需要覆盖非空字段时必须额外传 `--overwrite`。
脚本会拒绝位于 `--target-dir` 内部的 `--backup-dir`，也会拒绝复用已存在的 backup 目标文件，避免误把旧备份当成本次写入前备份。

如果不直接写入数据集，也可以生成同 schema 的 staging 目录用于人工审查：

```text
/cpfs/user/zhuzihou/tmp/auto_asset_annotator_backfill/{run_id}/GRScenes_assets/{category}/{asset_id}/{asset_id}_annotation.json
```

不要把未审查的模型输出直接写回：

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/.../dataset/GRScenes_assets
```

## Gemma4 smoke 输出是否一致

Gemma4 单资产 smoke 的实际输出：

```json
{
  "basket/6c68230d67112b1dfd2bd7fa9322c756": {
    "category": "basket",
    "description": "This is a woven basket with a natural, light brown color and a textured surface created by the interwoven strands. It features a sturdy handle attached to the rim, allowing it to be carried. The basket has a generally rounded or cylindrical shape, and its construction suggests it is designed for storage or carrying items. The weave pattern is consistent across the body, giving it a rustic and handcrafted appearance.",
    "material": "Woven natural fiber (likely wicker or reed) for the entire body and handle.",
    "dimensions": "0.4 * 0.3 * 0.2",
    "mass": "1.5",
    "placement": "OnFloor"
  }
}
```

这个格式与仓库现有 `./output/basket/..._annotation.json` 一致，但不等于 GRScenes 原始 metadata schema。

## 下游消费建议

如果下游只消费 Auto-Asset 输出目录：

- 读取顶层唯一 key。
- 使用 value 中的六个语义字段。
- 将 `dimensions` 和 `mass` 当字符串解析，而不是假设已经是 float。
- 将 `placement` 视为逗号分隔候选字符串。

如果下游消费 GRScenes 数据集目录：

- 先明确是否需要原始 metadata 字段。
- 如果需要，先做 schema merge。
- 保留原始文件或生成备份。
- 不要把 Auto-Asset 输出目录和 GRScenes dataset 目录混用。
