# syntax=docker/dockerfile:1
# =============================================================================
# Langchain-Chatchat (feature/aigitee) - 离线部署镜像
#
# 构建（在【可联网】的服务器上执行）：
#   docker build -t langchain-chatchat:offline .
#
# 该镜像已内置（构建期完成，运行期无需联网装依赖）：
#   - Python 3.11 运行时
#   - 精简依赖 requirements_openai.docker.txt（剔除 nvidia-*/vllm/xformers 等本地 GPU 组件）+ CPU 版 torch/torchvision
#   - 项目源码与测试通过的配置文件（configs/*.py，如 Gitee AI 在线模型配置）
#   - 知识库数据（knowledge_base/，含 info.db 与向量库）与 NLTK 数据（nltk_data/）
#
# 运行（在【完全断网】的服务器上执行）：
#   docker load -i langchain-chatchat-offline.tar
#   docker run -d --name chatchat \
#     -p 8501:8501 -p 7861:7861 -p 20000:20000 -p 20001:20001 -p 21010:21010 \
#     -e RUN_INIT_DB=0 --restart unless-stopped langchain-chatchat:offline
#
# 详细说明见 docs/DOCKER_OFFLINE_DEPLOY.md
# =============================================================================
FROM python:3.11-slim

# 运行时环境变量：
#   PYTHONUNBUFFERED/PYTHONDONTWRITEBYTECODE -> 日志实时输出、不写 .pyc
#   PIP_NO_CACHE_DIR                          -> 减小镜像体积
#   PIP_INDEX_URL/PIP_TRUSTED_HOST            -> 与测试环境一致的阿里云 PyPI 镜像源
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
    PIP_TRUSTED_HOST=mirrors.aliyun.com \
    # 大型 wheel（torch / nvidia-* 等数百 MB）下载易超时：加大读超时与重试次数
    PIP_TIMEOUT=120 \
    PIP_RETRIES=10

# 系统运行时库（长期保留；编译工具 build-essential 放到依赖层“随装随删”，以减小镜像体积）：
#   curl / git             -> 排障、拉取
#   libmagic1              -> python-magic（文件类型识别）
#   libgl1 / libglib2.0-0  -> opencv-python
#   poppler-utils          -> pdf2image（PDF 处理）
#   tesseract-ocr          -> pytesseract / unstructured OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        git \
        libmagic1 \
        libgl1 \
        libglib2.0-0 \
        poppler-utils \
        tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 依赖安装（单层：编译工具 build-essential 随装随删，避免其体积残留进镜像）：
#   1) CPU 版 torch/torchvision：本部署为纯在线 API（Gitee AI），无 GPU 本地推理；
#      但启动链 server.api -> knowledge_base_chat -> reranker -> sentence_transformers
#      会在 import 阶段 `import torch`，故必须装“可导入”的 torch。用 CPU 版即可满足 import，
#      同时彻底避开 nvidia-* CUDA 大包（约 5~8GB，正是之前构建下载超时的元凶）。
#   2) 精简依赖 requirements_openai.docker.txt（已剔除 nvidia-*/vllm/xformers/triton/torchaudio/ray）。
#   build-essential 仅用于编译个别无 wheel 的包，装完立即 --purge 移除。
#   国内若官方 torch 源慢/不可达：
#     TORCH_CPU_INDEX=https://mirrors.tuna.tsinghua.edu.cn/pytorch-wheels/cpu/ ./docker/build_online.sh
ARG TORCH_CPU_INDEX=https://download.pytorch.org/whl/cpu
COPY requirements_openai.docker.txt ./requirements_openai.docker.txt
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends build-essential; \
    attempt=0; \
    until pip install --no-cache-dir --timeout 120 --retries 10 \
            torch==2.1.2 torchvision==0.16.2 --index-url "${TORCH_CPU_INDEX}"; do \
        attempt=$((attempt + 1)); \
        if [ "$attempt" -ge 5 ]; then echo "==> CPU torch 安装连续 $attempt 次失败，请检查 TORCH_CPU_INDEX 是否可达。" >&2; exit 1; fi; \
        echo "==> CPU torch 安装失败，5 秒后进行第 $attempt 次重试..."; sleep 5; \
    done; \
    attempt=0; \
    until pip install --no-cache-dir --timeout 120 --retries 10 -r requirements_openai.docker.txt; do \
        attempt=$((attempt + 1)); \
        if [ "$attempt" -ge 5 ]; then echo "==> pip install 连续 $attempt 次失败，终止。请检查网络/镜像源。" >&2; exit 1; fi; \
        echo "==> pip install 失败，5 秒后进行第 $attempt 次重试..."; sleep 5; \
    done; \
    apt-get remove -y --purge build-essential; \
    apt-get autoremove -y --purge; \
    rm -rf /var/lib/apt/lists/*

# 复制项目源码与配置（.dockerignore 已排除 .venv / .git / logs 等大文件与运行时产物）
COPY . .

# 安全生成配置文件：仅当 configs/*.py 不存在时才从 .example 复制，
# 避免覆盖镜像中已内置的、测试通过的配置（如 Gitee AI 在线模型配置）。
RUN if [ ! -f configs/model_config.py ]; then \
        python copy_config_example.py; \
    fi

# 端口：webui(8501) api(7861) fschat-openai-api(20000) controller(20001) model-worker(21010/21009)
EXPOSE 8501 7861 20000 20001 21010 21009

# 健康检查：仅探测 API 端口是否可连接（本地 socket，离线可用，不依赖外网）
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
    CMD python -c "import socket; socket.create_connection(('127.0.0.1', 7861), 5).close()" || exit 1

ENTRYPOINT ["bash", "docker/entrypoint.sh"]
