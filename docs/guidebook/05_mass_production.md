# 终章：建立流水线

处理 1 个资产和处理 52,907 个资产，最大的区别不是命令变了，而是你必须学会把工作拆开、容错、续跑。

## 1. 影分身之术：Chunking

`main.py` 当前内置了分块处理：

```bash
python -m auto_asset_annotator.main --num_chunks 4 --chunk_index 0
python -m auto_asset_annotator.main --num_chunks 4 --chunk_index 1
```

它会先拿到完整资产列表，再按 `num_chunks` 和 `chunk_index` 切出当前 worker 要处理的那一段。

## 2. 为什么可以断点续跑？

因为程序不是傻乎乎地每次全量重跑。当前逻辑会在处理前检查输出文件：

- 文件不存在：处理
- 文件里有 `raw_output`：处理
- 传了 `--retry_incomplete` 且 `material` / `dimensions` / `mass` / `placement` 有空值：处理
- 传了 `--force`：处理
- 其余情况：跳过

这意味着中断后通常可以直接继续跑，而不是推倒重来。

## 3. 失败并不等于丢失

如果模型输出没被解析成功，系统会把原始文本塞进 `raw_output`。这非常重要，因为大规模流水线里最怕的不是失败，而是“失败了但没有证据”。

## 4. 这条流水线已经跑到了哪一步？

这不是纸上谈兵。当前仓库记录的完成状态是：

- 总资产数：**52,907**
- `raw_output` 失败数：**0**
- `description` / `material` / `dimensions` / `mass` / `placement`：**100% 完整**

换句话说，这一章讲的不是未来计划，而是已经被实际跑通过的方法。

## 5. 量产时最实用的三个习惯

- 先小样验证目录、prompt 和输出格式
- 批量时用 chunk 拆分，而不是把所有压力压在一台机器上
- 出现失败时，优先使用现有的重试和修复路径，而不是手工重复劳动

你现在看到的，不只是一个模型调用脚本，而是一条已经量产过的标注生产线。
