# Langchain-Chatchat 离线 Docker 部署指南（feature/aigitee）

本方案将项目改为 **Docker 部署**：在**可联网**的服务器上构建并导出镜像，拷贝到**完全断网**的服务器上加载并运行。全程不修改任何业务代码，仅新增部署相关文件。

## 一、部署架构

```
┌──────────────────────────── 可联网服务器 ────────────────────────────┐
│  1) docker build          安装全部依赖 + 打入源码/配置/知识库          │
│  2) docker save           导出为 dist/*.tar(.gz) 离线镜像包            │
└──────────────────────────────────────────────────────────────────────┘
                          │  拷贝镜像包（U盘/离线介质）
                          ▼
┌──────────────────────────── 完全断网服务器 ──────────────────────────┐
│  3) docker load           从 tar 包加载镜像（无需联网）                │
│  4) docker run            启动容器，entrypoint 按正确顺序拉服务        │
└──────────────────────────────────────────────────────────────────────┘
```

镜像在构建期先安装 **CPU 版 torch/torchvision**（`torch==2.1.2`，走 PyTorch CPU 源），再安装精简依赖 `requirements_openai.docker.txt`（其余走阿里云镜像源），运行期**不再需要联网安装任何依赖**。相比完整 `requirements_openai.txt`，精简版剔除了 `nvidia-*` CUDA 栈、`vllm`、`xformers`、`triton`、`torchaudio`、`ray`，镜像体积从十余 GB 降到约 1~3 GB。

## 二、端口说明（见 `configs/server_config.py`）

| 服务 | 容器端口 | 说明 |
| --- | --- | --- |
| WebUI | 8501 | Streamlit 前端，浏览器访问 |
| API | 7861 | Chatchat REST API |
| fschat-openai-api | 20000 | FastChat OpenAI 兼容接口 |
| controller | 20001 | FastChat 控制器 |
| model-worker(openai) | 21010 | 在线模型 worker（当前 `LLM_MODELS=["openai"]`）|
| model-worker(openai-api) | 21009 | 备用在线模型 worker |

> 外部访问一般只需 **8501（WebUI）** 与 **7861（API）**；其余为内部端口，脚本一并映射以便排障，可按需裁剪。

## 三、前置条件

- 可联网服务器：已安装 Docker（可拉取基础镜像 `python:3.11-slim`、可访问阿里云 PyPI 与 PyTorch CPU 源 `download.pytorch.org/whl/cpu`；国内慢时可用清华镜像，见“注意事项 2”）。
- 断网服务器：已安装 Docker（**无需**联网、**无需** PyPI）。
- 当前分支为**纯在线模型**配置（LLM/Embedding 均调用 Gitee AI `https://ai.gitee.com/v1`），镜像不含本地模型权重。

## 四、详细步骤

### 阶段 A：可联网服务器

```bash
# A1. 在“测试通过的工程目录”（即含 configs/*.py 与 knowledge_base/ 的目录）下构建镜像
./docker/build_online.sh

# A2. 导出离线镜像包（推荐开启 gzip 压缩，产物在 dist/）
GZIP=1 ./docker/export_image.sh
```

产物：`dist/langchain-chatchat-offline.tar.gz`（或 `.tar`）。

### 阶段 B：拷贝到断网服务器

用 U 盘 / 离线介质将 `dist/langchain-chatchat-offline.tar.gz` 与本仓库（含 `docker/` 脚本）一并拷贝到断网服务器。

### 阶段 C：完全断网服务器

```bash
# C1. 加载镜像
./docker/import_image.sh dist/langchain-chatchat-offline.tar.gz
# 或（若放在默认位置 dist/ 且未压缩）
./docker/import_image.sh

# C2. 启动服务（默认 RUN_INIT_DB=0，复用镜像内置知识库，完全断网可运行）
./docker/run_offline.sh
```

访问：`http://<服务器IP>:8501`（WebUI）、`http://<服务器IP>:7861`（API）。
查看日志：`docker logs -f chatchat`。

## 五、环境变量（`docker/run_offline.sh` / 容器内）

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `RUN_INIT_DB` | `0` | 是否执行 `init_database.py --recreate-vs`。`0`=复用镜像内置知识库（断网可用）；`1`=重建向量库（**需能访问 Embedding API**）|
| `STARTUP_ARGS` | `-a` | 传给 `startup.py` 的参数。`-a`=启动全部服务；可改为 `--all-api`（不带 WebUI）等 |
| `MOUNT_KB` | `0` | `1`=挂载 `$DATA_DIR/knowledge_base` 作为知识库（需自行准备数据）|
| `MODEL_NAME` | 空 | 追加给 `startup.py` 的模型名（`-n`）|
| `CONTAINER_NAME` | `chatchat` | 容器名 |
| `WEBUI_PORT`/`API_PORT`/... | 见端口表 | 宿主机端口映射 |
| `DATA_DIR` | `dist/data` | 日志等持久化数据目录 |
| `IMAGE` | `langchain-chatchat:offline` | 镜像名 |

## 六、与手工步骤的对应关系（顺序已修正）

你原始的手工步骤里 `startup.py -a` 排在 `copy_config_example.py`、`init_database.py` **之前**，在干净环境会失败（`startup.py`/`init_database.py` 都 `import configs`，而 `configs/*.py` 需由 `copy_config_example.py` 生成）。容器内按如下**正确顺序**执行：

| # | 手工步骤 | Docker 中的位置 |
| --- | --- | --- |
| 1 | `python -m venv .venv` / `source` / `pip install -r requirements_openai.txt` | 镜像构建期完成（`Dockerfile`），运行期无需 |
| 2 | `python copy_config_example.py` | entrypoint [1/3]，**仅当 `configs/*.py` 缺失时**执行（保留内置测试配置）|
| 3 | `python init_database.py --recreate-vs` | entrypoint [2/3]，由 `RUN_INIT_DB` 控制 |
| 4 | `python startup.py -a` | entrypoint [3/3]，前台运行（PID 1）|

## 七、注意事项与常见问题

1. **断网与在线 API 的关系**：本分支 LLM/Embedding 都调用 Gitee AI 接口。
   - 若断网服务器**也无法访问** `https://ai.gitee.com/v1`：请将知识库（含向量库）预先准备好并打入镜像或挂载，且设 `RUN_INIT_DB=0`；对话功能仍需该接口可达，否则无法应答。
   - 若“断网”仅指**不能连 PyPI/DockerHub**、但能访问 Gitee AI：可设 `RUN_INIT_DB=1` 以完全复现手工的 `init_database.py --recreate-vs` 步骤。
2. **镜像体积与精简依赖（已做）**：
   - 本部署为**纯在线 API**（LLM/Embedding 均走 Gitee AI），无本地 GPU 推理。但启动链 `server.api -> knowledge_base_chat -> reranker -> sentence_transformers` 会在 import 阶段 `import torch`，因此 **torch 必须保留**；用 **CPU 版**即可满足 import，从而彻底去掉 `nvidia-*` CUDA 大包（约 5~8GB，也是之前构建下载超时的元凶）。
   - `Dockerfile` 用 `requirements_openai.docker.txt`（由 `requirements_openai.txt` 派生，原文件未改动）替代完整清单，剔除 `nvidia-*`、`vllm`、`xformers`、`triton`、`torchaudio`、`ray`；镜像从十余 GB 降到约 1~3 GB，构建更快、且不再下载超大 CUDA wheel 而超时。
    - 编译工具链 `build-essential` 仅在安装依赖时临时使用，装完即在**同一镜像层内** `--purge` 移除，不计入最终体积（进一步压缩镜像）。
   - **前提**：目标机**不用本地 GPU 模型**（纯在线 API）。若将来要在容器内跑本地模型/GPU 推理，请改回完整 `requirements_openai.txt` + CUDA 版 torch。
   - **torch CPU 源**：默认 `https://download.pytorch.org/whl/cpu`；国内慢/不可达时：`TORCH_CPU_INDEX=https://mirrors.tuna.tsinghua.edu.cn/pytorch-wheels/cpu/ ./docker/build_online.sh`。
3. **配置保留**：镜像内置了测试通过的 `configs/*.py`。entrypoint 仅在缺失时才用 `.example` 生成，避免覆盖。请勿在断网端误执行无条件的 `copy_config_example.py`（会还原为默认配置）。
4. **数据持久化**：日志挂载于 `$DATA_DIR/logs`。若需持久化知识库，设 `MOUNT_KB=1` 并准备 `$DATA_DIR/knowledge_base`。
5. **重建/升级**：联网端改代码后重新 `build_online.sh` + `export_image.sh`，断网端重新 `import_image.sh` + `run_offline.sh` 即可（脚本幂等，会替换同名容器）。
