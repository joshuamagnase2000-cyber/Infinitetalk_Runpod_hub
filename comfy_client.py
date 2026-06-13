"""ComfyUI client helpers shared by the RunPod handler and the warm-up script.

Keeping these in a standalone module (rather than handler.py) lets warmup.py
reuse the exact submit/wait logic without importing handler.py — which would
otherwise call runpod.serverless.start() at import time.
"""

import os
import json
import time
import uuid
import logging
import urllib.request
import urllib.parse

import websocket

logger = logging.getLogger(__name__)

# ComfyUI 주소와 클라이언트 ID는 프로세스 전역에서 공유되어야 한다.
# (queue_prompt 와 websocket 이 동일한 client_id 를 사용해야 실행 메시지를 수신함)
server_address = os.getenv("SERVER_ADDRESS", "127.0.0.1")
client_id = str(uuid.uuid4())


def queue_prompt(prompt, input_type="image", person_count="single"):
    url = f"http://{server_address}:8188/prompt"
    logger.info(f"Queueing prompt to: {url}")
    p = {"prompt": prompt, "client_id": client_id}
    data = json.dumps(p).encode("utf-8")

    # 디버깅을 위해 워크플로우 내용 로깅
    logger.info(f"워크플로우 노드 수: {len(prompt)}")
    if input_type == "image":
        logger.info(
            f"이미지 노드(284) 설정: {prompt.get('284', {}).get('inputs', {}).get('image', 'NOT_FOUND')}"
        )
    else:
        logger.info(
            f"비디오 노드(228) 설정: {prompt.get('228', {}).get('inputs', {}).get('video', 'NOT_FOUND')}"
        )
    logger.info(
        f"오디오 노드(125) 설정: {prompt.get('125', {}).get('inputs', {}).get('audio', 'NOT_FOUND')}"
    )
    logger.info(
        f"텍스트 노드(241) 설정: {prompt.get('241', {}).get('inputs', {}).get('positive_prompt', 'NOT_FOUND')}"
    )
    if person_count == "multi":
        if "307" in prompt:
            logger.info(
                f"두 번째 오디오 노드(307) 설정: {prompt.get('307', {}).get('inputs', {}).get('audio', 'NOT_FOUND')}"
            )
        elif "313" in prompt:
            logger.info(
                f"두 번째 오디오 노드(313) 설정: {prompt.get('313', {}).get('inputs', {}).get('audio', 'NOT_FOUND')}"
            )

    req = urllib.request.Request(url, data=data)
    req.add_header("Content-Type", "application/json")

    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read())
        logger.info(f"프롬프트 전송 성공: {result}")
        return result
    except urllib.error.HTTPError as e:
        logger.error(f"HTTP 에러 발생: {e.code} - {e.reason}")
        logger.error(f"응답 내용: {e.read().decode('utf-8')}")
        raise
    except Exception as e:
        logger.error(f"프롬프트 전송 중 오류: {e}")
        raise


def get_image(filename, subfolder, folder_type):
    url = f"http://{server_address}:8188/view"
    logger.info(f"Getting image from: {url}")
    data = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    url_values = urllib.parse.urlencode(data)
    with urllib.request.urlopen(f"{url}?{url_values}") as response:
        return response.read()


def get_history(prompt_id):
    url = f"http://{server_address}:8188/history/{prompt_id}"
    logger.info(f"Getting history from: {url}")
    with urllib.request.urlopen(url) as response:
        return json.loads(response.read())


def get_videos(ws, prompt, input_type="image", person_count="single"):
    prompt_id = queue_prompt(prompt, input_type, person_count)["prompt_id"]
    logger.info(f"워크플로우 실행 시작: prompt_id={prompt_id}")

    output_videos = {}
    while True:
        out = ws.recv()
        if isinstance(out, str):
            message = json.loads(out)
            if message["type"] == "executing":
                data = message["data"]
                if data["node"] is not None:
                    logger.info(f"노드 실행 중: {data['node']}")
                if data["node"] is None and data["prompt_id"] == prompt_id:
                    logger.info("워크플로우 실행 완료")
                    break
        else:
            continue

    logger.info(f"히스토리 조회 중: prompt_id={prompt_id}")
    history = get_history(prompt_id)[prompt_id]
    logger.info(f"출력 노드 수: {len(history['outputs'])}")

    for node_id in history["outputs"]:
        node_output = history["outputs"][node_id]
        videos_output = []
        if "gifs" in node_output:
            logger.info(
                f"노드 {node_id}에서 {len(node_output['gifs'])}개의 비디오 발견"
            )
            for idx, video in enumerate(node_output["gifs"]):
                # fullpath를 그대로 반환 (base64 인코딩하지 않음)
                video_path = video["fullpath"]
                logger.info(f"비디오 파일 경로: {video_path}")

                # 파일 존재 여부 및 크기 확인
                if os.path.exists(video_path):
                    file_size = os.path.getsize(video_path)
                    logger.info(
                        f"비디오 {idx+1} 발견: {video_path} (크기: {file_size} bytes)"
                    )
                else:
                    logger.warning(f"비디오 파일이 존재하지 않습니다: {video_path}")

                videos_output.append(video_path)
        else:
            logger.info(f"노드 {node_id}에 비디오 출력 없음")
        output_videos[node_id] = videos_output

    logger.info(f"총 {len(output_videos)}개 노드에서 비디오 파일 경로 수집 완료")
    return output_videos


def load_workflow(workflow_path):
    with open(workflow_path, "r") as file:
        return json.load(file)


def get_workflow_path(input_type, person_count):
    """input_type과 person_count에 따라 적절한 워크플로우 파일 경로를 반환"""
    if input_type == "image":
        if person_count == "single":
            return "/I2V_single.json"
        else:  # multi
            return "/I2V_multi.json"
    else:  # video
        if person_count == "single":
            return "/V2V_single.json"
        else:  # multi
            return "/V2V_multi.json"


def connect_websocket():
    """ComfyUI HTTP 준비 확인 후 websocket 을 연결하여 반환한다.

    handler 와 warmup 이 동일한 연결 로직(재시도 포함)을 공유한다.
    """
    # HTTP 연결 확인 (최대 3분)
    http_url = f"http://{server_address}:8188/"
    logger.info(f"Checking HTTP connection to: {http_url}")
    max_http_attempts = 180
    for http_attempt in range(max_http_attempts):
        try:
            urllib.request.urlopen(http_url, timeout=5)
            logger.info(f"HTTP 연결 성공 (시도 {http_attempt+1})")
            break
        except Exception as e:
            logger.warning(
                f"HTTP 연결 실패 (시도 {http_attempt+1}/{max_http_attempts}): {e}"
            )
            if http_attempt == max_http_attempts - 1:
                raise Exception(
                    "ComfyUI 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요."
                )
            time.sleep(1)

    # 웹소켓 연결 시도 (최대 3분)
    ws_url = f"ws://{server_address}:8188/ws?clientId={client_id}"
    logger.info(f"Connecting to WebSocket: {ws_url}")
    ws = websocket.WebSocket()
    max_attempts = int(180 / 5)
    for attempt in range(max_attempts):
        try:
            ws.connect(ws_url)
            logger.info(f"웹소켓 연결 성공 (시도 {attempt+1})")
            return ws
        except Exception as e:
            logger.warning(f"웹소켓 연결 실패 (시도 {attempt+1}/{max_attempts}): {e}")
            if attempt == max_attempts - 1:
                raise Exception("웹소켓 연결 시간 초과 (3분)")
            time.sleep(5)
