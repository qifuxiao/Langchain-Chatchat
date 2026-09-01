#!/usr/bin/env bash
# =============================================================================
# 容器启动入口：在容器内按【正确顺序】执行部署步骤。
#
# 等价于宿主机上的手工步骤（顺序已修正）：
#   (镜像已内置) CPU 版 torch + pip install -r requirements_openai.docker.txt
#   [1] python copy_config_example.py         # 仅当 configs 缺失时执行
#   [2] python init_database.py --recreate-vs # 由 RUN_INIT_DB 控制
#   [3] python startup.py -a                   # 前台运行，成为 PID 1
#
# 可调环境变量：
#   RUN_INIT_DB   是否执行 init_database.py --recreate-vs，默认 "1"。
#                 完全断网、且镜像内已内置知识库向量时，请设为 "0"
#                 （此时无需访问 Embedding API，直接复用既有向量）。
#   STARTUP_ARGS  传给 startup.py 的参数，默认 "-a"
#                 （-a = 启动 controller/openai_api/model_worker/api/webui 全部服务）。
#   MODEL_NAME    可选，追加给 startup.py 的模型名（-n）。
# =============================================================================
set -euo pipefail

APP_DIR="/app"
cd "$APP_DIR"

RUN_INIT_DB="${RUN_INIT_DB:-1}"
STARTUP_ARGS="${STARTUP_ARGS:--a}"
MODEL_NAME="${MODEL_NAME:-}"

echo "=========================================================="
echo "Langchain-Chatchat 容器启动"
echo "  RUN_INIT_DB  = ${RUN_INIT_DB}"
echo "  STARTUP_ARGS = ${STARTUP_ARGS}"
echo "  MODEL_NAME   = ${MODEL_NAME:-<default>}"
echo "=========================================================="

# [1/3] 确保配置文件存在：仅当缺失时才从 .example 生成，避免覆盖内置的测试配置
if [ ! -f "configs/model_config.py" ]; then
    echo "[1/3] 未检测到 configs/model_config.py，执行 copy_config_example.py 生成默认配置..."
    python copy_config_example.py
else
    echo "[1/3] 检测到已内置配置 configs/model_config.py，跳过 copy_config_example.py（保留现有配置）。"
fi

# [2/3] 初始化数据库 / 重建向量库（可选）
if [ "${RUN_INIT_DB}" != "0" ]; then
    echo "[2/3] 执行 init_database.py --recreate-vs ...（需要可访问 Embedding API）"
    python init_database.py --recreate-vs
else
    echo "[2/3] RUN_INIT_DB=0，跳过 init_database.py（复用镜像内/挂载的既有知识库数据）。"
fi

# [3/3] 启动服务（前台运行；exec 使其成为 PID 1 以正确接收 SIGTERM 等信号）
if [ -n "${MODEL_NAME}" ]; then
    echo "[3/3] 启动服务：python startup.py ${STARTUP_ARGS} -n ${MODEL_NAME}"
    exec python startup.py ${STARTUP_ARGS} -n "${MODEL_NAME}"
else
    echo "[3/3] 启动服务：python startup.py ${STARTUP_ARGS}"
    exec python startup.py ${STARTUP_ARGS}
fi
