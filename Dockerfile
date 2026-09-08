# syntax=docker/dockerfile:1
FROM python:3.11-slim-bookworm AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_TIMEOUT=120 PIP_RETRIES=5
ARG TORCH_CPU_INDEX=https://download.pytorch.org/whl/cpu
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH
COPY requirements.txt requirements_openai.docker.txt ./
# Pin the local version suffix so the resolver cannot replace CPU torch with CUDA.
RUN pip install torch==2.1.2+cpu --index-url "${TORCH_CPU_INDEX}" \
    && pip install -r requirements_openai.docker.txt \
    && pip check

FROM python:3.11-slim-bookworm
ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    NLTK_DATA=/app/nltk_data TIKTOKEN_CACHE_DIR=/opt/tiktoken-cache \
    HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
# OpenCV/FAISS/ONNX, document parsing and GitPython (Streamlit) runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libmagic1 libgl1 libglib2.0-0 libgomp1 pandoc git \
    && rm -rf /var/lib/apt/lists/*
COPY --from=builder /opt/venv /opt/venv
WORKDIR /app
COPY . .
RUN python docker/prepare_configs.py \
    && python -c "import tiktoken; [tiktoken.get_encoding(n) for n in ('cl100k_base', 'p50k_base', 'r50k_base')]" \
    && python docker/smoke_test.py
EXPOSE 8501 7861
HEALTHCHECK --interval=30s --timeout=10s --start-period=180s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7861/openapi.json', timeout=5).close()" || exit 1
ENTRYPOINT ["bash", "docker/entrypoint.sh"]
