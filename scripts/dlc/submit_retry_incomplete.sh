#!/bin/bash
set -euo pipefail

CODE_ROOT=${DLC_CODE_ROOT:-"/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator"}
SUBMIT_PY="$CODE_ROOT/scripts/dlc/submit_batch.py"
PYTHON_BIN=${PYTHON_BIN:-python}

TOTAL=${TOTAL:-4}
NAME=${NAME:-retry_incomplete}
INPUT_DIR=${INPUT_DIR:-/data/assets}
OUTPUT_DIR=${OUTPUT_DIR:-/data/results}
EXTRA_MAIN_ARGS=${EXTRA_MAIN_ARGS:-}

COMMAND_ARGV=(--input_dir "$INPUT_DIR" --output_dir "$OUTPUT_DIR" --retry_incomplete)
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
