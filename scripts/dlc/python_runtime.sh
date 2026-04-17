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

MODEL_BACKEND_VALUE=${MODEL_BACKEND:-local_hf}
if [ "$MODEL_BACKEND_VALUE" = "openai_compatible" ]; then
    if [ -z "${API_BASE_URL:-}" ]; then
        echo "ERROR: API_BASE_URL is required when MODEL_BACKEND=openai_compatible" >&2
        exit 1
    fi
    if [ -z "${API_KEY_ENV:-}" ]; then
        echo "ERROR: API_KEY_ENV is required when MODEL_BACKEND=openai_compatible" >&2
        exit 1
    fi
    if [ -z "${!API_KEY_ENV:-}" ]; then
        echo "ERROR: Environment variable named by API_KEY_ENV ('$API_KEY_ENV') is not set" >&2
        exit 1
    fi
fi

if [ "$MODEL_BACKEND_VALUE" = "local_hf" ] && [ -n "${MODEL_PATH:-}" ]; then
    case "$MODEL_PATH" in
        /*|./*|../*)
            if [ ! -e "$MODEL_PATH" ]; then
                echo "ERROR: MODEL_PATH does not exist: $MODEL_PATH" >&2
                exit 1
            fi
            ;;
    esac
fi

exec "$PYTHON_BIN" "$@"
