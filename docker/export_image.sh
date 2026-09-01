#!/usr/bin/env bash
# =============================================================================
# 【在【可联网】的服务器上执行】将镜像导出为离线 tar 包，便于拷贝到断网服务器。
#
# 用法：
#   ./docker/export_image.sh                 # 导出为 dist/langchain-chatchat-offline.tar
#   GZIP=1 ./docker/export_image.sh          # 导出为 gzip 压缩的 .tar.gz（体积更小，推荐）
#   IMAGE=myname:v1 ./docker/export_image.sh # 指定要导出的镜像
#
# 产物位于 dist/ 目录（根 .gitignore 已忽略 dist/，不会误提交）。
# 请将产物拷贝到完全断网的服务器，再执行 ./docker/import_image.sh 加载。
# =============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

IMAGE="${IMAGE:-langchain-chatchat:offline}"
OUT_DIR="${OUT_DIR:-$ROOT_DIR/dist}"
mkdir -p "$OUT_DIR"

# 前置检查：镜像必须已构建
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    echo "错误：镜像 $IMAGE 不存在。请先执行 ./docker/build_online.sh 并确保构建成功。" >&2
    exit 1
fi

# 镜像名中的冒号不适合做文件名，替换为短横线
SAFE_NAME="${IMAGE//:/-}"

if [ "${GZIP:-0}" = "1" ]; then
    OUT_FILE="$OUT_DIR/${SAFE_NAME}.tar.gz"
    echo "==> 导出并压缩镜像 $IMAGE -> $OUT_FILE"
    # 关键：gzip 程序会读取名为 GZIP 的环境变量当作默认选项；
    # 而本脚本用 GZIP 作为开关变量，两者会冲突，导致
    #   "gzip: 1: non-option in GZIP environment variable" 并产出 0 字节文件。
    # 故调用 gzip 时用 `env -u GZIP` 清除该环境变量。
    docker save "$IMAGE" | env -u GZIP gzip -c > "$OUT_FILE"
else
    OUT_FILE="$OUT_DIR/${SAFE_NAME}.tar"
    echo "==> 导出镜像 $IMAGE -> $OUT_FILE"
    docker save "$IMAGE" -o "$OUT_FILE"
fi

# 后置检查：产物必须非空，避免把 0 字节文件当成果物
if [ ! -s "$OUT_FILE" ]; then
    echo "错误：导出产物 $OUT_FILE 为空（0 字节），docker save 未输出内容。" >&2
    echo "      请确认镜像存在且导出未被中断；删除空文件后重试。" >&2
    rm -f "$OUT_FILE"
    exit 1
fi

echo ""
echo "==> 导出完成。"
ls -lh "$OUT_FILE"
echo ""
echo "将 '$OUT_FILE' 拷贝到完全断网的服务器后，执行 ./docker/import_image.sh 加载。"
