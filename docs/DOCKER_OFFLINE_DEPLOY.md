# Langchain-Chatchat Docker 离线部署（从 GitHub 拉取代码开始）

本文覆盖**两台机器初始都没有代码**的完整流程：
- **联网构建机**：能访问 GitHub / PyPI / DockerHub / Gitee AI 在线 API。
- **离线运行机**：不能访问 PyPI / DockerHub / GitHub，但**必须能访问 Gitee AI 在线 API**（`https://ai.gitee.com/v1`）。

## 0. 先搞清楚“离线”的含义（重要）
本部署是“**软件包离线**”，不是“**业务断网**”：
- 依赖（pip）与镜像（docker）在联网机构建/导出，离线机不在线安装 —— 这是“离线”指的部分。
- 但对话（LLM）与向量化（Embedding）**运行时仍调用 Gitee AI 在线 API**。因此离线运行机必须能访问 `https://ai.gitee.com/v1`，否则无法回答、无法检索。
- 若离线机连 Gitee AI 都不通，则本“纯在线 Gitee AI”方案不适用（需改为本地模型方案）。

## 1. 哪些东西“不在仓库里”（clone 后需要手工准备）
`git clone` 下来是干净代码。以下两类被 `.gitignore` 忽略，**不随仓库分发**，需自行准备：
1. `configs/*.py`：Gitee AI 在线模型配置（含 **api_key**）。仓库只有 `configs/*.py.example`（其 `api_key` 为空）。
2. 知识库向量库 `knowledge_base/*/vector_store/`：由文档 + Gitee AI Embedding 生成。仓库只有原始文档（如 `knowledge_base/samples/content/`），**没有** `vector_store`。

> 好消息：本仓库的 `configs/*.py.example` 默认就是 Gitee AI 在线模式（`LLM_MODELS=["openai"]`、`api_base_url=https://ai.gitee.com/v1`），你只需填 `api_key`。

## 2. 联网构建机（从 clone 到导出）
### 2.1 拉取代码
```bash
git clone -b feature/aigitee https://github.com/qifuxiao/Langchain-Chatchat.git
cd Langchain-Chatchat
```

### 2.2 生成并配置 Gitee AI（填 api_key）
```bash
python copy_config_example.py        # 由 configs/*.py.example 生成 configs/*.py
```
编辑 `configs/model_config.py`，在 `ONLINE_LLM_MODEL["openai"]` 填入你的 Gitee AI 密钥与模型名：
```python
LLM_MODELS = ["openai"]               # 默认在线对话模型
ONLINE_LLM_MODEL = {
    "openai": {
        "model_name":   "glm-4-9b-chat",           # 你的 Gitee AI 对话模型名
        "api_base_url": "https://ai.gitee.com/v1",
        "api_key":      "填你的_Gitee_AI_api_key",  # ← 必填
        "embed_model":  "Qwen3-Embedding-8B",      # 你的 Embedding 模型名
        "provider":     "OpenAIWorker",
    },
}
```
- 模型名 / Embedding 名以你在 Gitee AI 控制台实际可用为准。
- `api_key` 只填在 `.py`（被 `.gitignore` 忽略，不会提交）；`.example` 保持空。

### 2.3 准备知识库
- 开箱演示：`knowledge_base/samples/content/` 已有样例文档（`用户使用协议.docx`、`llm/*.md`、`test_files/*`），直接用。
- 自有知识库：把文档放进 `knowledge_base/<你的KB名>/content/`。

### 2.4（推荐）联网预生成向量库
让离线机首次即用 `RUN_INIT_DB=0`，在联网机先本地生成 `vector_store`（`docker build` 用 `COPY . .` 会把它打进镜像）：
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt        # 或按需安装；需能访问 Gitee AI Embedding
python init_database.py --recreate-vs  # 处理 knowledge_base 下所有 KB（含 samples）
```
生成后 `knowledge_base/<KB>/vector_store/openai-api/` 出现 `index.faiss` / `index.pkl`。
> 不想预生成？可跳过本步，让离线机首次用 `RUN_INIT_DB=1` 现场生成（需离线机可访问 Gitee AI Embedding）。
### 2.5 构建镜像
```bash
docker build -t langchain-chatchat:offline .
```
CPU-only torch + 精简依赖，成品约 3 GB。

### 2.6 导出镜像
```bash
./docker/export_image.sh
# → dist/langchain-chatchat-offline.tar.gz（gzip，约 935 MB）
```
> 若导出为 0 字节：脚本已用 `env -u GZIP gzip -c` 规避 `GZIP` 环境变量冲突；亦可手动
> `docker save langchain-chatchat:offline | env -u GZIP gzip -c > dist/x.tar.gz`。

## 3. 传输
把 `dist/langchain-chatchat-offline.tar.gz` 拷贝到离线运行机（scp / U 盘 / 内网）。

## 4. 离线运行机（导入到运行）
### 4.1 导入镜像
```bash
gunzip -c langchain-chatchat-offline.tar.gz | docker load
# 或：docker load -i langchain-chatchat-offline.tar.gz
# 或（若此机也 clone 了仓库）：./docker/import_image.sh
```
> 说明：离线机**没有代码也没关系** —— 运行所需代码、配置、知识库都已在镜像里；脚本只是方便，手动 `docker load` / `docker run` 即可。

### 4.2 运行
```bash
docker run -d --name chatchat --restart unless-stopped \
  -p 8501:8501 -p 7861:7861 -p 20000:20000 -p 20001:20001 \
  -p 21010:21010 -p 21009:21009 \
  -v "$PWD/data/logs:/app/logs" \
  -e RUN_INIT_DB=0 \
  langchain-chatchat:offline
```
- `RUN_INIT_DB=0`：复用镜像内置向量库（做法 2.4 已预生成）。
- 若未预生成向量库，首次改 `RUN_INIT_DB=1`（现场用 Gitee AI Embedding 生成）。
- 若此机 clone 了仓库，可用 `./docker/run_offline.sh`（默认即上述参数 + `RUN_INIT_DB=0`）。

### 4.3 验证
```bash
docker logs --tail 50 chatchat
# 看到 [OK] startup ready ... 且输出 webui/api 地址 → 成功
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:7861/api/gitee/models
# 返回 200 → API 可用
```
浏览器打开 `http://<离线机IP>:8501` 即可使用。
## 5. 关键环境变量
| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `RUN_INIT_DB` | `0` | `1` = 启动时用 Gitee AI Embedding 重建向量库（需可访问 `ai.gitee.com`） |
| `DATA_DIR` | 工程内 `dist/data` | 日志持久化目录，挂载到 `/app/logs` |
| `WEBUI_PORT` / `API_PORT` 等 | `8501` / `7861` / … | 端口，见 `Dockerfile` 与 `server_config.py` |

## 6. 端口
| 端口 | 服务 |
| --- | --- |
| 8501 | WebUI |
| 7861 | 后端 API（`/api/gitee/*`） |
| 20000 | fastchat openai_api |
| 20001 | fastchat controller |
| 21010 / 21009 | 在线模型 worker（`openai` / `openai-api`） |

## 7. 常见问题
- **api_key 为空 / 鉴权失败**：检查 `configs/model_config.py` 的 `ONLINE_LLM_MODEL["openai"].api_key` 是否已填 Gitee AI 密钥（只填 `.py`，勿提交）。
- **启动报“知识库为空 / 无向量”**：镜像未内置 `vector_store`。首次用 `RUN_INIT_DB=1`，或联网机先 `python init_database.py --recreate-vs` 预生成再 `docker build`。
- **完全离线（连 Gitee AI 都不通）**：本方案不可行（LLM / Embedding 需在线）。
- **tokenizer / nltk 首次下载失败**：预生成向量库那步需联网下载 tokenizer；在联网机完成即可，离线机复用镜像内结果。
- **导出 0 字节**：见 2.6，用 `env -u GZIP`。

## 8. 关闭与清理
```bash
docker stop chatchat; docker rm chatchat                 # 停 + 删容器
docker rmi langchain-chatchat:offline                    # 删镜像
rm -rf data/ dist/langchain-chatchat-offline.tar.gz     # 删本地数据与离线包
```
> 只想“暂停”下次再用：`docker stop chatchat` 即可，不要 `rm` / `rmi`，保留镜像与数据，之后 `docker start chatchat` 或再跑 `./docker/run_offline.sh`。