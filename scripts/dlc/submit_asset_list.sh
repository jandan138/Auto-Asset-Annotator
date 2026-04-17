#!/bin/bash
set -euo pipefail

CODE_ROOT=${DLC_CODE_ROOT:-"/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator"}
SUBMIT_PY="$CODE_ROOT/scripts/dlc/submit_batch.py"
PYTHON_BIN=${PYTHON_BIN:-python}

TOTAL=${TOTAL:-4}
NAME=${NAME:-asset_list_annotation}
INPUT_DIR=${INPUT_DIR:-/data/assets}
OUTPUT_DIR=${OUTPUT_DIR:-/data/results}
EXTRA_MAIN_ARGS=${EXTRA_MAIN_ARGS:-}

ASSET_LIST_FILE=${ASSET_LIST_FILE:-}
FORWARD_ARGS=()

while [ $# -gt 0 ]; do
    case "$1" in
        --asset_list_file)
            if [ $# -lt 2 ]; then
                echo "ERROR: --asset_list_file requires a value" >&2
                exit 1
            fi
            ASSET_LIST_FILE="$2"
            shift 2
            ;;
        --asset_list_file=*)
            ASSET_LIST_FILE=${1#*=}
            shift
            ;;
        *)
            FORWARD_ARGS+=("$1")
            shift
            ;;
    esac
done

if [ -z "$ASSET_LIST_FILE" ]; then
    echo "ERROR: submit_asset_list.sh requires --asset_list_file <path> or ASSET_LIST_FILE" >&2
    exit 1
fi

ASSET_LIST_CHECK_PATH="$ASSET_LIST_FILE"
if [ ! -e "$ASSET_LIST_CHECK_PATH" ] && [ -e "$CODE_ROOT/$ASSET_LIST_FILE" ]; then
    ASSET_LIST_CHECK_PATH="$CODE_ROOT/$ASSET_LIST_FILE"
fi
if [ ! -r "$ASSET_LIST_CHECK_PATH" ]; then
    echo "ERROR: asset list file is not readable: $ASSET_LIST_FILE" >&2
    exit 1
fi

COMMAND_ARGV=(
    --input_dir "$INPUT_DIR"
    --output_dir "$OUTPUT_DIR"
    --asset_list_file "$ASSET_LIST_FILE"
)
printf -v COMMAND_ARGS '%q ' "${COMMAND_ARGV[@]}"
COMMAND_ARGS=${COMMAND_ARGS% }
if [ -n "$EXTRA_MAIN_ARGS" ]; then
    COMMAND_ARGS="$COMMAND_ARGS $EXTRA_MAIN_ARGS"
fi

exec "$PYTHON_BIN" "$SUBMIT_PY" \
    --total "$TOTAL" \
    --name "$NAME" \
    --command_args "$COMMAND_ARGS" \
    "${FORWARD_ARGS[@]}"
