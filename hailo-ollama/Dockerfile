ARG BUILD_FROM=ghcr.io/home-assistant/aarch64-base-debian:bookworm
FROM ${BUILD_FROM}

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        libusb-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY packages/ /tmp/packages/

RUN dpkg -i /tmp/packages/hailort_5.2.0_arm64.deb || true \
 && dpkg -i /tmp/packages/hailo_gen_ai_model_zoo_5.2.0_arm64.deb || true \
 && apt-get update && apt-get install -f -y \
 && ldconfig \
 && rm -rf /tmp/packages /var/lib/apt/lists/*

EXPOSE 8000

COPY run.sh /run.sh
RUN chmod +x /run.sh

ENTRYPOINT ["/init"]
CMD ["/run.sh"]