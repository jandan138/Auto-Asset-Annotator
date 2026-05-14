# Gemma4 本地多模态 Smoke Runbook

本页记录当前仓库中 `local_gemma4_multimodal` 的本地单资产 smoke 流程。它面向“先证明链路能跑通”的小范围验证，不是全量生产提交说明。

## 结论摘要

当前已经验证过一条可用路径：

- Python 环境：`/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python`
- 模型：`/cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8`
- 输入资产：`/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets/basket/6c68230d67112b1dfd2bd7fa9322c756`
- 输出根目录：`/cpfs/user/zhuzihou/tmp/auto_asset_annotator_smoke/20260514T024226Z_grscenes_basket_6c68230d_gemma4/`
- 成功输出：`output/basket/6c68230d67112b1dfd2bd7fa9322c756_annotation.json`

这个输出使用 Auto-Asset-Annotator 现有结果风格：顶层键是 `category/asset_id`，内部字段是 `category`、`description`、`material`、`dimensions`、`mass`、`placement`。它不是 GRScenes 原始资产目录里的 metadata schema。详见 `docs/usage/output_schema.md`。

## 什么时候使用

使用这个 runbook 的场景：

- 验证 Gemma4 base 模型能读取真实四视角资产图像。
- 比较 Gemma4 与 Qwen/API 输出质量。
- 调试 `local_gemma4_multimodal` backend、Transformers/Unsloth/bitsandbytes 兼容性。
- 在全量生产前做一两个资产的隔离验证。

不要用这个 runbook 直接做大批量生产：

- Gemma4 会加载约 11G 本地模型。
- 单资产 smoke 不等于质量 gate。
- Genesis-LLM adapter 尚未作为资产标注 adapter 验证。
- 输出目录必须隔离，不能直接覆盖数据集原始 annotation。

## 已知可用环境

Gemma4 本地多模态需要足够新的 Transformers 和 Unsloth runtime patch。

已验证可用：

```bash
/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python
```

本机预检结果：

```text
transformers 5.8.0.dev0
AutoProcessor=True
AutoModelForImageTextToText=True
Gemma4ForConditionalGeneration=True
torch 2.10.0+cu128
torch.cuda.is_available() == True on the smoke node
bitsandbytes 0.49.2
unsloth 2026.4.8
```

不够用的环境：

```text
.venv_dlc/bin/python
transformers 5.2.0
```

这个环境能导入部分 Gemma4 API，但 processor-only smoke 会退化成 tokenizer-style processor，不产生 `pixel_values` 或 `image_position_ids`，所以不能作为 Gemma4 多模态 smoke 的 runtime。

## 模型与 adapter 路径

Gemma4 base release 路径：

```text
/cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8
```

便捷 symlink：

```text
/cpfs/user/zhuzihou/models/gemma4/current
```

推荐生产候选和可复现记录使用不可变 release 路径。`current` 适合临时手动验证。

模型体积：

```text
11G   /cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8
341M  /cpfs/user/zhuzihou/models/gemma4/adapters/genesis-llm-fullscale-v0-gpu2-seed42-epoch3
```

Genesis adapter 路径：

```text
/cpfs/user/zhuzihou/models/gemma4/adapters/genesis-llm-fullscale-v0-gpu2-seed42-epoch3
```

默认不要启用该 adapter。它来自 Genesis-LLM text-to-physics 训练链路，不是已验证的四视角资产标注 adapter。

## 输出隔离规范

所有 smoke 输出必须写到临时/实验目录，不写入数据集原目录，不写入仓库默认 `output/`，不在仓库根生成缓存。

推荐 run root 形状：

```bash
RUN_ROOT=/cpfs/user/zhuzihou/tmp/auto_asset_annotator_smoke/$(date -u +%Y%m%dT%H%M%SZ)_grscenes_basket_6c68230d_gemma4
mkdir -p "$RUN_ROOT/input" "$RUN_ROOT/output" "$RUN_ROOT/logs" "$RUN_ROOT/cache"
```

资产列表文件：

```bash
printf '%s\n' 'basket/6c68230d67112b1dfd2bd7fa9322c756' > "$RUN_ROOT/input/asset_list.txt"
```

Unsloth 编译缓存：

```bash
export UNSLOTH_COMPILE_LOCATION="$RUN_ROOT/cache/unsloth_compiled_cache"
```

当前 backend 已经会在未设置 `UNSLOTH_COMPILE_LOCATION` 时选择仓库外的绝对路径，但 smoke/runbook 仍建议显式指向 run-local cache，便于复现实验和清理。

## 输入资产预检

数据根目录：

```bash
DATA_ROOT=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets
ASSET_REL=basket/6c68230d67112b1dfd2bd7fa9322c756
ASSET_DIR="$DATA_ROOT/$ASSET_REL"
```

检查图片：

```bash
ls "$ASSET_DIR"/front.png "$ASSET_DIR"/left.png "$ASSET_DIR"/back.png "$ASSET_DIR"/right.png
```

目标资产已经确认四张图片都存在，均为 `512x512 RGB`。

原始数据集自带 annotation 文件：

```text
/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets/basket/6c68230d67112b1dfd2bd7fa9322c756/6c68230d67112b1dfd2bd7fa9322c756_annotation.json
```

该文件属于 GRScenes 原始 metadata schema，不要被 smoke 输出覆盖。

## Processor-only Smoke

processor-only smoke 不加载模型权重，目标是证明 Gemma4 processor 能把真实图片转成多模态输入张量。
以下命令复用前面“输出隔离规范”中创建的 `RUN_ROOT` 和资产列表；如果是新的 shell，先重新执行那一段 setup。

```bash
: "${RUN_ROOT:?Run the output-isolation setup first.}"
DATA_ROOT=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets
ASSET_DIR="$DATA_ROOT/basket/6c68230d67112b1dfd2bd7fa9322c756"
MODEL_PATH=/cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8
mkdir -p "$RUN_ROOT/logs"

HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
MODEL_PATH="$MODEL_PATH" ASSET_DIR="$ASSET_DIR" PYTHONPATH=src \
/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python - \
  > "$RUN_ROOT/logs/processor_smoke.log" 2>&1 <<'PY'
import os
import sys
from pathlib import Path

import transformers
from transformers import AutoProcessor

model_path = Path(os.environ["MODEL_PATH"])
asset_dir = Path(os.environ["ASSET_DIR"])
image_paths = [asset_dir / name for name in ("front.png", "left.png", "back.png", "right.png")]
missing = [str(path) for path in image_paths if not path.exists()]
if missing:
    print("missing_images", missing)
    sys.exit(3)

print("python", sys.executable)
print("transformers", transformers.__version__, transformers.__file__)
print("model_path", model_path)
print("asset_dir", asset_dir)
print("images", [str(path) for path in image_paths])

processor = AutoProcessor.from_pretrained(
    str(model_path),
    trust_remote_code=True,
    local_files_only=True,
)
messages = [
    {
        "role": "user",
        "content": [{"type": "text", "text": "Describe this asset."}]
        + [{"type": "image", "image": str(path)} for path in image_paths],
    }
]
inputs = processor.apply_chat_template(
    messages,
    tokenize=True,
    return_dict=True,
    return_tensors="pt",
    add_generation_prompt=True,
)
print("processor_class", processor.__class__.__name__)
print("keys", sorted(inputs.keys()))
for key, value in inputs.items():
    shape = getattr(value, "shape", None)
    dtype = getattr(value, "dtype", None)
    print(f"tensor {key} shape={tuple(shape) if shape is not None else None} dtype={dtype}")
image_keys = [key for key in inputs.keys() if "image" in key or "pixel" in key]
print("image_keys", image_keys)
if not image_keys:
    print("ERROR missing image tensor keys")
    sys.exit(2)
print("OK image tensors present")
PY
```

通过时应看到：

```text
processor_class Gemma4Processor
keys ['attention_mask', 'image_position_ids', 'input_ids', 'mm_token_type_ids', 'pixel_values']
tensor pixel_values shape=(4, 2520, 768) dtype=torch.float32
tensor image_position_ids shape=(4, 2520, 2) dtype=torch.int64
image_keys ['pixel_values', 'image_position_ids']
OK image tensors present
```

如果只看到 `input_ids` / `attention_mask`，说明当前 runtime 没有真正走 Gemma4 多模态 processor。

## 单资产 CLI Smoke

这是当前推荐的真实模型 smoke 命令。它会加载 Gemma4 base，读取四张资产图片，调用现有 `AnnotationPipeline`，并写出 Auto-Asset 格式 JSON。
以下命令同样复用前面创建的 `RUN_ROOT`。它会先检查资产列表是否存在，避免先加载 11G 模型再因为输入文件缺失失败。

```bash
: "${RUN_ROOT:?Run the output-isolation setup first.}"
DATA_ROOT=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets
MODEL_PATH=/cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8
test -f "$RUN_ROOT/input/asset_list.txt"
mkdir -p "$RUN_ROOT/output" "$RUN_ROOT/logs" "$RUN_ROOT/cache"

HF_HUB_OFFLINE=1 \
TRANSFORMERS_OFFLINE=1 \
TOKENIZERS_PARALLELISM=false \
UNSLOTH_COMPILE_LOCATION="$RUN_ROOT/cache/unsloth_compiled_cache" \
PYTHONPATH=src \
/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310/bin/python \
  -m auto_asset_annotator.main \
  --input_dir "$DATA_ROOT" \
  --asset_list_file "$RUN_ROOT/input/asset_list.txt" \
  --output_dir "$RUN_ROOT/output" \
  --model_backend local_gemma4_multimodal \
  --model_path "$MODEL_PATH" \
  --force \
  > "$RUN_ROOT/logs/gemma4_cli_fixed_backend_smoke.log" 2>&1
```

通过时日志应包含：

```text
Unsloth Zoo will now patch everything to make training faster
[INFO] Loading Gemma4 multimodal model: ...
[INFO] Using Gemma4 model class: AutoModelForImageTextToText
[INFO] Gemma4 multimodal model loaded successfully.
[INFO] Loaded 1 assets from list.
[INFO] Processing asset: 6c68230d67112b1dfd2bd7fa9322c756
[INFO] Finished 6c68230d67112b1dfd2bd7fa9322c756 in ...
Processing complete.
```

输出文件：

```text
$RUN_ROOT/output/basket/6c68230d67112b1dfd2bd7fa9322c756_annotation.json
```

成功 smoke 的实际输出示例：

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

## 为什么需要 Unsloth patch

`unsloth/gemma-4-E4B-it-unsloth-bnb-4bit` 是 4-bit bitsandbytes checkpoint。真实图片推理会进入 Gemma4 vision tower。没有先加载 Unsloth patch 时，模型会在 vision branch 里触发 bitsandbytes FP4 初始化断言：

```text
FP4 quantization state not initialized
AssertionError
```

因此 backend 会在以下情况下自动准备 Unsloth runtime：

- `model.name` 路径或名称里包含 `unsloth`
- 本地 `config.json` 包含 `unsloth_fixed: true`
- 本地 `config.json` 的 `quantization_config` 是 `bitsandbytes` 且 `load_in_4bit` 为 true

这个逻辑也覆盖 `/cpfs/user/zhuzihou/models/gemma4/current` 这类 symlink 路径。

## 输出风格是否与旧结果一致

与仓库现有 `./output/.../*_annotation.json` 的 Auto-Asset 输出风格一致：

- 顶层是单键 dict，键为 `category/asset_id`
- 内部字段为 `category`、`description`、`material`、`dimensions`、`mass`、`placement`
- 字段值主要是字符串
- 文件路径为 `{output_dir}/{category}/{asset_id}_annotation.json`

不与 GRScenes 原始 metadata schema 完全一致。GRScenes 原始 annotation 通常是无顶层包装的对象，并包含 `uid`、`asset_type`、`usd_size`、`orientation`、`usd_material_softlink` 等字段，`placement` 也是 list。

如果后续要把 Auto-Asset 输出回填到 GRScenes 原始 metadata，需要单独做 schema 转换和字段合并，不要直接覆盖。

## 常见失败与处理

### Processor 只有 text keys

现象：

```text
processor_class: TokenizersBackend
keys: ['attention_mask', 'input_ids']
missing image tensor keys
```

原因：Transformers runtime 不支持 Gemma4 多模态 processor。切换到 Genesis-LLM QLoRA env 或等价环境。

### bitsandbytes FP4 AssertionError

现象：

```text
FP4 quantization state not initialized
AssertionError
```

原因：Unsloth patch 没有在 Transformers 之前加载。当前 backend 已修复；如果手写脚本绕过 backend，需要在任何 Transformers import 前 `import unsloth`。

### 仓库根目录出现 `unsloth_compiled_cache/`

原因：Unsloth 默认编译缓存落在当前工作目录。

处理：

- 新流程中设置 `UNSLOTH_COMPILE_LOCATION="$RUN_ROOT/cache/unsloth_compiled_cache"`。
- 当前 backend 默认会选择仓库外路径。
- 如果历史 smoke 已经生成了仓库根 cache，应移动到 smoke 目录或删除，不要提交。

### 输出只有 `raw_output`

原因：模型生成了文本，但 parser 没解析出结构化字段。

处理：

- 保留原始输出做排查。
- 重跑同一资产通常会自动重试 `raw_output` 文件。
- 检查 prompt 是否仍要求 `Category`、`Description`、`Material`、`Dimensions`、`Mass`、`Placement` 这些标题。

## 进入生产前的 gate

Gemma4 单资产 smoke 只证明链路可运行。进入更大范围前至少补齐：

- 多类别小样本 smoke。
- 与现有 Qwen/API 输出做并排质量对比。
- 检查 `dimensions`、`mass`、`placement` 是否符合下游物理使用要求。
- 明确是否需要 schema 转换到 GRScenes 原始 metadata。
- DLC worker 上的同等 runtime 验证。
- Genesis adapter A/B 对比，且只在 base 模型稳定后进行。
