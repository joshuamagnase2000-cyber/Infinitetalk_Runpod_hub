# InfiniteTalk for RunPod Serverless
[한국어 README 보기](README_kr.md)

This project is a template designed to easily deploy and use [InfiniteTalk](https://github.com/Kijai/InfiniteTalk) in the RunPod Serverless environment.

[![Runpod](https://api.runpod.io/badge/wlsdml1114/InfiniteTalk_Runpod_hub)](https://console.runpod.io/hub/wlsdml1114/InfiniteTalk_Runpod_hub)

InfiniteTalk is an AI model that takes a single portrait image and speech audio as input to generate natural lip-sync videos with infinite talking capabilities.

## 🎨 Engui Studio Integration

[![EnguiStudio](https://raw.githubusercontent.com/wlsdml1114/Engui_Studio/main/assets/banner.png)](https://github.com/wlsdml1114/Engui_Studio)

This InfiniteTalk template is primarily designed for **Engui Studio**, a comprehensive AI model management platform. While it can be used via API, Engui Studio provides enhanced features and broader model support.

**Engui Studio Benefits:**
- **Expanded Model Support**: Access to a wider variety of AI models beyond what's available through API
- **Enhanced User Interface**: Intuitive workflow management and model selection
- **Advanced Features**: Additional tools and capabilities for AI model deployment
- **Seamless Integration**: Optimized for Engui Studio's ecosystem

> **Note**: While this template works perfectly with API calls, Engui Studio users will have access to additional models and features that are planned for future releases.

## ✨ Key Features

*   **Infinite Talking**: Generates continuous talking videos without limitations on duration.
*   **High-Quality Lip-sync**: Lip movements are precisely synchronized with the input audio.
*   **Real-time Video Generation**: Creates videos synchronized with input audio at high speed.
*   **ComfyUI Integration**: Built on top of ComfyUI for flexible workflow management.
*   **Multiple Workflow Support**: Supports both Image-to-Video (I2V) and Video-to-Video (V2V) workflows.
*   **Single & Multi-Person**: Handles both single-person and multi-person talking scenarios.

## 🚀 RunPod Serverless Template

This template includes all the necessary components to run InfiniteTalk as a RunPod Serverless Worker.

*   **Dockerfile**: Configures the environment and installs all dependencies required for model execution.
*   **handler.py**: Implements the handler function that processes requests for RunPod Serverless.
*   **comfy_client.py**: Shared ComfyUI client helpers (queue/submit/wait) used by both the handler and the warm-up script.
*   **warmup.py**: Startup warm-up that pre-loads model weights into VRAM to reduce cold start (see [Cold Start Optimization](#-cold-start-optimization)).
*   **entrypoint.sh**: Performs initialization tasks when the worker starts.
*   **I2V_single.json**: Image-to-Video single-person workflow configuration.
*   **I2V_multi.json**: Image-to-Video multi-person workflow configuration.
*   **V2V_single.json**: Video-to-Video single-person workflow configuration.
*   **V2V_multi.json**: Video-to-Video multi-person workflow configuration.

### Input

The `input` object must contain the following fields. Images, videos, and audio can be input using **path, URL, or Base64** - one method for each.

#### Workflow Selection Parameters
| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `input_type` | `string` | No | `"image"` | Type of input: `"image"` for Image-to-Video (I2V) or `"video"` for Video-to-Video (V2V) |
| `person_count` | `string` | No | `"single"` | Number of people: `"single"` for one person or `"multi"` for multiple people |

#### Image Input (for I2V workflows - use only one)
| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `image_path` | `string` | No | `/examples/image.jpg` | Local path to the portrait image for lip-sync |
| `image_url` | `string` | No | `/examples/image.jpg` | URL to the portrait image for lip-sync |
| `image_base64` | `string` | No | `/examples/image.jpg` | Base64 encoded string of the portrait image for lip-sync |

#### Video Input (for V2V workflows - use only one)
| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `video_path` | `string` | No | `/examples/image.jpg` | Local path to the input video file |
| `video_url` | `string` | No | `/examples/image.jpg` | URL to the input video file |
| `video_base64` | `string` | No | `/examples/image.jpg` | Base64 encoded string of the input video file |

#### Audio Input (use only one)
| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `wav_path` | `string` | No | `/examples/audio.mp3` | Local path to the audio file (WAV/MP3 format supported) |
| `wav_url` | `string` | No | `/examples/audio.mp3` | URL to the audio file (WAV/MP3 format supported) |
| `wav_base64` | `string` | No | `/examples/audio.mp3` | Base64 encoded string of the audio file (WAV/MP3 format supported) |

#### Multi-Person Audio Input (for multi-person workflows - use only one)
| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `wav_path_2` | `string` | No | Same as first audio | Local path to the second audio file for multi-person scenarios |
| `wav_url_2` | `string` | No | Same as first audio | URL to the second audio file for multi-person scenarios |
| `wav_base64_2` | `string` | No | Same as first audio | Base64 encoded string of the second audio file for multi-person scenarios |

#### Other Parameters
| Parameter | Type | Required | Default | Description |
| --- | --- | --- | --- | --- |
| `prompt` | `string` | No | `"A person talking naturally"` | Description text for the video to be generated |
| `width` | `integer` | No | `512` | Width of the output video in pixels |
| `height` | `integer` | No | `512` | Height of the output video in pixels |
| `max_frame` | `integer` | No | Auto-calculated | Maximum number of frames for the output video (automatically calculated based on audio duration if not provided) |
| `force_offload` | `boolean` | No | `true` | Whether to offload model components to CPU during inference. Set to `false` for ~1.5x faster processing on high-VRAM GPUs (24GB+). Default `true` prevents OOM on smaller GPUs. |
| `network_volume` | `boolean` | No | `false` | Whether to use network volume for output storage. If `true`, returns file path instead of Base64 data |

**Request Examples:**

#### 1. I2V Single (Image-to-Video Single Person)
```json
{
  "input": {
    "input_type": "image",
    "person_count": "single",
    "prompt": "A person is talking in a natural way.",
    "image_url": "https://example.com/portrait.jpg",
    "wav_url": "https://example.com/audio.wav",
    "width": 512,
    "height": 512
  }
}
```

#### 2. I2V Multi (Image-to-Video Multi Person)
```json
{
  "input": {
    "input_type": "image",
    "person_count": "multi",
    "prompt": "Two people having a conversation.",
    "image_url": "https://example.com/portrait.jpg",
    "wav_url": "https://example.com/audio1.wav",
    "wav_url_2": "https://example.com/audio2.wav",
    "width": 512,
    "height": 512
  }
}
```

#### 3. V2V Single (Video-to-Video Single Person)
```json
{
  "input": {
    "input_type": "video",
    "person_count": "single",
    "prompt": "A person singing a song.",
    "video_url": "https://example.com/input_video.mp4",
    "wav_url": "https://example.com/audio.wav",
    "width": 512,
    "height": 512
  }
}
```

#### 4. V2V Multi (Video-to-Video Multi Person)
```json
{
  "input": {
    "input_type": "video",
    "person_count": "multi",
    "prompt": "Two people talking in a video.",
    "video_url": "https://example.com/input_video.mp4",
    "wav_url": "https://example.com/audio1.wav",
    "wav_url_2": "https://example.com/audio2.wav",
    "width": 512,
    "height": 512
  }
}
```

#### 5. Using Base64 (I2V Single Example)
```json
{
  "input": {
    "input_type": "image",
    "person_count": "single",
    "prompt": "A person is talking in a natural way.",
    "image_base64": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD...",
    "wav_base64": "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=",
    "width": 512,
    "height": 512
  }
}
```

#### 6. Using Local Paths (V2V Single Example)
```json
{
  "input": {
    "input_type": "video",
    "person_count": "single",
    "prompt": "A person is talking in a natural way.",
    "video_path": "/my_volume/input_video.mp4",
    "wav_path": "/my_volume/audio.wav",
    "width": 512,
    "height": 512
  }
}
```

#### 7. Using Network Volume for Output (I2V Single Example)
```json
{
  "input": {
    "input_type": "image",
    "person_count": "single",
    "prompt": "A person talking in a natural way.",
    "image_url": "https://example.com/portrait.jpg",
    "wav_url": "https://example.com/audio.wav",
    "width": 512,
    "height": 512,
    "network_volume": true
  }
}
```

### Output

#### Success

If the job is successful, it returns a JSON object with the generated video. The response format depends on the `network_volume` parameter.

**When `network_volume` is `false` (default):**

| Parameter | Type | Description |
| --- | --- | --- |
| `video` | `string` | Base64 encoded video file data. |

**Success Response Example (Base64):**

```json
{
  "video": "data:video/mp4;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
}
```

**When `network_volume` is `true`:**

| Parameter | Type | Description |
| --- | --- | --- |
| `video_path` | `string` | File path to the generated video stored in the network volume. |

**Success Response Example (Network Volume):**

```json
{
  "video_path": "/runpod-volume/infinitetalk_task_12345.mp4"
}
```

#### Error

If the job fails, it returns a JSON object containing an error message.

| Parameter | Type | Description |
| --- | --- | --- |
| `error` | `string` | Description of the error that occurred. |

**Error Response Example:**

```json
{
  "error": "비디오를 찾을 수 없습니다."
}
```

## 🛠️ Usage and API Reference

1.  Create a Serverless Endpoint on RunPod based on this repository.
2.  Once the build is complete and the endpoint is active, submit jobs via HTTP POST requests according to the API Reference below.

### 📁 Using Network Volumes

You can use RunPod's Network Volumes for both input and output files. This is especially useful when dealing with large files.

#### For Input Files

Instead of directly transmitting Base64 encoded files, you can use Network Volumes to handle large input files:

1.  **Create and Connect Network Volume**: Create a Network Volume (e.g., S3-based volume) from the RunPod dashboard and connect it to your Serverless Endpoint settings.
2.  **Upload Files**: Upload the image, video, and audio files you want to use to the created Network Volume.
3.  **Specify Paths**: When making an API request, specify the file paths within the Network Volume for `image_path`, `video_path`, and `wav_path`. For example, if the volume is mounted at `/my_volume` and you use `portrait.jpg`, the path would be `"/my_volume/portrait.jpg"`.

#### For Output Files

You can also use Network Volumes to store the generated video files instead of returning Base64 data:

1.  **Set `network_volume` to `true`**: Add `"network_volume": true` to your request input.
2.  **Get File Path**: The response will contain a `video_path` field with the location of the generated video file in the network volume.
3.  **Access Files**: The generated video will be saved to `/runpod-volume/` directory with a unique filename.

**Benefits of using Network Volumes:**
- **Reduced Memory Usage**: No need to load large files into memory for Base64 encoding/decoding
- **Faster Processing**: Direct file access is more efficient than Base64 conversion
- **Persistent Storage**: Generated files remain accessible after the job completes
- **Large File Support**: Handle files larger than typical API payload limits

## 🔧 Workflow Configuration

This template includes four workflow configurations that are automatically selected based on your input parameters:

*   **I2V_single.json**: Image-to-Video single-person workflow
*   **I2V_multi.json**: Image-to-Video multi-person workflow
*   **V2V_single.json**: Video-to-Video single-person workflow
*   **V2V_multi.json**: Video-to-Video multi-person workflow

### Workflow Selection Logic

The handler automatically selects the appropriate workflow based on your input parameters:

| input_type | person_count | Selected Workflow |
|------------|--------------|-------------------|
| `"image"` | `"single"` | I2V_single.json |
| `"image"` | `"multi"` | I2V_multi.json |
| `"video"` | `"single"` | V2V_single.json |
| `"video"` | `"multi"` | V2V_multi.json |

The workflows are based on ComfyUI and include all necessary nodes for InfiniteTalk processing. Each workflow is optimized for its specific use case and includes the appropriate model configurations.

## ⚡ Cold Start Optimization (zero added cost)

A serverless worker has three cold-start phases: (1) container schedule/pull, (2) ComfyUI process boot, and (3) **loading ~26GB of model weights into VRAM**. Phase 3 is the slow one. The ~26GB of weights are already baked into the Docker image (loaded from local NVMe), which is RunPod's recommended approach — so moving models to a *network volume would not help and is generally slower*. The remaining cost is the VRAM load, which this template reduces using **only free levers** — no always-on workers, no raised idle timeouts, nothing that bills idle GPU time.

### 1. Startup warm-up (built in)

On boot, `entrypoint.sh` runs `warmup.py` — a single **minimal** I2V workflow using the bundled example assets — **before** the handler starts accepting jobs. This forces ComfyUI to load the diffusion / VAE / text-encoder / clip-vision / audio models into VRAM during boot, so the worker becomes warm as part of initialization.

To keep its own GPU time negligible, the warm-up runs at the cheapest settings that still load every weight: **256×256 resolution, one 81-frame chunk, and a single diffusion step**. It loads the same models a real job would, but skips almost all of the sampling compute.

*   Best-effort: any failure is logged and ignored so it can never block the endpoint.
*   Warms the most common path (I2V single). The `InfiniteTalk-Multi` model still loads on the first multi-person request.
*   Disable it by setting the endpoint environment variable `WARMUP_ENABLED=false`.

| Env Var | Default | Description |
| --- | --- | --- |
| `WARMUP_ENABLED` | `true` | Pre-load models into VRAM at startup. Set to `false` to skip warm-up. |

### 2. Keep FlashBoot enabled (free)

Leave **FlashBoot** on (the RunPod default). It snapshots a worker once it's warmed up, so when the endpoint scales up — or replaces a worker — the new worker **restores the warmed state instead of reloading ~26GB from scratch**. This is what makes the warm-up pay off across requests, and it costs nothing extra.

### Honest trade-off

These levers are free because they never keep an idle GPU billing. The cost is that a **scale-to-zero endpoint can still cold-start its first request** after a long idle period: that first worker loads the weights during boot (the warm-up), and the user who triggered it waits through that. FlashBoot then keeps subsequent scale-ups fast.

The only way to make even that first request instant is to run an **active (min) worker**, but that bills GPU time 24/7 whether or not anyone is using it — so it is intentionally **not** recommended here. If you later decide the always-on cost is worth it for your traffic, set min workers ≥ 1 on the endpoint; the built-in warm-up will keep that worker VRAM-warm.

## 🙏 Original Project

This project is based on the following original repository. All rights to the model and core logic belong to the original authors.

*   **InfiniteTalk:** [https://github.com/MeiGen-AI/InfiniteTalk](https://github.com/MeiGen-AI/InfiniteTalk)
*   **ComfyUI:** [https://github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
*   **WanVideoWrapper** [https://github.com/kijai/ComfyUI-WanVideoWrapper](https://github.com/kijai/ComfyUI-WanVideoWrapper)

## 📄 License

The original InfiniteTalk project follows the Apache 2.0 License. This template also adheres to that license.
