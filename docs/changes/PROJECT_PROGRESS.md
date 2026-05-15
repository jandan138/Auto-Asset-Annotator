# Auto-Asset-Annotator 项目进度总览

**最后更新**: 2026-05-15

> 历史记录：主体内容是 2026-03-09 阶段收尾时写下的项目里程碑总览。
>
> 当前相关性：用于回顾 2026-03-05 至 2026-03-09 的修复、补标注与字段补全时间线。当前 Gemma4 / DLC 重标注状态见本页顶部“2026-05-15 当前状态”。

## 2026-05-15 当前状态

已对以下数据集完成 Gemma4 全量重新标注，并已把语义字段同步回目标数据集 metadata。旧 Qwen 小模型输出仍保留做对比，不作为本轮生产结果直接复用：

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets
```

关键事实：

| 项目 | 状态 |
|------|------|
| 当前资产数 | 53,167 |
| 缺四视角图资产 | 0 |
| Gemma4 本地单资产 smoke | 已通过 |
| DLC Gemma4 wrapper dry-run | 已通过 |
| 真实 DLC 单资产 probe | v3 已成功 |
| 多类别 DLC probe | 已成功，8 个资产 |
| 全量真实 DLC run | 已完成，64/64 Succeeded |
| Gemma4 新输出根 | `/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T015209Z_gemma4_full_v1/output` |
| Dataset metadata sync | 已完成，53,167/53,167 更新 |
| Dataset 后验验证 | bad_json=0，uid/category mismatch=0，五个语义字段空值=0 |
| Dataset sync backup | `/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs/20260515T015209Z_gemma4_full_v1/backups/dataset_annotations_before_sync_20260515T085255Z` |

当前规范文档：

| 文档 | 内容 |
|------|------|
| `2026-05-14_gemma4_dlc_reannotation_status.md` | 当前状态、下一步 probe/full-run 命令、已验证证据 |
| `2026-05-14_dlc_gemma4_worker_runtime.md` | DLC worker runtime 接入记录和安全门 |
| `2026-05-14_grscenes-test0-annotation-preflight.md` | GRScenes test0 数据集预检、资产数、输出隔离策略、最终同步结果 |
| `../dlc/README.md` | DLC 操作手册 |
| `../usage/gemma4_local_smoke.md` | Gemma4 本地 smoke 和 DLC 批量入口 |
| `../usage/output_schema.md` | Auto-Asset wrapped output 与 GRScenes metadata 的 schema merge/sync 规则 |

## 最终状态

**52,907 个资产，5 个字段全部 100% 填充完成。**

| 字段 | 完成数 | 完成率 |
|------|--------|--------|
| description | 52,907 | 100% |
| material | 52,907 | 100% |
| dimensions | 52,907 | 100% |
| mass | 52,907 | 100% |
| placement | 52,907 | 100% |

---

## 时间线

### 第一阶段：初始标注（~03-04）

- 使用 Qwen2.5-VL-7B-Instruct 对 50,091 个资产进行 VLM 标注
- 通过 DLC 分布式提交多 GPU 并行处理
- 产出 5 个字段的结构化标注

### 第二阶段：失败修复（03-05）

解决 VLM 输出解析失败的问题。

| 文档 | 内容 |
|------|------|
| `2026-03-05_failed_annotations_analysis.md` | 分析失败标注的模式 |
| `2026-03-05_rawoutput_patterns.md` | raw_output 文本模式分析 |
| `2026-03-05_parser_implementation.md` | 改进解析器以处理更多格式变体 |
| `2026-03-05_batch_fix_execution.md` | 批量修复执行报告 |
| `2026-03-05_reannotation_script.md` | 重标注脚本实现 |
| `2026-03-05_data_analysis.md` | 标注质量数据分析 |
| `2026-03-05_dlc_migration.md` | DLC 迁移实现 |

### 第三阶段：顽固资产处理（03-06）

处理多次重跑仍失败的资产。

| 文档 | 内容 |
|------|------|
| `2026-03-06_stubborn_assets_rerun.md` | 顽固资产 DLC 重跑任务 |
| `2026-03-06_stubborn_assets_final_report.md` | 重跑最终报告 |
| `2026-03-06_stubborn_15_final_report.md` | 最后 15 个顽固资产报告 |
| `2026-03-06_stubborn_15_manual_completion.md` | 15 个资产手动标注完成 |
| `2026-03-06_final_verification_report.md` | 最终全面检查报告 |

**阶段成果**：50,091 个资产全部解析成功（0 个 raw_output 失败）。

### 第四阶段：补标注（03-09）

发现目标目录有 52,907 个资产，而标注只覆盖了 50,091 个。

| 文档 | 内容 |
|------|------|
| `2026-03-09_annotation-validation-report.md` | 标注验证报告，发现 2,816 个缺失 |
| `2026-03-09_backfill-2816-missing-annotations.md` | 补标注 2,816 个缺失资产 |
| `2026-03-09_fix-42-null-descriptions.md` | 修复 42 个 description 为 null 的资产 |

**阶段成果**：52,907 个资产全部有标注，description 100% 完成。

### 第五阶段：物理属性填充（03-09）

VLM 对 2,148 个资产（主要是 wall/ground/ceiling/other 等结构性元素）的物理属性生成不完整。

| 文档 | 内容 |
|------|------|
| `2026-03-09_backfill-incomplete-physical-properties.md` | VLM 重标注物理属性（第二轮） |
| `2026-03-09_fill-default-physical-properties.md` | 用类别默认值填充 material/mass/placement |
| `2026-03-09_fill-dimensions-category-medians.md` | 用类别中位数填充 dimensions |

**阶段成果**：5 个字段全部 100% 完成。

---

## 数据流

```
VLM 标注 → output/{cat}/{id}_annotation.json → fill_annotations.py → GRScenes_assets/{cat}/{id}/{id}_annotation.json
```

说明：这是当时的数据交付链路摘要，保留原始阶段语境。

- **源目录**: `/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/output/`
- **目标目录**: `/cpfs/shared/simulation/zhuzihou/dev/usd-scene-physics-prep/GRScenes-test1/GRScenes_assets/`

## 填充策略总结

| 来源 | 覆盖资产数 | 字段 |
|------|-----------|------|
| VLM (Qwen2.5-VL-7B) | ~50,800 | 全部 5 个字段 |
| 类别默认值 | 2,055 | material, mass, placement |
| 类别中位数 | 1,911 | dimensions |
| 格式修复 | 24 | mass（非数字值替换） |
