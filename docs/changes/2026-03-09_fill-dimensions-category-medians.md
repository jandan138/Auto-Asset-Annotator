# 用类别中位数填充 1,911 个空 dimensions 字段

**日期**: 2026-03-09

## 背景

在 material/mass/placement 全部填充完毕后，还剩 1,911 个资产的 dimensions 字段为空（3.6%）。

评估了多种方案后，选择用同类别已有标注的中位数来填充：
- **GLB 解析方案**：可行（纯 Python 可解析 GLB 文件提取包围盒），但存在单位不一致问题，需要逐资产校准缩放因子
- **VLM 重跑**：这些资产之前 VLM 已经标注失败过，再跑收益低
- **类别中位数**：最简单直接，虽然精度有限但能保证格式一致和值合理

## 实施

### 计算中位数

从 output/ 中 50,996 个已填充 dimensions 的标注文件中，按类别统计所有有效 `X * Y * Z` 值，计算 W/D/H 各维度的中位数。覆盖 47 个类别。

### 更新 fill_defaults.py

在 `CATEGORY_DEFAULTS` 的每个类别条目中增加 `"dimensions"` 字段。示例：

```python
"bottle": {"material": "Plastic (PET)", "mass": "0.15", "dimensions": "0.15 * 0.15 * 0.2", "placement": "OnTable"},
```

### 执行

```bash
python scripts/fill_defaults.py --output_dir ./output --asset_list final_remaining.txt --fill_dimensions --apply
python scripts/fill_annotations.py --apply
```

## 结果

- 1,911 个 dimensions 字段成功填充
- 源目录和目标目录均验证通过：所有 5 个字段 0 空值

### 各类别填充数量（前 10）

| 类别 | 填充数 |
|------|--------|
| other | 490 |
| wall | 434 |
| ground | 378 |
| bottle | 123 |
| ceiling | 57 |
| book | 55 |
| window | 40 |
| cabinet | 36 |
| plant | 35 |
| faucet | 32 |

## 备注

源目录 strict 模式仍报 31 个 "invalid format" dimensions（非空但格式不标准，如缺少小数点），这些是 VLM 原始输出的遗留问题，不影响实际使用。
