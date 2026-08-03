# Gitee AI Docker 离线交付

本镜像仅将 Langchain-Chatchat 服务及其 Python 依赖打包；聊天和向量化请求仍会从离线服务器访问 `https://ai.gitee.com/v1`。因此“离线”指不需要在目标服务器下载镜像、Python 依赖或本地模型，不代表模型推理可在断网环境运行。

## 构建与导出

在可联网的构建机执行：

```bash
cp .env.gitee.example .env
# 编辑 .env，仅填写 GITEE_AI_API_KEY
docker compose build
docker save -o langchain-chatchat-gitee-0.2.9.tar langchain-chatchat-gitee:0.2.9
```

把 `langchain-chatchat-gitee-0.2.9.tar`、`docker-compose.yml` 与目标服务器的 `.env` 传到离线服务器。目标服务器执行：

```bash
docker load -i langchain-chatchat-gitee-0.2.9.tar
docker compose up -d
```

首次启动会从模板生成 `configs/*.py`，并读取 `GITEE_AI_*` 环境变量。知识库、FAISS 索引和 SQLite 元数据保存到 `./data/knowledge_base`，日志保存到 `./data/logs`；升级镜像不会覆盖这些数据。

访问地址：WebUI `http://SERVER:8501`，业务 API `http://SERVER:7861/docs`，兼容 OpenAI 的本地代理 `http://SERVER:20000/v1`。

如需完全断网运行，必须改用本地 LLM 与本地 Embedding 模型；Gitee API 无法在无外网连接的环境中完成推理。
