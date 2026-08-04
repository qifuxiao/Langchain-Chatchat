# Gitee AI Docker 离线交付

本镜像仅将 Langchain-Chatchat 服务及其 Python 依赖打包；聊天和向量化请求仍会从离线服务器访问 `https://ai.gitee.com/v1`。因此“离线”指不需要在目标服务器下载镜像、Python 依赖或本地模型，不代表模型推理可在断网环境运行。

## 构建与导出

在可联网的构建机执行：

```bash
cp .env.gitee.example .env
# 编辑 .env，仅填写 GITEE_AI_API_KEY
docker compose build
bash scripts/export-offline-bundle.sh
```

Dockerfile 默认使用阿里云的 Debian 与 PyPI 镜像，可在 `.env` 通过
`APT_MIRROR_HOST`、`PIP_INDEX_URL`、`PIP_TRUSTED_HOST` 改为公司内部源。它们只影响构建期依赖下载。

构建成功后，Docker 会生成 `langchain-chatchat-gitee:0.2.9` 镜像。导出脚本会把它、无 `build` 段的 Compose 文件、示例环境变量和 SHA-256 校验和打成 `dist/langchain-chatchat-gitee-0.2.9.tar.gz`。

把该压缩包传到离线服务器。目标服务器执行：

```bash
bash import-offline-bundle.sh langchain-chatchat-gitee-0.2.9.tar.gz /opt/langchain-chatchat
cd /opt/langchain-chatchat
# 编辑 .env，仅填写 GITEE_AI_API_KEY
docker compose up -d
```

首次启动会从模板生成 `configs/*.py`，并读取 `GITEE_AI_*` 环境变量。知识库、FAISS 索引和 SQLite 元数据保存到 `./data/knowledge_base`，日志保存到 `./data/logs`；升级镜像不会覆盖这些数据。

访问地址：WebUI `http://SERVER:8501`，业务 API `http://SERVER:7861/docs`，兼容 OpenAI 的本地代理 `http://SERVER:20000/v1`。

如需完全断网运行，必须改用本地 LLM 与本地 Embedding 模型；Gitee API 无法在无外网连接的环境中完成推理。当前交付仅实现镜像和依赖的离线搬运，不能让 Gitee API 在隔绝外网环境中推理。
