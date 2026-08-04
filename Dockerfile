FROM python:3.10-slim

ARG APT_MIRROR_HOST=mirrors.aliyun.com
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
ARG PIP_TRUSTED_HOST=mirrors.aliyun.com

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Use Aliyun's mirrors by default. Override the build arguments when building
# outside China or when an internal artifact mirror is available.
# Runtime libraries are used by document parsing, PDF rendering and RapidOCR.
RUN find /etc/apt -type f \( -name '*.list' -o -name '*.sources' \) -exec \
        sed -i \
            -e "s|deb.debian.org/debian-security|${APT_MIRROR_HOST}/debian-security|g" \
            -e "s|deb.debian.org/debian|${APT_MIRROR_HOST}/debian|g" {} \; \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        libgomp1 libgl1 libglib2.0-0 libmagic1 poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.gitee.txt ./
RUN pip install --upgrade pip \
        --index-url "${PIP_INDEX_URL}" \
        --trusted-host "${PIP_TRUSTED_HOST}" \
    && pip install -r requirements.gitee.txt \
        --index-url "${PIP_INDEX_URL}" \
        --trusted-host "${PIP_TRUSTED_HOST}"

# Keep this in a separate layer so an application-code update can reuse the
# expensive Python dependency layer. These resources are therefore present in
# every offline image and Word document parsing never downloads at runtime.
ENV NLTK_DATA=/app/nltk_data
RUN python -m nltk.downloader -d /app/nltk_data punkt punkt_tab \
    && test -d /app/nltk_data/tokenizers/punkt \
    && test -d /app/nltk_data/tokenizers/punkt_tab

COPY . ./
RUN chmod +x /app/docker-entrypoint.sh \
    && mkdir -p /app/knowledge_base /app/logs

EXPOSE 8501 7861 20000
VOLUME ["/app/knowledge_base", "/app/logs"]

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["python", "startup.py", "--all-webui"]
