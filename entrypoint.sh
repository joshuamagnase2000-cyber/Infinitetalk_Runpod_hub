#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Start ComfyUI in the background
echo "Starting ComfyUI in the background..."
python /ComfyUI/main.py --listen &

# Wait for ComfyUI to be ready
echo "Waiting for ComfyUI to be ready..."
max_wait=300  # 최대 5분 대기 (safety margin for cold starts)
wait_count=0
while [ $wait_count -lt $max_wait ]; do
    if curl -s http://127.0.0.1:8188/ > /dev/null 2>&1; then
        echo "ComfyUI is ready!"
        break
    fi
    echo "Waiting for ComfyUI... ($wait_count/$max_wait)"
    sleep 2
    wait_count=$((wait_count + 2))
done

if [ $wait_count -ge $max_wait ]; then
    echo "Error: ComfyUI failed to start within $max_wait seconds"
    exit 1
fi

# Warm up the model cache before accepting jobs so the first request isn't slow.
# Loads the heavy weights into VRAM during boot instead of on the first user job.
# Best-effort: failures must never block the handler from starting (|| true).
# Disable by setting WARMUP_ENABLED=false on the endpoint.
if [ "${WARMUP_ENABLED:-true}" = "true" ]; then
    echo "Warming up models (loading weights into VRAM)..."
    python /warmup.py || echo "Warm-up failed or skipped; continuing to handler."
else
    echo "Warm-up disabled (WARMUP_ENABLED=${WARMUP_ENABLED})."
fi

# Start the handler in the foreground
# 이 스크립트가 컨테이너의 메인 프로세스가 됩니다.
echo "Starting the handler..."
exec python handler.py