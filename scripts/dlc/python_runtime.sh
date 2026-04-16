#!/bin/bash
set -euo pipefail

CODE_ROOT=${DLC_CODE_ROOT:-"/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator"}

if [ -d "$CODE_ROOT/.venv_dlc" ]; then
    VENV_PATH="$CODE_ROOT/.venv_dlc"
elif [ -d "$CODE_ROOT/.venv" ]; then
    VENV_PATH="$CODE_ROOT/.venv"
else
    echo "ERROR: No virtual environment found at $CODE_ROOT/.venv_dlc or $CODE_ROOT/.venv" >&2
    exit 1
fi

PYTHON_BIN="$VENV_PATH/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
    echo "ERROR: Python not found or not executable at $PYTHON_BIN" >&2
    exit 1
fi

export PYTHONUNBUFFERED=1
if [ -n "${PYTHONPATH:-}" ]; then
    export PYTHONPATH="$CODE_ROOT:$PYTHONPATH"
else
    export PYTHONPATH="$CODE_ROOT"
fi

cd "$CODE_ROOT"

if ! "$PYTHON_BIN" -c "import auto_asset_annotator" >/dev/null 2>&1; then
    echo "ERROR: Failed to import auto_asset_annotator with $PYTHON_BIN from $CODE_ROOT" >&2
    exit 1
fi

exec "$PYTHON_BIN" "$@"
