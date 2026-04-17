#!/bin/bash
set -euo pipefail

CODE_ROOT=${DLC_CODE_ROOT:-"/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator"}
SUBMIT_PY="$CODE_ROOT/scripts/dlc/submit_batch.py"
PYTHON_BIN=${PYTHON_BIN:-python}

TOTAL=${TOTAL:-4}
NAME=${NAME:-retry_failed}
INPUT_DIR=${INPUT_DIR:-/data/assets}
OUTPUT_DIR=${OUTPUT_DIR:-/data/results}
ASSET_LIST_FILE=${ASSET_LIST_FILE:-archive/temp_lists/failed_assets.txt}
EXTRA_MAIN_ARGS=${EXTRA_MAIN_ARGS:-}

FAILED_LIST_CHECK_PATH="$ASSET_LIST_FILE"
if [ ! -e "$FAILED_LIST_CHECK_PATH" ] && [ -e "$CODE_ROOT/$ASSET_LIST_FILE" ]; then
    FAILED_LIST_CHECK_PATH="$CODE_ROOT/$ASSET_LIST_FILE"
fi
if [ ! -r "$FAILED_LIST_CHECK_PATH" ]; then
    echo "ERROR: failed-asset list is not readable: $ASSET_LIST_FILE" >&2
    exit 1
fi

COMMAND_ARGV=(
    --input_dir "$INPUT_DIR"
    --output_dir "$OUTPUT_DIR"
    --asset_list_file "$ASSET_LIST_FILE"
    --force
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
    "$@"
