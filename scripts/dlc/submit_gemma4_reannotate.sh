#!/bin/bash
set -euo pipefail

CODE_ROOT=${DLC_CODE_ROOT:-"/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator"}
SUBMIT_WRAPPER="$CODE_ROOT/scripts/dlc/submit_asset_list.sh"

TOTAL=${TOTAL:-1}
NAME=${NAME:-gemma4_reannotate}
INPUT_DIR=${INPUT_DIR:-/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/dataset/GRScenes_assets}
RUN_ID=${RUN_ID:-$(date -u +%Y%m%dT%H%M%SZ)_gemma4_reannotate}
ANNOTATION_RUNS_ROOT=/cpfs/user/zhuzihou/assets/dedup_workspaces/test0_transitive_apply_parallel/annotation_runs
OUTPUT_DIR=${OUTPUT_DIR:-$ANNOTATION_RUNS_ROOT/$RUN_ID/output}
ASSET_LIST_FILE=${ASSET_LIST_FILE:-}
MODEL_BACKEND=local_gemma4_multimodal
MODEL_PATH=${MODEL_PATH:-/cpfs/user/zhuzihou/models/gemma4/releases/unsloth-gemma-4-E4B-it-unsloth-bnb-4bit/9746c23553347b443ebdc1caba1d41b52223d0c8}
AUTO_ASSET_VENV=${AUTO_ASSET_VENV:-/cpfs/user/zhuzihou/conda-managed/envs/genesis-llm-qlora-py310}
DLC_WORKER_SETUP_SCRIPT=${DLC_WORKER_SETUP_SCRIPT:-/cpfs/user/zhuzihou/conda-managed/bin/use-gcc-toolchain-hf-offline.sh}
# Gemma4 follows the Genesis-LLM QLoRA runtime path. The Isaac Sim image is
# suitable for USD/physics jobs but has already failed this model load path.
DLC_IMAGE=${DLC_IMAGE:-pj4090acr-registry-vpc.cn-beijing.cr.aliyuncs.com/pj4090/mahaoxiang:genmanip-mahaoxiang}
DLC_PROFILE=${DLC_PROFILE:-local_hf_default}
DLC_DATA_SOURCES=${DLC_DATA_SOURCES:-d-mzps5b7joy2axmqpa8,d-d49o5g0h2818sw8j1g,d-8wz4emfs21s5ajs9oz,d-f1dsz5nbamclxgydo8}

RUN_ROOT=${RUN_ROOT:-$(dirname "$OUTPUT_DIR")}
UNSLOTH_COMPILE_LOCATION=${UNSLOTH_COMPILE_LOCATION:-$RUN_ROOT/cache/unsloth_compiled_cache}
HF_HUB_OFFLINE=${HF_HUB_OFFLINE:-1}
TRANSFORMERS_OFFLINE=${TRANSFORMERS_OFFLINE:-1}
TOKENIZERS_PARALLELISM=${TOKENIZERS_PARALLELISM:-false}
EXTRA_MAIN_ARGS=${EXTRA_MAIN_ARGS:-}

normalize_path() {
    case "$1" in
        /*) realpath -m "$1" ;;
        *) realpath -m "$CODE_ROOT/$1" ;;
    esac
}

safe_output_dir_error() {
    local output_dir="$1"
    local abs_output abs_runs_root abs_input abs_code output_parent output_grandparent

    abs_output="$(normalize_path "$output_dir")"
    abs_runs_root="$(normalize_path "$ANNOTATION_RUNS_ROOT")"
    abs_input="$(normalize_path "$INPUT_DIR")"
    abs_code="$(normalize_path "$CODE_ROOT")"
    output_parent="$(dirname "$abs_output")"
    output_grandparent="$(dirname "$output_parent")"

    if [ "$(basename "$abs_output")" != "output" ] || [ "$output_grandparent" != "$abs_runs_root" ]; then
        echo "output must match $abs_runs_root/<run_id>/output"
        return 0
    fi

    case "$abs_output/" in
        "$abs_input/"*|"$abs_code/output/"*|"$abs_code/output_reannotate/"*)
            echo "output resolves inside an unsafe input or legacy output tree"
            return 0
            ;;
    esac

    return 1
}

find_protected_extra_main_arg() {
    EXTRA_MAIN_ARGS_VALUE="$EXTRA_MAIN_ARGS" python - <<'PY'
import os
import shlex
import sys

protected = {
    "--input_dir",
    "--output_dir",
    "--asset_list_file",
    "--num_chunks",
    "--chunk_index",
    "--model_backend",
    "--model_path",
}

try:
    args = shlex.split(os.environ["EXTRA_MAIN_ARGS_VALUE"])
except ValueError as exc:
    print(f"parse error: {exc}", file=sys.stderr)
    sys.exit(2)

for arg in args:
    key = arg.split("=", 1)[0]
    if key in protected:
        print(arg)
        sys.exit(0)

sys.exit(1)
PY
}

if [ -z "$ASSET_LIST_FILE" ]; then
    echo "ERROR: submit_gemma4_reannotate.sh requires ASSET_LIST_FILE" >&2
    exit 1
fi

if output_error="$(safe_output_dir_error "$OUTPUT_DIR")"; then
    echo "ERROR: refusing unsafe Gemma4 output directory: $OUTPUT_DIR" >&2
    echo "Reason: $output_error" >&2
    echo "Use an isolated annotation_runs/<run_id>/output path." >&2
    exit 1
fi

if protected_extra_arg="$(find_protected_extra_main_arg)"; then
    echo "ERROR: refusing protected EXTRA_MAIN_ARGS token for Gemma4 reannotation: $protected_extra_arg" >&2
    echo "Set INPUT_DIR, OUTPUT_DIR, ASSET_LIST_FILE, MODEL_PATH, and chunking through the wrapper environment instead." >&2
    exit 1
else
    protected_status=$?
    if [ "$protected_status" -eq 2 ]; then
        echo "ERROR: refusing protected EXTRA_MAIN_ARGS because it could not be parsed" >&2
        exit 1
    fi
fi

MODEL_CLI_ARGS=(
    --model_backend "$MODEL_BACKEND"
    --model_path "$MODEL_PATH"
    --force
)
printf -v MODEL_EXTRA_MAIN_ARGS '%q ' "${MODEL_CLI_ARGS[@]}"
MODEL_EXTRA_MAIN_ARGS=${MODEL_EXTRA_MAIN_ARGS% }
if [ -n "$EXTRA_MAIN_ARGS" ]; then
    EXTRA_MAIN_ARGS="$EXTRA_MAIN_ARGS $MODEL_EXTRA_MAIN_ARGS"
else
    EXTRA_MAIN_ARGS="$MODEL_EXTRA_MAIN_ARGS"
fi

export TOTAL NAME INPUT_DIR OUTPUT_DIR ASSET_LIST_FILE EXTRA_MAIN_ARGS
export MODEL_BACKEND MODEL_PATH AUTO_ASSET_VENV DLC_WORKER_SETUP_SCRIPT DLC_IMAGE DLC_PROFILE DLC_DATA_SOURCES
export UNSLOTH_COMPILE_LOCATION HF_HUB_OFFLINE TRANSFORMERS_OFFLINE TOKENIZERS_PARALLELISM

echo "[gemma4-reannotate] TOTAL=$TOTAL NAME=$NAME DLC_PROFILE=$DLC_PROFILE"
echo "[gemma4-reannotate] INPUT_DIR=$INPUT_DIR"
echo "[gemma4-reannotate] OUTPUT_DIR=$OUTPUT_DIR"
echo "[gemma4-reannotate] ASSET_LIST_FILE=$ASSET_LIST_FILE"
echo "[gemma4-reannotate] MODEL_PATH=$MODEL_PATH"
echo "[gemma4-reannotate] AUTO_ASSET_VENV=$AUTO_ASSET_VENV"
echo "[gemma4-reannotate] DLC_WORKER_SETUP_SCRIPT=$DLC_WORKER_SETUP_SCRIPT"
echo "[gemma4-reannotate] DLC_IMAGE=$DLC_IMAGE"

exec bash "$SUBMIT_WRAPPER" "$@"
