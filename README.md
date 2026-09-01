![](img/logo-long-chatchat-trans-v2.png)


🌍 [READ THIS IN ENGLISH](README_en.md)

📃 **LangChain-Chatchat** (原 Langchain-ChatGLM)

基于 ChatGLM 等大语言模型与 Langchain 等应用框架实现，开源、可离线部署的检索增强生成(RAG)大模型知识库项目。

---

## 目录

* [介绍](README.md#介绍)
* [解决的痛点](README.md#解决的痛点)
* [Docker 部署](README.md#docker-部署)
* [快速上手](README.md#快速上手)
  * [1. 环境配置](README.md#1-环境配置)
  * [2. 模型下载](README.md#2-模型下载)
  * [3. 初始化知识库和配置文件](README.md#3-初始化知识库和配置文件)
  * [4. 一键启动](README.md#4-一键启动)
  * [5. 启动界面示例](README.md#5-启动界面示例)
* [联系我们](README.md#联系我们)


## 介绍

🤖️ 一种利用 [langchain](https://github.com/hwchase17/langchain) 思想实现的基于本地知识库的问答应用，目标期望建立一套对中文场景与开源模型支持友好、可离线运行的知识库问答解决方案。

💡 受 [GanymedeNil](https://github.com/GanymedeNil) 的项目 [document.ai](https://github.com/GanymedeNil/document.ai) 和 [AlexZhangji](https://github.com/AlexZhangji) 创建的 [ChatGLM-6B Pull Request](https://github.com/THUDM/ChatGLM-6B/pull/216) 启发，建立了全流程可使用开源模型实现的本地知识库问答应用。本项目的最新版本中通过使用 [FastChat](https://github.com/lm-sys/FastChat) 接入 Vicuna, Alpaca, LLaMA, Koala, RWKV 等模型，依托于 [langchain](https://github.com/langchain-ai/langchain) 框架支持通过基于 [FastAPI](https://github.com/tiangolo/fastapi) 提供的 API 调用服务，或使用基于 [Streamlit](https://github.com/streamlit/streamlit) 的 WebUI 进行操作。

✅ 依托于本项目支持的开源 LLM 与 Embedding 模型，本项目可实现全部使用**开源**模型**离线私有部署**。与此同时，本项目也支持 OpenAI GPT API 的调用，并将在后续持续扩充对各类模型及模型 API 的接入。

⛓️ 本项目实现原理如下图所示，过程包括加载文件 -> 读取文本 -> 文本分割 -> 文本向量化 -> 问句向量化 -> 在文本向量中匹配出与问句向量最相似的 `top k`个 -> 匹配出的文本作为上下文和问题一起添加到 `prompt`中 -> 提交给 `LLM`生成回答。

📺 [原理介绍视频](https://www.bilibili.com/video/BV13M4y1e7cN/?share_source=copy_web&vd_source=e6c5aafe684f30fbe41925d61ca6d514)

![实现原理图](img/langchain+chatglm.png)

从文档处理角度来看，实现流程如下：

![实现原理图2](img/langchain+chatglm2.png)

🚩 本项目未涉及微调、训练过程，但可利用微调或训练对本项目效果进行优化。

🌐 [AutoDL 镜像](https://www.codewithgpu.com/i/chatchat-space/Langchain-Chatchat/Langchain-Chatchat) 中 `v11` 版本所使用代码已更新至本项目 `v0.2.7` 版本。

🐳 [Docker 镜像](registry.cn-beijing.aliyuncs.com/chatchat/chatchat:0.2.6) 已经更新到 ```0.2.7``` 版本。

🌲 一行命令运行 Docker ：

```shell
docker run -d --gpus all -p 80:8501 registry.cn-beijing.aliyuncs.com/chatchat/chatchat:0.2.7
```

🧩 本项目有一个非常完整的[Wiki](https://github.com/chatchat-space/Langchain-Chatchat/wiki/) ， README只是一个简单的介绍，__仅仅是入门教程，能够基础运行__。 如果你想要更深入的了解本项目，或者想对本项目做出贡献。请移步 [Wiki](https://github.com/chatchat-space/Langchain-Chatchat/wiki/)  界面

## 解决的痛点

该项目是一个可以实现 __完全本地化__推理的知识库增强方案, 重点解决数据安全保护，私域化部署的企业痛点。
本开源方案采用```Apache License```，可以免费商用，无需付费。

我们支持市面上主流的本地大语言模型和Embedding模型，支持开源的本地向量数据库。
支持列表详见[Wiki](https://github.com/chatchat-space/Langchain-Chatchat/wiki/)


## Docker 部署

本分支（`feature/aigitee`）提供 **Docker 部署**：在**可联网**服务器构建镜像并导出，拷贝到**完全断网**服务器加载运行。镜像基于 `python:3.11-slim`，内置 **CPU 版 torch + 精简依赖 + 源码 + 配置 + 知识库**，纯在线调用 Gitee AI（`https://ai.gitee.com/v1`），**不含本地 GPU 模型**，体积约 **3 GB**（已从十余 GB 精简）。未改动任何业务代码，仅新增下列文件。

### 部署文件清单

| 文件 | 作用 |
| --- | --- |
| `Dockerfile` | 构建镜像（CPU torch + 精简依赖，编译工具随装随删）|
| `.dockerignore` | 排除 `.venv`/`.git`/`dist` 等，减小构建上下文 |
| `requirements_openai.docker.txt` | 精简依赖（剔除 `nvidia-*`/`vllm`/`xformers`/`triton`/`torchaudio`/`ray`）|
| `docker/build_online.sh` | 联网机：构建镜像（可覆盖 torch CPU 源）|
| `docker/export_image.sh` | 联网机：导出为 `dist/*.tar(.gz)` |
| `docker/import_image.sh` | 断网机：`docker load` 加载镜像 |
| `docker/run_offline.sh` | 断网机：`docker run` 启动容器（默认 `RUN_INIT_DB=0`）|
| `docker/entrypoint.sh` | 容器入口（按正确顺序拉服务）|
| `docs/DOCKER_OFFLINE_DEPLOY.md` | 离线部署详细文档 |

### 方式一：离线部署（断网服务器，推荐）

**① 联网服务器：构建 + 导出**
```bash
cd Langchain-Chatchat
./docker/build_online.sh                 # 构建 langchain-chatchat:offline
GZIP=1 ./docker/export_image.sh          # 导出 dist/langchain-chatchat-offline.tar.gz
ls -lh dist/                             # 确认 GB 级、非 0 字节
```
> 国内官方 torch 源慢/超时：`TORCH_CPU_INDEX=https://mirrors.tuna.tsinghua.edu.cn/pytorch-wheels/cpu/ ./docker/build_online.sh`

**② 拷贝**：用 U 盘/离线介质将 `dist/langchain-chatchat-offline.tar.gz` 与仓库（至少 `docker/` 脚本）拷到断网服务器。

**③ 断网服务器：导入 + 运行**
```bash
cd Langchain-Chatchat
./docker/import_image.sh dist/langchain-chatchat-offline.tar.gz   # docker load
./docker/run_offline.sh                                           # docker run（RUN_INIT_DB=0）
docker logs -f chatchat
```

**④ 验证**
```bash
docker ps                                            # STATUS 应为 (healthy)
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:7861/    # 期望 200
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8501/    # 期望 200
```
浏览器访问 `http://<断网机IP>:8501`（WebUI）、`http://<断网机IP>:7861`（API）。

### 方式二：在线构建并直接运行（服务器有网络）

```bash
cd Langchain-Chatchat
./docker/build_online.sh                  # 或 docker build -t langchain-chatchat:offline .
./docker/run_offline.sh                    # 默认 RUN_INIT_DB=0；在线重建向量库用：RUN_INIT_DB=1 ./docker/run_offline.sh
docker logs -f chatchat
```

### 方式三：手动 Docker 命令（不依赖脚本）

```bash
# 构建
docker build -t langchain-chatchat:offline .
# 导出 / 导入（离线）
docker save langchain-chatchat:offline | env -u GZIP gzip -c > chatchat-offline.tar.gz
docker load -i chatchat-offline.tar.gz
# 运行
docker run -d --name chatchat --restart unless-stopped \
  -p 8501:8501 -p 7861:7861 -p 20000:20000 -p 20001:20001 -p 21010:21010 -p 21009:21009 \
  -e RUN_INIT_DB=0 langchain-chatchat:offline
```

### 环境变量（`run_offline.sh` / 容器内）

| 变量 | 默认 | 说明 |
| --- | --- | --- |
| `RUN_INIT_DB` | `0` | `1`=启动时执行 `init_database.py --recreate-vs`（需可访问 Embedding API）；`0`=复用镜像内置知识库（断网可用）|
| `STARTUP_ARGS` | `-a` | 传给 `startup.py`；`-a`=全部服务，`--all-api`=不带 WebUI |
| `MOUNT_KB` | `0` | `1`=挂载 `$DATA_DIR/knowledge_base` 作为知识库 |
| `MODEL_NAME` | 空 | 追加给 `startup.py -n` 的模型名 |
| `IMAGE` | `langchain-chatchat:offline` | 镜像名 |
| `TORCH_CPU_INDEX` | `download.pytorch.org/whl/cpu` | 构建期 CPU torch 源（仅 `build_online.sh`）|
| `GZIP` | `0` | `1`=导出为 `.tar.gz`（仅 `export_image.sh`）|
| `DATA_DIR` | `dist/data` | 日志等持久化目录 |
| `WEBUI_PORT`/`API_PORT`/… | 见端口表 | 宿主机端口映射 |

### 端口（`configs/server_config.py`）

| 服务 | 端口 |
| --- | --- |
| WebUI | 8501 |
| API | 7861 |
| fschat-openai-api | 20000 |
| controller | 20001 |
| model-worker | 21010 / 21009 |

> 外部访问一般只需 **8501**（WebUI）与 **7861**（API）。

### 常见问题（FAQ）

1. **导出 0 字节**：多为 `GZIP` 环境变量与 `gzip` 程序冲突；`docker/export_image.sh` 已用 `env -u GZIP gzip` 规避，直接重跑 `GZIP=1 ./docker/export_image.sh` 即可。
2. **构建在 `pip install torch` 超时**：换清华 CPU 源 `TORCH_CPU_INDEX=https://mirrors.tuna.tsinghua.edu.cn/pytorch-wheels/cpu/`。
3. **为何没有 nvidia/CUDA torch**：纯在线 API 部署无需 GPU；启动链仅需 `import torch`，CPU 版即可满足，故剔除 CUDA 栈以减小镜像。若需在容器内跑本地 GPU 模型，请改回完整 `requirements_openai.txt` + CUDA 版 torch。
4. **配置不被覆盖**：镜像内置测试通过的 `configs/*.py`；`entrypoint.sh` 仅在其缺失时才执行 `copy_config_example.py` 生成。

📄 完整步骤、原理与排障：[docs/DOCKER_OFFLINE_DEPLOY.md](docs/DOCKER_OFFLINE_DEPLOY.md)

## 快速上手

### 1. 环境配置

+ 首先，确保你的机器安装了 Python 3.8 - 3.10
```
$ python --version
Python 3.10.12
```
接着，创建一个虚拟环境，并在虚拟环境内安装项目的依赖
```shell

# 拉取仓库
$ git clone https://github.com/chatchat-space/Langchain-Chatchat.git

# 进入目录
$ cd Langchain-Chatchat

# 安装全部依赖
$ pip install -r requirements.txt 
$ pip install -r requirements_api.txt
$ pip install -r requirements_webui.txt  

# 默认依赖包括基本运行环境（FAISS向量库）。如果要使用 milvus/pg_vector 等向量库，请将 requirements.txt 中相应依赖取消注释再安装。
```
### 2， 模型下载

如需在本地或离线环境下运行本项目，需要首先将项目所需的模型下载至本地，通常开源 LLM 与 Embedding 模型可以从 [HuggingFace](https://huggingface.co/models) 下载。

以本项目中默认使用的 LLM 模型 [THUDM/ChatGLM3-6B](https://huggingface.co/THUDM/chatglm3-6b) 与 Embedding 模型 [BAAI/bge-large-zh](https://huggingface.co/BAAI/bge-large-zh) 为例：

下载模型需要先[安装 Git LFS](https://docs.github.com/zh/repositories/working-with-files/managing-large-files/installing-git-large-file-storage)，然后运行

```Shell
$ git lfs install
$ git clone https://huggingface.co/THUDM/chatglm3-6b
$ git clone https://huggingface.co/BAAI/bge-large-zh
```
### 3. 初始化知识库和配置文件

按照下列方式初始化自己的知识库和简单的复制配置文件
```shell
$ python copy_config_example.py
$ python init_database.py --recreate-vs
 ```
### 4. 一键启动

按照以下命令启动项目
```shell
$ python startup.py -a
```
### 5. 启动界面示例

如果正常启动，你将能看到以下界面

1. FastAPI Docs 界面

![](img/fastapi_docs_026.png)

2. Web UI 启动界面示例：

- Web UI 对话界面：

![img](img/LLM_success.png)

- Web UI 知识库管理页面：

![](img/init_knowledge_base.jpg)


### 注意

以上方式只是为了快速上手，如果需要更多的功能和自定义启动方式 ，请参考[Wiki](https://github.com/chatchat-space/Langchain-Chatchat/wiki/)


---
## 项目里程碑


---
## 联系我们
### Telegram
[![Telegram](https://img.shields.io/badge/Telegram-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white "langchain-chatglm")](https://t.me/+RjliQ3jnJ1YyN2E9)

### 项目交流群
<img src="img/qr_code_82.jpg" alt="二维码" width="300" />

🎉 Langchain-Chatchat 项目微信交流群，如果你也对本项目感兴趣，欢迎加入群聊参与讨论交流。

### 公众号

<img src="img/official_wechat_mp_account.png" alt="二维码" width="300" />

🎉 Langchain-Chatchat 项目官方公众号，欢迎扫码关注。
