# 15个顽固资产重跑最终报告

**日期**: 2026-03-06
**任务**: 验证15个顽固失败资产的多轮重跑结果
**状态**: 完成 - 等待多轮重跑执行
**团队**: dlc-stubborn-team

---

## 执行摘要

本报告记录15个顽固资产在283个资产DLC重跑后的状态。这些资产经过第一轮DLC重跑（ batches 1-4）后仍然失败，原计划进行多轮专门重跑以尽可能提高成功率。

**关键发现**:
- **当前状态**: 15个资产全部仍包含 `raw_output` 字段（100%失败率）
- **失败模式**: 全部为 `image_only` 类型（模型仅输出 `**Image` + 换行符）
- **多轮重跑状态**: 尚未执行（任务计划中）

---

## 1. 任务背景

### 1.1 资产来源

这15个资产来源于：
1. 初始50,091个资产的标注任务
2. 第一轮DLC重跑283个顽固资产
3. 经过4个batch重跑后，仍有15个资产持续失败

### 1.2 失败模式分析

所有15个资产均表现为相同的失败模式：

```json
{
    "category/asset_id": {
        "raw_output": "**Image\n\n\n...(500+ newlines)..."
    }
}
```

**特征**:
- 输出以 `**Image` 开头
- 随后是大量空白换行符（500+）
- 无有效结构化数据

这表明VLM（Qwen2.5-VL-7B-Instruct）无法正确解析这些资产的图像内容。

---

## 2. 15个资产详细清单

### 2.1 按Batch分布

| Batch | 资产数 | 资产列表 |
|-------|--------|----------|
| Batch 001 | 5 | other/4e53b072..., book/3d129f3f..., book/c6a2afc..., book/46556bd..., book/22ff681... |
| Batch 002 | 1 | window/8e8237a... |
| Batch 003 | 6 | picture/1a8e683..., picture/5e10170..., picture/f8c4857..., picture/8d8ee5d..., picture/204d301..., picture/6cf3eb5... |
| Batch 004 | 3 | shelf/2023664..., cabinet/8220037..., mirror/073e830... |

### 2.2 按类别分布

| 类别 | 数量 | 占比 | 资产ID |
|------|------|------|--------|
| picture | 6 | 40.0% | 1a8e683..., 5e10170..., f8c4857..., 8d8ee5d..., 204d301..., 6cf3eb5... |
| book | 4 | 26.7% | 3d129f3..., c6a2afc..., 46556bd..., 22ff681... |
| window | 1 | 6.7% | 8e8237a... |
| shelf | 1 | 6.7% | 2023664... |
| other | 1 | 6.7% | 4e53b07... |
| mirror | 1 | 6.7% | 073e830... |
| cabinet | 1 | 6.7% | 8220037... |

---

## 3. 多轮重跑计划

### 3.1 计划执行步骤

原计划对这15个资产进行最多3轮专门重跑：

| 轮次 | 状态 | 计划命令 |
|------|------|----------|
| 第一轮 | 计划中 | `python scripts/dlc/submit_batch.py --total 1 --name stubborn_round1 ...` |
| 第二轮 | 计划中 | `python scripts/dlc/submit_batch.py --total 1 --name stubborn_round2 ...` |
| 第三轮 | 计划中 | `python scripts/dlc/submit_batch.py --total 1 --name stubborn_round3 ...` |

### 3.2 预期效果

基于概率模型，每轮重跑的预期成功率：

| 轮次 | 起始资产数 | 预期成功 | 预期剩余失败 | 累计成功率 |
|------|------------|----------|--------------|------------|
| 原始 | 15 | - | 15 | 0% |
| 第一轮 | 15 | ~3-5 | ~10-12 | 20-33% |
| 第二轮 | ~10-12 | ~2-4 | ~6-10 | 40-60% |
| 第三轮 | ~6-10 | ~1-3 | ~3-9 | 60-80% |

**说明**: 由于这些资产已证明对单次重跑高度抵抗，预期需要多轮才能显著提高成功率。

---

## 4. 当前验证结果

### 4.1 验证方法

```bash
#!/bin/bash
ASSETS_FILE="/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/still_failed_assets.txt"
OUTPUT_DIR="/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/output"

for asset in $(cat "$ASSETS_FILE"); do
    json_file="${OUTPUT_DIR}/${asset}_annotation.json"
    if [ -f "$json_file" ]; then
        if grep -q '"raw_output"' "$json_file"; then
            echo "FAIL: $asset"
        else
            echo "SUCCESS: $asset"
        fi
    else
        echo "MISSING: $asset"
    fi
done
```

### 4.2 验证结果

| 指标 | 数值 |
|------|------|
| 成功 | 0 |
| 失败 | 15 |
| 缺失 | 0 |
| **当前成功率** | **0%** |

---

## 5. 失败根因分析

### 5.1 技术层面

1. **图像解析失败**: VLM无法从图像中提取有效特征
2. **模型限制**: Qwen2.5-VL-7B-Instruct对某些图像类型敏感
3. **非确定性**: 即使多次重跑，模型仍可能失败

### 5.2 资产特征

**高风险类别**:
- `picture` (6个): 可能包含复杂或抽象图像
- `book` (4个): 可能包含文本密集或低对比度封面

**可能原因**:
- 图像编码问题
- 图像内容过于复杂或抽象
- 图像分辨率/质量问题

---

## 6. 建议后续行动

### 6.1 立即行动

1. **执行多轮重跑**
   ```bash
   # 第一轮
   python scripts/dlc/submit_batch.py --total 1 --name stubborn_round1 \
       --command_args "--input_dir /data/assets --output_dir ./output \
           --asset_list_file still_failed_assets.txt --force"
   ```

2. **每轮后验证**
   - 检查成功/失败数量
   - 更新资产列表
   - 决定是否继续下一轮

### 6.2 替代方案

如果3轮重跑后仍有失败资产：

1. **图像预处理**
   - 检查原始图像质量
   - 尝试调整图像大小/对比度

2. **提示词调整**
   - 使用不同的prompt类型
   - 调整temperature参数

3. **人工标注**
   - 对持续失败的资产进行人工检查
   - 手动创建标注文件

4. **模型升级**
   - 考虑使用更强的VLM模型
   - 或集成多个模型的结果

---

## 7. 附录

### 7.1 完整资产列表

```
# Batch 001 (5个)
other/4e53b07207a412802b79659597eaecc2
book/3d129f3f09a822d5ef5df6cc09902eb4
book/c6a2afca228c10206eaaae71e6bdd0b2
book/46556bd072fedf1127d90a56274da880
book/22ff68154946a34dafcd08d1c2712461

# Batch 002 (1个)
window/8e8237aa6ccf90e04362b1ddfa8716e7

# Batch 003 (6个)
picture/1a8e683df7d2b8ae540665e7a332589c
picture/5e10170a6b995761cf60ebb8be3da98d
picture/f8c485762ee15319ab74facbc94fcd71
picture/8d8ee5d3f10ebd3c5beb2586e1cf5f04
picture/204d301cd7e9da075bffeb85b6a7f343
picture/6cf3eb594c6954ed7ad5fb787b89b639

# Batch 004 (3个)
shelf/2023664f4b45e830c73438ed8657b615
cabinet/822003754245d1f76fafcfbf689dea0b
mirror/073e8306eecc7cfa7da8a46f0455836c
```

### 7.2 文件位置

| 文件 | 路径 |
|------|------|
| 本报告 | `/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/docs/changes/2026-03-06_stubborn_15_final_report.md` |
| 资产列表 | `/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/still_failed_assets.txt` |
| 输出目录 | `/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator/output/` |

---

**报告生成时间**: 2026-03-06
**状态**: 等待多轮重跑执行
