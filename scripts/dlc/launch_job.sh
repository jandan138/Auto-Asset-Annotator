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
    echo "  DLC_RESOURCE_ID  : DLC resource quota ID (default: quotalplclkpgjgv)"
    echo "  DLC_IMAGE        : Docker image URL for VLM inference"
    echo "  DLC_CODE_ROOT    : Code root directory in container"
    exit 1
fi

# Parse command line arguments
TASK_NAME=$1
CHUNK_ID=$2
CHUNK_TOTAL=$3

# Data sources (optional, with default)
# Default data sources for the VLM annotation project
DATA_SOURCES=${4:-"d-mzps5b7joy2axmqpa8,d-d49o5g0h2818sw8j1g,d-8wz4emfs21s5ajs9oz"}

# Extra main.py arguments for run_task.sh batch mode (optional)
EXTRA_ARGS=("${@:5}")

# ========================================================================
# Configuration (can be overridden via environment variables)
# ========================================================================

# DLC Workspace ID (default: SmartBot Workspace)
WORKSPACE_ID=${DLC_WORKSPACE_ID:-"270969"}

# Resource profile selector for this repository.
DLC_PROFILE=${DLC_PROFILE:-"local_hf_default"}
case "$DLC_PROFILE" in
    api_light)
        PROFILE_GPU=1
        PROFILE_CPU=8
        PROFILE_MEMORY=48Gi
        PROFILE_SHARED_MEMORY=48Gi
        PROFILE_RESOURCE_ID="quotalplclkpgjgv"
        ;;
    local_hf_default)
        PROFILE_GPU=1
        PROFILE_CPU=16
        PROFILE_MEMORY=118Gi
        PROFILE_SHARED_MEMORY=118Gi
        PROFILE_RESOURCE_ID="quotalplclkpgjgv"
        ;;
    local_hf_heavy)
        PROFILE_GPU=1
        PROFILE_CPU=24
        PROFILE_MEMORY=160Gi
        PROFILE_SHARED_MEMORY=160Gi
        PROFILE_RESOURCE_ID="quotalplclkpgjgv"
        ;;
    *)
        echo "ERROR: Unsupported DLC_PROFILE: $DLC_PROFILE" >&2
        exit 1
        ;;
esac

WORKER_GPU=${DLC_WORKER_GPU:-"$PROFILE_GPU"}
WORKER_CPU=${DLC_WORKER_CPU:-"$PROFILE_CPU"}
WORKER_MEMORY=${DLC_WORKER_MEMORY:-"$PROFILE_MEMORY"}
WORKER_SHARED_MEMORY=${DLC_WORKER_SHARED_MEMORY:-"$PROFILE_SHARED_MEMORY"}
RESOURCE_ID=${DLC_RESOURCE_ID:-"$PROFILE_RESOURCE_ID"}

# Docker Image for VLM Inference
# Using Isaac Sim 4.5.0 image (pre-configured with CUDA and Python)
# This image is verified to work with DLC and contains necessary dependencies
IMAGE=${DLC_IMAGE:-"dsw-registry-vpc.cn-beijing.cr.aliyuncs.com/pai-training-algorithm/isaac-sim:isaacsim450-vnc-v8"}

# Code root directory (mounted in container)
CODE_ROOT=${DLC_CODE_ROOT:-"/cpfs/shared/simulation/zhuzihou/dev/Auto-Asset-Annotator"}

# ========================================================================
# Construct and submit job
# ========================================================================

# Generate unique job name
JOB_NAME="${TASK_NAME}_${CHUNK_ID}_${CHUNK_TOTAL}"
RUN_TASK_COMMAND=("bash" "$CODE_ROOT/scripts/dlc/run_task.sh" "$CHUNK_ID" "$CHUNK_TOTAL" "${EXTRA_ARGS[@]}")
printf -v FINAL_COMMAND '%q ' "${RUN_TASK_COMMAND[@]}"
FINAL_COMMAND=${FINAL_COMMAND% }

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

# Verify DLC binary exists
DLC_BIN=${DLC_BIN:-"$CODE_ROOT/dlc"}
if [ ! -x "$DLC_BIN" ]; then
    echo "ERROR: DLC binary not found or not executable at $DLC_BIN"
    echo "Please ensure the dlc binary exists at the code root or set DLC_BIN environment variable"
    exit 1
fi

"$DLC_BIN" submit pytorchjob \
    --name="$JOB_NAME" \
    --workers=1 \
    --job_max_running_time_minutes=0 \
    --worker_gpu="$WORKER_GPU" \
    --worker_cpu="$WORKER_CPU" \
    --worker_memory="$WORKER_MEMORY" \
    --worker_shared_memory="$WORKER_SHARED_MEMORY" \
    --worker_image="$IMAGE" \
    --workspace_id="$WORKSPACE_ID" \
    --resource_id="$RESOURCE_ID" \
    --data_sources="$DATA_SOURCES" \
    --oversold_type=ForbiddenQuotaOverSold \
    --priority=7 \
    --command="$FINAL_COMMAND"

echo ""
echo "Job submitted successfully: $JOB_NAME"
echo "Monitor with: $DLC_BIN get job --workspace_id=$WORKSPACE_ID --display_name $JOB_NAME"
