# HailoRT 安装包放置说明

本加载项镜像需要在构建时安装 **HailoRT 运行时**（包含 `hailo_platform` Python 绑定与 PCIe 用户态驱动）。
由于 HailoRT 需要登录 Hailo Developer Zone 下载，无法直接 pip 安装，请按以下步骤准备：

## 1. 下载 HailoRT deb 安装包

前往 https://hailo.ai/developer-zone/ 下载与你硬件/系统匹配的版本（建议 5.2.0 及以上，需与模型/示例匹配）：

- 树莓派 5 / 其它 ARM64 主机（aarch64）：`hailort_<ver>_arm64.deb`
- x86_64 小主机（amd64）：`hailort_<ver>_amd64.deb`

> 同时建议下载 `hailo_gen_ai_model_zoo_<ver>_arm64.deb` / `_amd64.deb`（可选，部分示例依赖）。

## 2. 放入本目录

将下载好的 `.deb` 文件复制到本 `packages/` 目录，例如：

```
hailo-whisper/
└── packages/
    ├── hailort_5.2.0_arm64.deb
    └── hailo_gen_ai_model_zoo_5.2.0_arm64.deb
```

Dockerfile 在构建时会按目标架构（`TARGETARCH`）自动安装匹配的 deb；若只放了一种架构，则安装该架构的包。

## 3. 构建 / 安装加载项

在 Home Assistant → 加载项商店 → 上传仓库 / 本地构建时，会执行上述 Dockerfile。
若 `packages/` 为空，镜像仍可构建，但运行时加载模型会失败（缺少 `hailo_platform`）。

## 4. 宿主机内核驱动

容器内的用户态驱动依赖**宿主机已加载 Hailo PCIe 内核驱动**。Home Assistant OS 默认不包含该驱动，
需在宿主机侧安装（如社区维护的 Hailo 驱动加载项 / 内核模块），否则 `/dev/hailo0` 等设备节点不会出现。
