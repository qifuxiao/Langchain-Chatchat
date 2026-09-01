#!/usr/bin/env bash
# =============================================================================
# 【在【完全断网】的服务器上执行】从离线 tar 包加载镜像。
#
# 用法：
#   ./docker/import_image.sh                       # 默认加载 dist/langchain-chatchat-offline.tar
#   ./docker/import_image.sh /path/to/xxx.tar      # 指定 tar 包路径
#   ./docker/import_image.sh /path/to/xxx.tar.gz   # 亦支持 gzip 包
#
# 加载完成后执行 ./docker/run_offline.sh 启动服务。
# =============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

IMAGE="${IMAGE:-langchain-chatchat:offline}"
TAR_FILE="${1:-$ROOT_DIR/dist/${IMAGE//:/-}.tar}"

# 若未显式指定且默认 .tar 不存在，尝试 .tar.gz
if [ ! -f "$TAR_FILE" ]; then
    if [ -f "$TAR_FILE.gz" ]; then
        TAR_FILE="$TAR_FILE.gz"
    else
        echo "错误：找不到镜像包 $TAR_FILE（也未找到 $TAR_FILE.gz）" >&2
        echo "提示：可用 './docker/import_image.sh /path/to/xxx.tar' 指定镜像包路径。" >&2
        exit 1
    fi
fi

# 前置检查：镜像包必须非空
if [ ! -s "$TAR_FILE" ]; then
    echo "错误：镜像包 $TAR_FILE 为空（0 字节）。" >&2
    echo "      请先在联网服务器确认 export 成功（正常应为数 GB）。" >&2
    exit 1
fi

echo "==> 加载镜像包: $TAR_FILE"
docker load -i "$TAR_FILE"

echo ""
echo "==> 加载完成。当前相关镜像："
docker images
echo ""
echo "下一步：执行 ./docker/run_offline.sh 启动服务。"
