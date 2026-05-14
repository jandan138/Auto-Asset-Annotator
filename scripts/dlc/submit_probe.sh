#!/bin/bash
set -euo pipefail

CODE_ROOT=${DLC_CODE_ROOT:-"/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator"}
SUBMIT_WRAPPER="$CODE_ROOT/scripts/dlc/submit_asset_list.sh"

TOTAL=${TOTAL:-1}
NAME=${NAME:-annotate_probe}
ASSET_LIST_FILE=${ASSET_LIST_FILE:-}
FORWARD_ARGS=()
MODEL_CLI_ARGS=()

while [ $# -gt 0 ]; do
    case "$1" in
        --asset_list_file)
            if [ $# -lt 2 ]; then
                echo "ERROR: --asset_list_file requires a value" >&2
                exit 1
            fi
            ASSET_LIST_FILE="$2"
            FORWARD_ARGS+=("$1" "$2")
            shift 2
            ;;
        --asset_list_file=*)
            ASSET_LIST_FILE=${1#*=}
            FORWARD_ARGS+=("$1")
            shift
            ;;
        *)
            FORWARD_ARGS+=("$1")
            shift
            ;;
    esac
done

if [ -z "${MODEL_BACKEND:-}" ]; then
    echo "ERROR: submit_probe.sh requires explicit MODEL_BACKEND (local_hf, local_gemma4_multimodal, or openai_compatible)" >&2
    exit 1
fi

if [ -z "$ASSET_LIST_FILE" ]; then
    echo "ERROR: submit_probe.sh requires ASSET_LIST_FILE or --asset_list_file <path> so the probe stays tiny and explicit" >&2
    exit 1
fi

case "$MODEL_BACKEND" in
    openai_compatible)
        DLC_PROFILE=${DLC_PROFILE:-api_light}
        ;;
    local_hf)
        DLC_PROFILE=${DLC_PROFILE:-local_hf_default}
        ;;
    local_gemma4_multimodal)
        DLC_PROFILE=${DLC_PROFILE:-local_hf_default}
        ;;
    *)
        echo "ERROR: Unsupported MODEL_BACKEND for probe: $MODEL_BACKEND" >&2
        exit 1
        ;;
esac

if [ "$MODEL_BACKEND" = "local_gemma4_multimodal" ] && [ -z "${MODEL_PATH:-}" ]; then
    echo "ERROR: MODEL_PATH is required when MODEL_BACKEND=local_gemma4_multimodal" >&2
    exit 1
fi

if [ -n "${MODEL_PATH:-}" ]; then
    MODEL_CLI_ARGS+=("--model_path" "$MODEL_PATH")
fi
MODEL_CLI_ARGS+=("--model_backend" "$MODEL_BACKEND")
if [ -n "${API_BASE_URL:-}" ]; then
    MODEL_CLI_ARGS+=("--api_base_url" "$API_BASE_URL")
fi
if [ -n "${API_KEY_ENV:-}" ]; then
    MODEL_CLI_ARGS+=("--api_key_env" "$API_KEY_ENV")
fi

printf -v MODEL_EXTRA_MAIN_ARGS '%q ' "${MODEL_CLI_ARGS[@]}"
MODEL_EXTRA_MAIN_ARGS=${MODEL_EXTRA_MAIN_ARGS% }
if [ -n "${EXTRA_MAIN_ARGS:-}" ]; then
    EXTRA_MAIN_ARGS="$EXTRA_MAIN_ARGS $MODEL_EXTRA_MAIN_ARGS"
else
    EXTRA_MAIN_ARGS="$MODEL_EXTRA_MAIN_ARGS"
fi

export TOTAL NAME DLC_PROFILE ASSET_LIST_FILE MODEL_BACKEND EXTRA_MAIN_ARGS

echo "[probe] TOTAL=$TOTAL NAME=$NAME DLC_PROFILE=$DLC_PROFILE MODEL_BACKEND=$MODEL_BACKEND"
echo "[probe] ASSET_LIST_FILE=$ASSET_LIST_FILE"
echo "[probe] Use --dry-run first. Remove it only for a tiny real submission over this explicit asset list."

exec bash "$SUBMIT_WRAPPER" "${FORWARD_ARGS[@]}"
