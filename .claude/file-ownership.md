# 文件归属表（File Ownership Map）

> 本文件供 Agent Teams 使用：team lead 依此分配任务，version-commit-agent 依此规划合并顺序。
> **同一文件在一次 Agent Teams 会话中只能由一个 agent 修改**；若多个 agent 需触及同一文件，应串行而非并行。

## 代码模块归属

| 路径 | 负责 Agent | 说明 |
|---|---|---|
| `src/auto_asset_annotator/core/` | feature-implementer, bug-fixer | 核心管道：pipeline、model、prompt |
| `src/auto_asset_annotator/config/` | feature-implementer, code-refactorer | 配置系统：settings、YAML 加载 |
| `src/auto_asset_annotator/utils/` | feature-implementer, bug-fixer | 工具函数：file、image |
| `src/auto_asset_annotator/main.py` | feature-implementer, code-refactorer | CLI 入口；高冲突风险 |
| `scripts/` | feature-implementer | 独立工具脚本 |
| `test_parser_robustness.py` | test-writer, bug-fixer | 解析器测试 |

## 文档归属

| 路径 | 负责 Agent | 说明 |
|---|---|---|
| `CLAUDE.md` | docs-writer, team lead | 项目级指令；重要变更需人工审核 |
| `README.md` | docs-writer | 项目说明文档 |
| `docs/` | docs-writer | 详细文档目录 |

## 配置归属

| 路径 | 负责 Agent | 说明 |
|---|---|---|
| `config/config.yaml` | feature-implementer | 默认配置；各模块都可能引用 |
| `pyproject.toml` | team lead / 手动 | 包配置 |
| `requirements.txt` | team lead / 手动 | 依赖列表 |

## 高冲突风险文件

以下文件被多个模块依赖，在 Agent Teams 并行时需特别注意：

| 文件 | 风险原因 | 推荐处理方式 |
|---|---|---|
| `src/auto_asset_annotator/main.py` | CLI 参数解析，所有功能入口 | 多功能时串行处理 |
| `src/auto_asset_annotator/core/pipeline.py` | 核心管道，连接所有组件 | 协调修改，避免并发 |
| `CLAUDE.md` | 中央文档 | 仅 docs-writer 或 team lead 修改 |

## 规则摘要

1. **并行安全**：各 agent 改动不重叠的路径
2. **并行危险**：两个 agent 都需要改同一个文件
3. **合并顺序**：version-commit-agent 应先合并改动范围最小、最独立的分支
4. **超范围警告**：若 agent 的改动超出本表所列范围，version-commit-agent 须在合并前报告 team lead
