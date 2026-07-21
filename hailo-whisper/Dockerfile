FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 LC_ALL=C.UTF-8

# 基础系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    jq curl wget udev ffmpeg libsndfile1 ca-certificates \
    libusb-1.0-0 libstdc++6 pciutils \
    && rm -rf /var/lib/apt/lists/*

# 安装 HailoRT 驱动（需将对应架构的 deb 放入 packages/ 目录）
# 支持 arm64（树莓派 5 等）与 amd64（x86 小主机），按构建目标架构优先匹配
COPY packages/ /tmp/packages/
RUN dpkg -i /tmp/packages/hailort_5.2.0_arm64.deb || true \
 && dpkg -i /tmp/packages/hailo_gen_ai_model_zoo_5.2.0_arm64.deb || true \
 && apt-get update && apt-get install -f -y \
 && ldconfig;

WORKDIR /opt/hailo-whisper

# Python 依赖
COPY requirements.txt .
RUN pip3 install --break-system-packages -r requirements.txt
RUN pip3 install /tmp/packages/hailort-5.2.0-cp311-cp311-linux_aarch64.whl
RUN rm -rf /tmp/packages /var/lib/apt/lists/*

# 业务代码（app 与 common 为同级包，便于 `from common.xxx` / `from app.xxx` 导入）
COPY app ./app
COPY common ./common

# 启动脚本
COPY run.sh /run.sh
RUN chmod +x /run.sh

EXPOSE 10300
CMD ["/run.sh"]
