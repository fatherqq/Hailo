FROM debian:bookworm-slim

# 基础系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    jq curl udev ffmpeg libsndfile1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 安装 HailoRT 驱动
COPY packages/ /tmp/packages/

RUN dpkg -i /tmp/packages/hailort_5.2.0_arm64.deb || true \
 && dpkg -i /tmp/packages/hailo_gen_ai_model_zoo_5.2.0_arm64.deb || true \
 && apt-get update && apt-get install -f -y \
 && ldconfig \
 && rm -rf /tmp/packages /var/lib/apt/lists/*

# 工作目录
WORKDIR /opt/hailo-whisper

# Python 依赖
COPY requirements.txt .
RUN pip3 install --break-system-packages -r requirements.txt

# 复制业务代码
COPY app/ ./app/

# 复制启动脚本
COPY run.sh /run.sh
RUN chmod +x /run.sh

# 启动入口
CMD [ "/run.sh" ]
