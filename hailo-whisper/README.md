# Hailo Whisper — Home Assistant 加载项

基于 **Hailo NPU（Hailo-8 / 8L / 10H）** 硬件加速的离线语音转写加载项。
底层推理复用 Hailo 官方 Whisper 示例，对外以 **REST API** 形式提供 Whisper 服务，并针对 Home Assistant 做了如下改造：

- ✅ **硬件自动识别**：自动检测 `hailo8` / `hailo8l` / `hailo10h`（优先用 HailoRT 读取器件型号，回退到设备节点）。
- ✅ **可选模型**：`base` / `tiny` / `tiny.en`（tiny.en 仅 10H 支持，会自动回退到可用变体）。
- ✅ **模型自动下载 + 持久化**：首次启动按 `(硬件, 模型)` 组合从 Hailo 资源库下载 HEF 权重与 Token 嵌入文件，保存到 `/data/hailo-whisper/models`，**重启不丢失**，仅首次需要联网。
- ✅ **REST + OpenAI 兼容接口**：`/transcribe` 与 `/v1/audio/transcriptions`，便于对接 Home Assistant 语音助手 / 自动化。

---

## 目录结构

```
hailo-whisper/
├── config.yaml            # HA 加载项清单（端口 / 设备 / 可配置项）
├── Dockerfile             # Debian 基础镜像，安装 HailoRT 与 Python 依赖
├── requirements.txt
├── run.sh                 # 入口脚本：建持久化目录、修设备权限、启动服务
├── packages/
│   └── README.md          # 放置 HailoRT deb 安装包（需自行从 Developer Zone 下载）
├── app/                   # 服务代码（与 common 同级，便于 from common / from app 导入）
│   ├── api_server.py      # FastAPI 服务（REST + OpenAI 兼容）
│   ├── whisper_service.py # 推理编排（加锁串行，复用单条 pipeline）
│   ├── model_manager.py   # 模型自动下载 + 持久化
│   ├── hw_detect.py       # 硬件架构自动识别
│   ├── whisper_hef_registry.py  # HEF 路径注册表（指向持久化目录）
│   ├── hailo_whisper_pipeline.py# Hailo 推理 pipeline（读取持久化 decoder 资源）
│   ├── download_resources.py    # CLI 预下载模型
│   └── app_hailo_whisper.py     # 麦克风命令行演示（本地调试用）
└── common/                # 推理工具（Hailo 官方示例，原样保留）
    ├── audio_utils.py / preprocessing.py / postprocessing.py / record_utils.py
    └── assets/mel_filters.npz
```

> 相比原 `fatherqq/Hailo` 仓库：根目录的 `speech_recognition/` 被重构成同级的 `app/` + `common/`（满足 `from common.xxx` 绝对导入）；新增 `api_server` / `whisper_service` / `model_manager` / `hw_detect`；修正了原 `whisper_hef_registry` 中 **hailo10h base 解码器文件名错误** 以及 decoder 资源未持久化的问题。

---

## 1. 前置条件

1. **Hailo 加速卡**：Hailo-8 / 8L（PCIe，设备节点 `/dev/hailo0`）或 Hailo-10H（`/dev/h1x-0` / `/dev/hailo10`）。
2. **宿主机内核驱动**：Home Assistant OS 默认不含 Hailo PCIe 驱动，需在宿主机侧安装（社区 Hailo 驱动加载项 / 内核模块），否则不会出现设备节点。
3. **HailoRT 安装包**：因需登录 Hailo Developer Zone 下载，无法 pip 安装。请把对应架构的 `hailort_<ver>_arm64.deb`（或 `_amd64.deb`）放入 `packages/`，详见 `packages/README.md`。

---

## 2. 安装与配置

- 将本目录作为加载项仓库加入 Home Assistant（或本地构建）。
- 在加载项配置中按需设置：
  - `hw_arch`：`auto`（默认，自动识别）/ `hailo8` / `hailo8l` / `hailo10h`
  - `model_variant`：`base`（默认）/ `tiny` / `tiny.en`
  - `language`：`auto` / `zh` / `en`（提示用，pipeline 实际自动检测语种）
  - `model_auto_download`：首次是否自动下载模型（默认开）
  - `multi_process_service`：是否启用多进程共享（与其它 Hailo 模型共用同一芯片）
  - `vdevice_group_id`：共享组名（默认 `HAILO_SHARED`）
- 启动加载项。首次启动会下载模型（日志可见进度），请耐心等待 `/health` 返回 `ready: true`。

---

## 3. API 用法

服务监听 `10300/tcp`。

### 健康检查
```bash
curl http://<ha-ip>:10300/health
# {"status":"ok","ready":true,"hw_arch":"hailo10h","variant":"base",...}
```

### 转写音频文件
```bash
curl -F "file=@/path/to/audio.wav" http://<ha-ip>:10300/transcribe
# {"text":"今天天气真好","variant":"base","language":"auto"}
```

### OpenAI 兼容（可对接 HA Whisper 集成）
```bash
curl -F "file=@/path/to/audio.wav" -F "model=whisper-1" \
     http://<ha-ip>:10300/v1/audio/transcriptions
# {"text":"今天天气真好"}
```

### 查看 / 重新加载
```bash
curl http://<ha-ip>:10300/models          # 各模型下载状态
curl -X POST http://<ha-ip>:10300/admin/reload   # 热重载（如后插设备/换模型）
```

---

## 4. 接入 Home Assistant 语音助手（示例）

最简方式：用 `rest_command` 或在自动化里调用 `/transcribe`。例如 `configuration.yaml`：

```yaml
rest_command:
  hailo_transcribe:
    url: "http://127.0.0.1:10300/transcribe"
    method: POST
    files:
      file: "{{ audio_file }}"
    content_type: multipart/form-data
```

也可把 `/v1/audio/transcriptions` 作为 OpenAI 兼容端点接到 HA 的 Whisper/STT 集成（需 HA 版本支持自定义 Whisper API 地址）。

---

## 5. 持久化说明

所有模型与 tokenizer 缓存均位于加载项持久存储：

```
/data/hailo-whisper/models/
├── hefs/            # HEF 权重（按硬件/变体分目录）
│   ├── h8/  h8l/  h10h/
├── decoder_assets/ # Token 嵌入 .npy（按变体）
└── hf/             # HuggingFace tokenizer 缓存
```

重启加载项不会重新下载；如需清理空间，直接删除 `/data/hailo-whisper/models` 下对应目录，下次启动会自动重新下载。

---

## 6. 本地调试（非 HA 环境）

```bash
# 准备 HailoRT + 依赖后，从仓库根（含 app/ 与 common/ 的目录）运行：
export MODELS_DIR=/tmp/hailo_models
python3 -m app.download_resources --hw-arch hailo8 --variant base   # 预下载
python3 -m app.api_server                                            # 启动 REST 服务
# 或麦克风演示：
python3 -m app.app_hailo_whisper --hw-arch hailo8 --variant base
```

---

## 7. 已知限制 / 排错

- **语种**：当前 Hailo decoder HEF 采用自动语种检测，配置中的 `language` 仅作 API 元信息提示，不强制指定输出语种。
- **长音频**：默认单次处理上限 60s（`common/preprocessing.py` 的 `max_duration`），更长会被截断。
- **设备未就绪**：`/health` 显示 `ready:false` 时，多为宿主机未加载 Hailo 驱动或 `packages/` 未放 HailoRT deb。查看加载项日志确认具体原因，必要时 `POST /admin/reload`。
- **10H 仅支持 base/tiny/tiny.en**，8/8L 支持 base/tiny；若选了不支持的组合，服务会自动回退到该硬件上可用的变体。
