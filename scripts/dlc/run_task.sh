#!/bin/bash
set -euo pipefail

CODE_ROOT=${DLC_CODE_ROOT:-"/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator"}

if [ -n "${DLC_WORKER_SETUP_SCRIPT:-}" ]; then
    if [ ! -f "$DLC_WORKER_SETUP_SCRIPT" ]; then
        echo "ERROR: DLC_WORKER_SETUP_SCRIPT is not a file: $DLC_WORKER_SETUP_SCRIPT" >&2
        exit 1
    fi
    # shellcheck disable=SC1090
    if ! source "$DLC_WORKER_SETUP_SCRIPT"; then
        echo "ERROR: DLC_WORKER_SETUP_SCRIPT failed: $DLC_WORKER_SETUP_SCRIPT" >&2
        exit 1
    fi
    set -euo pipefail
    export AUTO_ASSET_WORKER_SETUP_SOURCED=1
fi

PYTHON_RUNTIME=${DLC_PYTHON_RUNTIME:-"$CODE_ROOT/scripts/dlc/python_runtime.sh"}

append_supported_cli_args() {
    if [ -n "${MODEL_PATH:-}" ]; then
        CMD_ARGS+=("--model_path" "$MODEL_PATH")
    fi
    if [ -n "${MODEL_BACKEND:-}" ]; then
        CMD_ARGS+=("--model_backend" "$MODEL_BACKEND")
    fi
    if [ -n "${API_BASE_URL:-}" ]; then
        CMD_ARGS+=("--api_base_url" "$API_BASE_URL")
    fi
    if [ -n "${API_KEY_ENV:-}" ]; then
        CMD_ARGS+=("--api_key_env" "$API_KEY_ENV")
    fi
}

if [ $# -eq 0 ]; then
    echo "Usage: run_task.sh <mode> [args...]"
    echo ""
    echo "Modes:"
    echo "  annotate        Run VLM annotation with default prompt (extract_object_attributes_prompt)"
    echo "  classify        Run object classification task"
    echo "  extract         Run attribute extraction task"
    echo "  custom          Pass any command to the Python environment"
    echo ""
    echo "Chunk-based distributed mode:"
    echo "  run_task.sh <chunk_id> <chunk_total> [extra_args...]"
    echo ""
    echo "Examples:"
    echo "  bash run_task.sh annotate --input_dir /data/assets --output_dir /data/results"
    echo "  bash run_task.sh classify --input_dir /data/assets --output_dir /data/results"
    echo "  bash run_task.sh 0 4 --input_dir /data/assets --output_dir /data/results"
    exit 1
fi

if [ ! -f "$PYTHON_RUNTIME" ]; then
    echo "ERROR: Python runtime wrapper not found at $PYTHON_RUNTIME" >&2
    exit 1
fi

if [ "$1" == "annotate" ]; then
    shift
    CMD_ARGS=()
    append_supported_cli_args
    bash "$PYTHON_RUNTIME" -m auto_asset_annotator.main --prompt_type extract_object_attributes_prompt "${CMD_ARGS[@]}" "$@"

elif [ "$1" == "classify" ]; then
    shift
    CMD_ARGS=()
    append_supported_cli_args
    bash "$PYTHON_RUNTIME" -m auto_asset_annotator.main --prompt_type classify_object_category_prompt "${CMD_ARGS[@]}" "$@"

elif [ "$1" == "extract" ]; then
    shift
    CMD_ARGS=()
    append_supported_cli_args
    bash "$PYTHON_RUNTIME" -m auto_asset_annotator.main --prompt_type extract_object_attributes_prompt "${CMD_ARGS[@]}" "$@"

elif [ "$1" == "custom" ]; then
    shift
    if [ $# -eq 0 ]; then
        echo "ERROR: Custom mode requires a Python command" >&2
        echo "Usage: run_task.sh custom <python_args...>" >&2
        exit 1
    fi
    bash "$PYTHON_RUNTIME" "$@"

else
    if [ $# -lt 2 ]; then
        echo "ERROR: Batch mode requires at least 2 arguments: <chunk_id> <chunk_total>"
        echo "Usage: run_task.sh <chunk_id> <chunk_total> [--input_dir <path>] [--output_dir <path>] [other_args...]"
        echo ""
        echo "Examples:"
        echo "  bash run_task.sh 0 4 --input_dir /data/assets --output_dir /data/results"
        echo "  bash run_task.sh 2 8 --input_dir /data/assets --output_dir /data/results --force"
        exit 1
    fi

    CHUNK_ID=$1
    CHUNK_TOTAL=$2
    shift 2

    CMD_ARGS=()
    append_supported_cli_args

    if [ $# -gt 0 ]; then
        CMD_ARGS+=("$@")
    fi

    bash "$PYTHON_RUNTIME" -m auto_asset_annotator.main --num_chunks "$CHUNK_TOTAL" --chunk_index "$CHUNK_ID" "${CMD_ARGS[@]}"
fi
