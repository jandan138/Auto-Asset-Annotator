#!/bin/bash
set -euo pipefail

CODE_ROOT=${DLC_CODE_ROOT:-"/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator"}

if [ -n "${DLC_WORKER_SETUP_SCRIPT:-}" ] && [ "${AUTO_ASSET_WORKER_SETUP_SOURCED:-0}" != "1" ]; then
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
fi

if [ -n "${AUTO_ASSET_VENV:-}" ]; then
    VENV_PATH="$AUTO_ASSET_VENV"
elif [ -d "$CODE_ROOT/.venv_dlc" ]; then
    VENV_PATH="$CODE_ROOT/.venv_dlc"
elif [ -d "$CODE_ROOT/.venv" ]; then
    VENV_PATH="$CODE_ROOT/.venv"
else
    echo "ERROR: No virtual environment found. Set AUTO_ASSET_VENV or create $CODE_ROOT/.venv_dlc or $CODE_ROOT/.venv" >&2
    exit 1
fi

PYTHON_BIN="$VENV_PATH/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
    echo "ERROR: Python not found or not executable at $PYTHON_BIN" >&2
    exit 1
fi

export PYTHONUNBUFFERED=1
CODE_SRC="$CODE_ROOT/src"
if [ -n "${PYTHONPATH:-}" ]; then
    export PYTHONPATH="$CODE_SRC:$CODE_ROOT:$PYTHONPATH"
else
    export PYTHONPATH="$CODE_SRC:$CODE_ROOT"
fi

cd "$CODE_ROOT"

if ! "$PYTHON_BIN" -c "import auto_asset_annotator" >/dev/null 2>&1; then
    echo "ERROR: Failed to import auto_asset_annotator with $PYTHON_BIN from $CODE_ROOT" >&2
    exit 1
fi

MODEL_BACKEND_VALUE=${MODEL_BACKEND:-local_hf}
MODEL_PATH_VALUE=${MODEL_PATH:-}
API_BASE_URL_VALUE=${API_BASE_URL:-}
API_KEY_ENV_VALUE=${API_KEY_ENV:-}

ARGS=("$@")
ARG_INDEX=0
while [ "$ARG_INDEX" -lt "${#ARGS[@]}" ]; do
    ARG=${ARGS[$ARG_INDEX]}
    case "$ARG" in
        --model_backend)
            NEXT_INDEX=$((ARG_INDEX + 1))
            if [ "$NEXT_INDEX" -lt "${#ARGS[@]}" ]; then
                MODEL_BACKEND_VALUE=${ARGS[$NEXT_INDEX]}
                ARG_INDEX=$((ARG_INDEX + 2))
                continue
            fi
            ;;
        --model_backend=*)
            MODEL_BACKEND_VALUE=${ARG#*=}
            ;;
        --model_path)
            NEXT_INDEX=$((ARG_INDEX + 1))
            if [ "$NEXT_INDEX" -lt "${#ARGS[@]}" ]; then
                MODEL_PATH_VALUE=${ARGS[$NEXT_INDEX]}
                ARG_INDEX=$((ARG_INDEX + 2))
                continue
            fi
            ;;
        --model_path=*)
            MODEL_PATH_VALUE=${ARG#*=}
            ;;
        --api_base_url)
            NEXT_INDEX=$((ARG_INDEX + 1))
            if [ "$NEXT_INDEX" -lt "${#ARGS[@]}" ]; then
                API_BASE_URL_VALUE=${ARGS[$NEXT_INDEX]}
                ARG_INDEX=$((ARG_INDEX + 2))
                continue
            fi
            ;;
        --api_base_url=*)
            API_BASE_URL_VALUE=${ARG#*=}
            ;;
        --api_key_env)
            NEXT_INDEX=$((ARG_INDEX + 1))
            if [ "$NEXT_INDEX" -lt "${#ARGS[@]}" ]; then
                API_KEY_ENV_VALUE=${ARGS[$NEXT_INDEX]}
                ARG_INDEX=$((ARG_INDEX + 2))
                continue
            fi
            ;;
        --api_key_env=*)
            API_KEY_ENV_VALUE=${ARG#*=}
            ;;
    esac
    ARG_INDEX=$((ARG_INDEX + 1))
done

if [ "$MODEL_BACKEND_VALUE" = "openai_compatible" ]; then
    if [ -z "$API_BASE_URL_VALUE" ]; then
        echo "ERROR: API_BASE_URL is required when MODEL_BACKEND=openai_compatible" >&2
        exit 1
    fi
    if [ -z "$API_KEY_ENV_VALUE" ]; then
        echo "ERROR: API_KEY_ENV is required when MODEL_BACKEND=openai_compatible" >&2
        exit 1
    fi
    if [ -z "${!API_KEY_ENV_VALUE:-}" ]; then
        echo "ERROR: Environment variable named by API_KEY_ENV ('$API_KEY_ENV_VALUE') is not set" >&2
        exit 1
    fi
fi

if [ "$MODEL_BACKEND_VALUE" = "local_gemma4_multimodal" ] && [ -z "$MODEL_PATH_VALUE" ]; then
    echo "ERROR: MODEL_PATH is required when MODEL_BACKEND=local_gemma4_multimodal" >&2
    exit 1
fi

if { [ "$MODEL_BACKEND_VALUE" = "local_hf" ] || [ "$MODEL_BACKEND_VALUE" = "local_gemma4_multimodal" ]; } && [ -n "$MODEL_PATH_VALUE" ]; then
    case "$MODEL_PATH_VALUE" in
        /*|./*|../*)
            if [ ! -e "$MODEL_PATH_VALUE" ]; then
                echo "ERROR: MODEL_PATH does not exist: $MODEL_PATH_VALUE" >&2
                exit 1
            fi
            ;;
    esac
fi

exec "$PYTHON_BIN" "$@"
