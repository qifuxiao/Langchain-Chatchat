#!/usr/bin/env bash
# =============================================================================
# 【在【可联网】的服务器上执行】构建 Langchain-Chatchat 离线部署镜像。
#
# 用法：
#   ./docker/build_online.sh                    # 默认镜像名 langchain-chatchat:offline
#   IMAGE=myname:v1 ./docker/build_online.sh    # 自定义镜像名
#
# 说明：
#   - 请在“测试通过的工程目录”下执行，这样 configs/*.py（Gitee AI 在线模型配置）
#     与 knowledge_base/（含向量库）会被一并打入镜像。
#   - 构建依赖联网（pip 走阿里云镜像源、拉取基础镜像）。
# =============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

IMAGE="${IMAGE:-langchain-chatchat:offline}"
# CPU 版 torch 的下载索引（纯在线 API 部署无需 CUDA，故用 CPU 版 torch 以大幅缩小镜像）。
# 国内若官方源慢/不可达，可用清华镜像覆盖：
#   TORCH_CPU_INDEX=https://mirrors.tuna.tsinghua.edu.cn/pytorch-wheels/cpu/ ./docker/build_online.sh
TORCH_CPU_INDEX="${TORCH_CPU_INDEX:-https://download.pytorch.org/whl/cpu}"

echo "==> 项目根目录:   $ROOT_DIR"
echo "==> 构建镜像:     $IMAGE"
echo "==> torch CPU 源: $TORCH_CPU_INDEX"
docker build \
    --build-arg TORCH_CPU_INDEX="$TORCH_CPU_INDEX" \
    -t "$IMAGE" .

echo ""
echo "==> 校验镜像是否构建成功："
if docker image inspect "$IMAGE" >/dev/null 2>&1; then
    docker images "$IMAGE"
    echo "==> 构建成功，镜像已就绪。"
else
    echo "错误：构建后未找到镜像 $IMAGE。请检查上方 docker build 的报错日志。" >&2
    exit 1
fi
echo ""
echo "下一步：执行 ./docker/export_image.sh 导出离线镜像包。"
