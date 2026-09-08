# OpenAI 接口模式：Docker 离线部署

适用基线：16089572；本文替代 e33fe7d3 / 7f85de50 中的部署步骤。
这里“离线”指运行机不访问 Docker Hub、PyPI、Hugging Face。运行机仍须能访问
配置的 LLM 和 Embedding API；可以是内网服务，不要求访问 Gitee 公网。
已有向量库也必须调用 Embedding API 将查询文本向量化。

## 1. 构建机（联网、Linux amd64 Docker）

构建机和运行机的 CPU 架构必须一致。当前 CPU torch 2.1.2+cpu 方案面向 amd64。

```bash
git clone -b feature/aigitee https://github.com/qifuxiao/Langchain-Chatchat.git
cd Langchain-Chatchat
bash docker/build_online.sh
```

源码必须包含本次修复。Docker 自动使用 `configs/*.py.example` 生成配置，
不复制本机 `configs/*.py` 或 `.env`，无需在宿主机安装 Python / CUDA。
若有自定义 KB / 端口配置，运行时挂载对应 `.py` 文件；配置目录整体挂载时需保留
`__init__.py` 并包含全部配置。不要把真实密钥写进模板。

依赖使用 `requirements.txt`；`requirements_openai.docker.txt` 仅引用它。
移除 CUDA、vLLM、xformers、torchvision、sentence-transformers、llama-index、
unstructured-inference、spacy 等。为保留 FastChat 默认模型适配器的兼容性，本次保守保留
CPU torch、transformers 和 accelerate；不启用本地模型。PDF/图片使用原有 CPU RapidOCR / ONNX，
不安装本地 LLM / Embedding / rerank 权重。

构建使用独立编译阶段，只把 Python 环境复制到运行镜像；构建时执行 `pip check`、
API 导入、分词与 OCR 初始化检查，预缓存 tiktoken，并使用仓库内 NLTK 3.8.1 对应数据。
成品大小须以构建结果为准，不再承诺固定 3 GB / 935 MB。

本机 Python 3.11 安装相同依赖时先安装 CPU torch：

```bash
python -m pip install torch==2.1.2+cpu --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
```

不要追加安装旧 `requirements_api.txt` / `requirements_openai.txt`，它们仍含本地 GPU 依赖。
精简镜像不支持本地模型和 Spacy 分词；传统 `.doc` / `.ppt` 转换需另装 LibreOffice。
远程 rerank 尚无适配器，模板保持 `USE_RERANKER=False`，不能仅设为 True。

## 2. 准备运行配置及知识库

```bash
cp docker/api.env.example .env
# 编辑 .env：设置模型地址、密钥、实际模型名。
```

默认模型名沿用提供的配置：`glm-4-9b-chat` / `Qwen3-Embedding-8B`。
对话别名为 `openai`，Embedding 别名必须为 `openai-api`。
分别部署时设置 `OPENAI_EMBEDDING_API_BASE_URL` 和 `OPENAI_EMBEDDING_API_KEY`；
未设置时复用对话服务地址和密钥。不要把占位地址 `localhost` 用于宿主机服务，
容器里的 localhost 指容器自身。

知识库有两种准备方式：

- 新建知识库：首次运行默认只创建缺失的数据库表，再通过 WebUI 上传文档并向量化。
- 迁移已有知识库：完整复制 `knowledge_base/`，包括文档、`info.db`、`vector_store`，
  并保持 Embedding 模型及其版本、向量维度一致。目录中的本地配置与 API 模型名必须匹配。

如需在构建机预生成向量，先准备 `knowledge_base/<KB>/content/`，使用刚构建的镜像：

```bash
docker run --rm --env-file .env --entrypoint python \
  -v "$PWD/knowledge_base:/app/knowledge_base" \
  langchain-chatchat:offline init_database.py --recreate-vs
# 重建镜像，把生成的 info.db 和 vector_store 一并带过去。
bash docker/build_online.sh
```

检查初始化日志确认各文件成功；批量导入可能记录单文件失败后继续，不能仅凭退出码判断成功。
也可以直接单独传输知识库目录到运行机，不将其放入镜像。

## 3. 导出和传输

```bash
GZIP=1 bash docker/export_image.sh
# dist/langchain-chatchat-offline.tar.gz
```

不设 `GZIP=1` 时输出 `.tar`。将镜像包和运行配置传到运行机，密钥配置单独保管。
如另行传输知识库，需复制完整目录。运行机不需要 Git 或项目源码。

## 4. 运行机（无需公网包管理服务）

```bash
docker load -i langchain-chatchat-offline.tar.gz
docker run -d --name chatchat --restart unless-stopped \
  -p 8501:8501 -p 7861:7861 \
  --env-file .env \
  -v chatchat-knowledge-base:/app/knowledge_base \
  -v "$PWD/logs:/app/logs" \
  -e RUN_INIT_DB=0 \
  langchain-chatchat:offline
```

新的命名卷首次从镜像复制知识库，后续复用卷；替换镜像不会自动更新已有卷中的数据。
如迁移了独立知识库目录，将知识库挂载改为 `-v "$PWD/knowledge_base:/app/knowledge_base"`。
空的宿主目录会遮蔽镜像中的知识库，务必检查挂载内容。

有项目脚本时可用 `ENV_FILE=/path/to/.env bash docker/run_offline.sh`。
脚本默认使用持久化命名卷，遇到已有容器会退出，不会自动删除它。
`RUN_INIT_DB` 默认 0，不重建向量；需要重建时在维护窗口运行一次上面的
`--entrypoint python ... init_database.py --recreate-vs` 命令。
`RUN_INIT_DB=1` 会在每次启动时重建，因此不推荐用于长期运行的容器。

浏览器访问 `http://<服务器IP>:8501`；API 地址为 `http://<服务器IP>:7861`。
仅暴露这两个端口即可，FastChat 内部服务不需要映射到宿主机。

```bash
docker logs --tail 100 chatchat
curl --fail http://localhost:7861/openapi.json
# 再通过 WebUI 实测对话、上传文档、知识库检索。
docker image inspect --format '{{.Size}} bytes' langchain-chatchat:offline
docker exec chatchat python -m pip check
```

HTTP 健康检查仅验证 API 服务；不代表模型接口、认证和知识库检索均正常。

## 5. 停止与恢复

```bash
docker stop chatchat
docker start chatchat
```

更新前备份知识库卷。只有确认知识库已持久化，才删除旧容器后用新镜像创建容器。
不要删除知识库卷来处理一般启动故障。
