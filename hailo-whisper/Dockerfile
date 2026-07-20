FROM debian:bookworm-slim

# 基础系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-pip python3-venv \
    jq curl udev ffmpeg libsndfile1 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 安装 HailoRT 驱动（将对应版本 deb 包放在项目根目录）
# 示例文件名：hailort_5.3.0_amd64.deb，请替换为实际文件名
COPY hailort_*.deb /tmp/
RUN dpkg -i /tmp/hailort_*.deb && rm /tmp/hailort_*.deb

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
