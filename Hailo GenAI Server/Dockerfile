ARG BUILD_FROM
FROM $BUILD_FROM

# 安装基础工具和依赖（如果需要）
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    jq \
    bash \
    && rm -rf /var/lib/apt/lists/*

# 下载并安装 Hailo-Ollama 预编译 deb 包
# 请根据实际发布的版本和架构修改 URL
# 架构可通过 uname -m 或构建参数传入，这里以 amd64 和 arm64 为例
ARG TARGETARCH
RUN case "${TARGETARCH}" in \
        amd64)  ARCH="amd64" ;; \
        arm64)  ARCH="arm64" ;; \
        *)      echo "Unsupported architecture: ${TARGETARCH}"; exit 1 ;; \
    esac && \
    DEB_URL="https://github.com/hailo-ai/hailo_model_zoo_genai/releases/download/v1.0.0/hailo-ollama_1.0.0_${ARCH}.deb" && \
    wget -O /tmp/hailo-ollama.deb "${DEB_URL}" && \
    dpkg -i /tmp/hailo-ollama.deb || apt-get install -f -y && \
    rm /tmp/hailo-ollama.deb

# 复制启动脚本
COPY run.sh /run.sh
RUN chmod a+x /run.sh

EXPOSE 8000
CMD [ "/run.sh" ]
