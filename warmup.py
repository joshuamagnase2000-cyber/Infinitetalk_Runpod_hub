"""Startup warm-up: run one minimal ComfyUI workflow so the heavy InfiniteTalk /
Wan / VAE / text-encoder / clip-vision / audio models are loaded into VRAM
*before* the RunPod handler starts accepting jobs.

Without this, ComfyUI lazy-loads ~26GB of weights only when the first real job
runs, so the first user eats the full cold-start cost. Running a tiny job here
moves that cost onto worker boot instead. Combined with FlashBoot snapshotting
and/or an active worker, the warm VRAM state is then retained across requests.

This script is intentionally best-effort: any failure is logged and swallowed so
a bad warm-up can never block the endpoint from serving (entrypoint.sh calls it
with `|| true`).
"""

import os
import logging

from comfy_client import (
    load_workflow,
    get_workflow_path,
    connect_websocket,
    get_videos,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("warmup")

# 워밍업은 가장 흔한 경로인 I2V single 을 사용한다.
# (I2V_multi 의 InfiniteTalk-Multi 모델은 첫 multi 요청 시 로드됨)
INPUT_TYPE = "image"
PERSON_COUNT = "single"

# 저장소에 포함된 예제 자산 — 별도 다운로드 불필요
EXAMPLE_IMAGE = "/examples/image.jpg"
EXAMPLE_AUDIO = "/examples/audio.mp3"

# 연산을 최소화하기 위한 워밍업 전용 설정 (목표는 가중치 VRAM 적재이지 품질이 아님).
# 비용을 0 에 가깝게 만들기 위해 해상도/프레임/샘플링 스텝을 모두 최소화한다.
WARMUP_PROMPT = "warmup"
WARMUP_MAX_FRAME = 81  # InfiniteTalk 단일 청크 — 더 줄이면 의미 없음
WARMUP_RESOLUTION = 256  # 가중치는 동일하게 적재되지만 연산/메모리는 대폭 감소
WARMUP_STEPS = 1  # 디퓨전 샘플링을 1 스텝으로 — 모델만 적재하고 연산은 최소


def _set_sampler_steps(prompt, steps):
    """WanVideoSampler 노드를 찾아 샘플링 스텝 수를 주입한다 (handler 와 동일한 탐색)."""
    node_id = None
    if "128" in prompt and prompt["128"].get("class_type") == "WanVideoSampler":
        node_id = "128"
    else:
        for nid, node in prompt.items():
            if node.get("class_type") == "WanVideoSampler":
                node_id = nid
                break
    if node_id:
        prompt[node_id].setdefault("inputs", {})["steps"] = steps
        logger.info(f"노드 {node_id} (WanVideoSampler) steps={steps} 로 설정")
    else:
        logger.warning("WanVideoSampler 노드를 찾지 못해 기본 steps 사용")


def run_warmup():
    workflow_path = get_workflow_path(INPUT_TYPE, PERSON_COUNT)
    logger.info(f"🔥 워밍업 시작: {workflow_path}")

    # 예제 자산이 없으면 워밍업을 건너뛴다 (정상 동작에는 영향 없음)
    for asset in (EXAMPLE_IMAGE, EXAMPLE_AUDIO):
        if not os.path.exists(asset):
            logger.warning(f"⚠️ 워밍업 자산 없음, 건너뜀: {asset}")
            return

    prompt = load_workflow(workflow_path)

    # handler.py 와 동일한 노드들에 최소 입력 주입
    prompt["284"]["inputs"]["image"] = EXAMPLE_IMAGE
    prompt["125"]["inputs"]["audio"] = EXAMPLE_AUDIO
    prompt["241"]["inputs"]["positive_prompt"] = WARMUP_PROMPT
    prompt["245"]["inputs"]["value"] = WARMUP_RESOLUTION
    prompt["246"]["inputs"]["value"] = WARMUP_RESOLUTION
    prompt["270"]["inputs"]["value"] = WARMUP_MAX_FRAME
    _set_sampler_steps(prompt, WARMUP_STEPS)

    ws = connect_websocket()
    try:
        get_videos(ws, prompt, INPUT_TYPE, PERSON_COUNT)
        logger.info("✅ 워밍업 완료: 모델이 VRAM 에 적재되었습니다.")
    finally:
        ws.close()


if __name__ == "__main__":
    try:
        run_warmup()
    except Exception as e:
        # 워밍업 실패는 치명적이지 않다 — 로그만 남기고 핸들러는 정상 기동
        logger.warning(f"⚠️ 워밍업 실패(무시하고 계속): {e}")
