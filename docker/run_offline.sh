#!/usr/bin/env bash
# =============================================================================
# 【在【完全断网】的服务器上执行】启动 Langchain-Chatchat 容器。
#
# 默认策略（保证完全断网即可运行）：
#   RUN_INIT_DB=0  —— 复用镜像内已内置的、测试通过的知识库（含向量库），
#                     启动时不再调用 Embedding API，因此无需外网。
#
# 常用可覆盖变量：
#   RUN_INIT_DB=1    启动时执行 init_database.py --recreate-vs
#                    （需该服务器能访问 Embedding API，即 Gitee AI 接口）
#   MOUNT_KB=1       额外挂载宿主机目录 $DATA_DIR/knowledge_base 作为知识库
#                    （请先自行准备好知识库数据）
#   STARTUP_ARGS     传给 startup.py 的参数（默认 -a）
#   CONTAINER_NAME   容器名（默认 chatchat）
#   WEBUI_PORT / API_PORT 等  宿主机端口映射
#
# 用法：
#   ./docker/run_offline.sh
#   RUN_INIT_DB=1 MOUNT_KB=1 ./docker/run_offline.sh
# =============================================================================
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

IMAGE="${IMAGE:-langchain-chatchat:offline}"
CONTAINER_NAME="${CONTAINER_NAME:-chatchat}"
DATA_DIR="${DATA_DIR:-$ROOT_DIR/dist/data}"

# 宿主机端口映射（左侧）: 容器端口（右侧，见 configs/server_config.py）
WEBUI_PORT="${WEBUI_PORT:-8501}"
API_PORT="${API_PORT:-7861}"
FSCHAT_OPENAI_API_PORT="${FSCHAT_OPENAI_API_PORT:-20000}"
CONTROLLER_PORT="${CONTROLLER_PORT:-20001}"
MODEL_WORKER_PORT="${MODEL_WORKER_PORT:-21010}"
MODEL_WORKER_API_PORT="${MODEL_WORKER_API_PORT:-21009}"

# 默认 RUN_INIT_DB=0：使用镜像内置知识库，完全断网可运行
RUN_INIT_DB="${RUN_INIT_DB:-0}"
STARTUP_ARGS="${STARTUP_ARGS:--a}"

# 前置检查：镜像是否已加载
if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
    echo "错误：未找到镜像 $IMAGE。请先执行 ./docker/import_image.sh 加载镜像。" >&2
    exit 1
fi

# 幂等：若同名容器已存在，先停止并删除
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "==> 检测到已存在容器 ${CONTAINER_NAME}，先停止并删除..."
    docker rm -f "${CONTAINER_NAME}" >/dev/null
fi

mkdir -p "$DATA_DIR/logs"
VOLUMES=(-v "${DATA_DIR}/logs:/app/logs")
if [ "${MOUNT_KB:-0}" = "1" ]; then
    mkdir -p "$DATA_DIR/knowledge_base"
    VOLUMES+=(-v "${DATA_DIR}/knowledge_base:/app/knowledge_base")
fi

echo "==> 启动容器: ${CONTAINER_NAME} (镜像: ${IMAGE})"
echo "    RUN_INIT_DB=${RUN_INIT_DB}  STARTUP_ARGS=${STARTUP_ARGS}"
docker run -d \
    --name "${CONTAINER_NAME}" \
    --restart unless-stopped \
    -p "${WEBUI_PORT}:8501" \
    -p "${API_PORT}:7861" \
    -p "${FSCHAT_OPENAI_API_PORT}:20000" \
    -p "${CONTROLLER_PORT}:20001" \
    -p "${MODEL_WORKER_PORT}:21010" \
    -p "${MODEL_WORKER_API_PORT}:21009" \
    "${VOLUMES[@]}" \
    -e RUN_INIT_DB="${RUN_INIT_DB}" \
    -e STARTUP_ARGS="${STARTUP_ARGS}" \
    "${IMAGE}"

echo ""
echo "==> 容器已启动。查看实时日志："
echo "    docker logs -f ${CONTAINER_NAME}"
echo ""
echo "服务地址（浏览器/客户端访问宿主机对应端口）："
echo "    WebUI : http://<服务器IP>:${WEBUI_PORT}"
echo "    API   : http://<服务器IP>:${API_PORT}"
echo "    内部端口（一般无需从外部访问）: controller=${CONTROLLER_PORT} openai_api=${FSCHAT_OPENAI_API_PORT} model_worker=${MODEL_WORKER_PORT}"
