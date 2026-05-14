#!/bin/bash
set -euo pipefail
# DLC annotation job launcher.
# Usage: bash launch_job.sh <TASK_NAME> <CHUNK_ID> <CHUNK_TOTAL> [DATA_SOURCES] [EXTRA_MAIN_ARGS...]
# Final run_task contract: run_task.sh <chunk_id> <chunk_total> [extra main.py flags...]

if [ $# -lt 3 ]; then
    echo "Usage: bash launch_job.sh <TASK_NAME> <CHUNK_ID> <CHUNK_TOTAL> [DATA_SOURCES] [EXTRA_MAIN_ARGS...]"
    echo ""
    echo "Arguments:"
    echo "  TASK_NAME     : Name of the task (e.g., annotate_assets)"
    echo "  CHUNK_ID      : Current chunk ID (0-indexed, e.g., 0)"
    echo "  CHUNK_TOTAL   : Total number of chunks (e.g., 4)"
    echo "  DATA_SOURCES  : Optional. Comma-separated DLC data source IDs"
    echo "  EXTRA_MAIN_ARGS: Optional. Extra auto_asset_annotator.main flags for chunk mode"
    echo ""
    echo "Environment Variables (can override defaults):"
    echo "  DLC_WORKSPACE_ID : DLC workspace ID (default: 270969)"
    echo "  DLC_RESOURCE_ID  : Optional quota override (default: resolved from GPU template)"
    echo "  DLC_IMAGE        : Docker image URL for VLM inference"
    echo "  DLC_CODE_ROOT    : Code root directory in container"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse command line arguments
TASK_NAME=$1
CHUNK_ID=$2
CHUNK_TOTAL=$3

is_non_negative_int() {
    case "$1" in
        ''|*[!0-9]*) return 1 ;;
        *) return 0 ;;
    esac
}

if ! is_non_negative_int "$CHUNK_ID"; then
    echo "ERROR: CHUNK_ID must be a non-negative integer, got: '$CHUNK_ID'" >&2
    exit 1
fi

if ! is_non_negative_int "$CHUNK_TOTAL" || [ "$CHUNK_TOTAL" -lt 1 ]; then
    echo "ERROR: CHUNK_TOTAL must be a positive integer, got: '$CHUNK_TOTAL'" >&2
    exit 1
fi

if [ "$CHUNK_ID" -ge "$CHUNK_TOTAL" ]; then
    echo "ERROR: CHUNK_ID must be less than CHUNK_TOTAL (got $CHUNK_ID >= $CHUNK_TOTAL)" >&2
    exit 1
fi

# Data sources (optional, with default)
# Default data sources for the VLM annotation project
DATA_SOURCES=${4:-${DLC_DATA_SOURCES:-"d-mzps5b7joy2axmqpa8,d-d49o5g0h2818sw8j1g,d-8wz4emfs21s5ajs9oz"}}

# Extra main.py arguments for run_task.sh batch mode (optional)
EXTRA_ARGS=("${@:5}")

# ========================================================================
# Configuration (can be overridden via environment variables)
# ========================================================================

EXPLICIT_WORKSPACE_ID=${DLC_WORKSPACE_ID:-}
EXPLICIT_RESOURCE_ID=${DLC_RESOURCE_ID:-}

# DLC Workspace ID (default: SmartBot Workspace for dry-run only)
WORKSPACE_ID=${DLC_WORKSPACE_ID:-"270969"}

# Resource profile selector for this repository.
DLC_PROFILE=${DLC_PROFILE:-"local_hf_default"}
case "$DLC_PROFILE" in
    api_light)
        PROFILE_GPU_COUNT=1
        ;;
    local_hf_default)
        PROFILE_GPU_COUNT=1
        ;;
    local_hf_heavy)
        PROFILE_GPU_COUNT=4
        ;;
    *)
        echo "ERROR: Unsupported DLC_PROFILE: $DLC_PROFILE" >&2
        exit 1
        ;;
esac

GPU_COUNT=${DLC_GPU_COUNT:-${DLC_WORKER_GPU:-$PROFILE_GPU_COUNT}}
case "$GPU_COUNT" in
    1)
        TPL_GPU=1
        TPL_CPU=14
        TPL_MEM=100Gi
        TPL_SHMEM=100Gi
        TPL_RES=quota1r947pmazvk
        ;;
    2)
        TPL_GPU=2
        TPL_CPU=28
        TPL_MEM=200Gi
        TPL_SHMEM=200Gi
        TPL_RES=quota1r947pmazvk
        ;;
    4)
        TPL_GPU=4
        TPL_CPU=56
        TPL_MEM=400Gi
        TPL_SHMEM=400Gi
        TPL_RES=quota1r947pmazvk
        ;;
    8)
        TPL_GPU=8
        TPL_CPU=128
        TPL_MEM=960Gi
        TPL_SHMEM=960Gi
        TPL_RES=quotaksvqq2oh2pg
        ;;
    *)
        echo "ERROR: Unsupported GPU count: $GPU_COUNT. Supported values: 1, 2, 4, 8." >&2
        exit 1
        ;;
esac

WORKER_GPU=${DLC_WORKER_GPU:-"$TPL_GPU"}
WORKER_CPU=${DLC_WORKER_CPU:-"$TPL_CPU"}
WORKER_MEMORY=${DLC_WORKER_MEMORY:-"$TPL_MEM"}
WORKER_SHARED_MEMORY=${DLC_WORKER_SHARED_MEMORY:-"$TPL_SHMEM"}
RESOURCE_ID=${DLC_RESOURCE_ID:-"$TPL_RES"}

# Docker Image for VLM Inference
# Using Isaac Sim 4.5.0 image (pre-configured with CUDA and Python)
# This image is verified to work with DLC and contains necessary dependencies
IMAGE=${DLC_IMAGE:-"dsw-registry-vpc.cn-beijing.cr.aliyuncs.com/pai-training-algorithm/isaac-sim:isaacsim450-vnc-v8"}

# Code root directory (mounted in container)
CODE_ROOT=${DLC_CODE_ROOT:-"/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator"}
DLC_BIN=${DLC_BIN:-"$REPO_ROOT/dlc"}

# ========================================================================
# Construct and submit job
# ========================================================================

# Generate unique job name
JOB_NAME="${TASK_NAME}_${CHUNK_ID}_${CHUNK_TOTAL}"

FINAL_COMMAND=""
for ENV_NAME in \
    DLC_WORKER_SETUP_SCRIPT \
    AUTO_ASSET_VENV \
    DLC_PYTHON_RUNTIME \
    UNSLOTH_COMPILE_LOCATION \
    MODEL_BACKEND \
    MODEL_PATH \
    API_BASE_URL \
    API_KEY_ENV \
    HF_HUB_OFFLINE \
    TRANSFORMERS_OFFLINE \
    TOKENIZERS_PARALLELISM
do
    if [ -n "${!ENV_NAME:-}" ]; then
        printf -v QUOTED_ENV_VALUE '%q' "${!ENV_NAME}"
        FINAL_COMMAND+="$ENV_NAME=$QUOTED_ENV_VALUE "
    fi
done

RUN_TASK_COMMAND=("bash" "$CODE_ROOT/scripts/dlc/run_task.sh" "$CHUNK_ID" "$CHUNK_TOTAL" "${EXTRA_ARGS[@]}")
printf -v QUOTED_RUN_TASK_COMMAND '%q ' "${RUN_TASK_COMMAND[@]}"
QUOTED_RUN_TASK_COMMAND=${QUOTED_RUN_TASK_COMMAND% }
FINAL_COMMAND+="$QUOTED_RUN_TASK_COMMAND"

echo "========================================"
echo "DLC Job Submission"
echo "========================================"
echo "Job Name:       $JOB_NAME"
echo "Task:           $TASK_NAME"
echo "Chunk:          $CHUNK_ID / $CHUNK_TOTAL"
echo "DLC Profile:    $DLC_PROFILE"
echo "Code Root:      $CODE_ROOT"
echo "Workspace ID:   $WORKSPACE_ID"
echo "Resource ID:    $RESOURCE_ID"
echo "Worker GPU:     $WORKER_GPU"
echo "Worker CPU:     $WORKER_CPU"
echo "Worker Memory:  $WORKER_MEMORY"
echo "Worker SHM:     $WORKER_SHARED_MEMORY"
echo "Image:          $IMAGE"
echo "Data Sources:   $DATA_SOURCES"
echo "Extra Args:     ${EXTRA_ARGS[*]:-<none>}"
echo "Resolved config summary: profile=$DLC_PROFILE gpu=$WORKER_GPU cpu=$WORKER_CPU memory=$WORKER_MEMORY shared_memory=$WORKER_SHARED_MEMORY resource_id=$RESOURCE_ID"
echo "Final command:  $FINAL_COMMAND"
echo "========================================"

CMD=(
    "$DLC_BIN" submit pytorchjob
    --name="$JOB_NAME"
    --workers=1
    --job_max_running_time_minutes=0
    --worker_gpu="$WORKER_GPU"
    --worker_cpu="$WORKER_CPU"
    --worker_memory="$WORKER_MEMORY"
    --worker_shared_memory="$WORKER_SHARED_MEMORY"
    --worker_image="$IMAGE"
    --workspace_id="$WORKSPACE_ID"
    --resource_id="$RESOURCE_ID"
    --data_sources="$DATA_SOURCES"
    --oversold_type=ForbiddenQuotaOverSold
    --priority=7
    --command="$FINAL_COMMAND"
)
printf 'Resolved submit command:'
printf ' %q' "${CMD[@]}"
printf '\n'

if [ "${DLC_DRY_RUN:-1}" != "0" ] || [ "${DLC_SUBMIT:-0}" != "1" ]; then
    echo "Dry-run only; set DLC_SUBMIT=1 and DLC_DRY_RUN=0 for real submission."
    exit 0
fi

if [ -z "$EXPLICIT_WORKSPACE_ID" ]; then
    echo "ERROR: DLC_WORKSPACE_ID must be explicitly set for real submission" >&2
    exit 1
fi

if [ -z "$EXPLICIT_RESOURCE_ID" ]; then
    echo "ERROR: DLC_RESOURCE_ID must be explicitly set for real submission" >&2
    exit 1
fi

if [ "${DLC_REAL_SUBMIT_CONFIRM:-}" != "$JOB_NAME" ]; then
    echo "ERROR: DLC_REAL_SUBMIT_CONFIRM must exactly match job name '$JOB_NAME' for real submission" >&2
    exit 1
fi

# Verify DLC binary exists on submit host.
DLC_BIN=${DLC_BIN:-"$REPO_ROOT/dlc"}
if [ ! -x "$DLC_BIN" ]; then
    echo "ERROR: DLC binary not found or not executable at $DLC_BIN"
    echo "Please ensure the dlc binary exists at the submit host repo root or set DLC_BIN"
    exit 1
fi

"${CMD[@]}"

echo ""
echo "Job submitted successfully: $JOB_NAME"
echo "Monitor with: $DLC_BIN get job --workspace_id=$WORKSPACE_ID --display_name $JOB_NAME"
