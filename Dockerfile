FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Runtime libraries used by document parsing, PDF rendering and RapidOCR.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        libgomp1 libgl1 libglib2.0-0 libmagic1 poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.gitee.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.gitee.txt

COPY . ./
RUN chmod +x /app/docker-entrypoint.sh \
    && mkdir -p /app/knowledge_base /app/logs

EXPOSE 8501 7861 20000
VOLUME ["/app/knowledge_base", "/app/logs"]

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python", "startup.py", "--all-webui"]
