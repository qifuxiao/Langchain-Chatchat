# Docker 提交审查与修复记录

范围：以 `16089572` 为可用业务基线，审查 `e33fe7d3` 的 Docker 实现和
`7f85de50` 的离线部署文档。本次保留原有 OpenAI 对话及 Embedding 请求逻辑。

## 确认的问题

| 级别 | 原位置 | 问题及影响 | 本次处理 |
| --- | --- | --- | --- |
| P1 | e33fe7d3 `docker/run_offline.sh` | 再运行脚本会 `docker rm -f` 同名容器，且默认不持久化知识库；运行期间上传的文档和向量可能丢失。 | 遇到已有容器退出，默认使用独立知识库命名卷。 |
| P1 | e33fe7d3 `docker/entrypoint.sh` | 默认 `RUN_INIT_DB=1`；普通 `docker run` 或重启会重复执行全库向量重建。与 run 脚本默认值不一致。 | 默认 0，只创建缺失的 SQL 表；重建改为显式维护操作。 |
| P1 | e33fe7d3 `Dockerfile` / `.dockerignore` | `COPY . .` 包含真实 `configs/*.py`，还未排除 `.env`；测试配置中的密钥会跟随镜像分发。 | 排除运行配置和 `.env`，构建使用示例，部署时注入环境变量。 |
| P1 | 7f85de50 文档 2.2 | 示例把 `ONLINE_LLM_MODEL` 整体设为只含 `openai`；实际 Embedding 默认别名是 `openai-api`，`server/embeddings_api.py` 直接读取它。照抄会导致向量化失败。 | 同时配置两个别名；允许各自使用不同内网服务及密钥。 |
| P2 | e33fe7d3 配置生成 | 只判断 `model_config.py` 是否存在；其他配置缺失时不补全，反过来又可能调用全量复制脚本覆盖已有配置。 | 新增逐个文件补全逻辑。 |
| P2 | e33fe7d3 依赖表 | 255 行冻结表保留 llama-index 全家桶、本地文档推理、sentence-transformers、spacy 等；虽然删了 CUDA 条目，仍有较大无用依赖。 | requirements 改为 API / FAISS / WebUI / CPU OCR 所需依赖；延迟导入关闭状态的 reranker；CPU torch 用 `+cpu` 版本锁定。 |
| P2 | 7f85de50 文档 2.6 | 未设 `GZIP=1` 却声称输出 `.tar.gz`，后续传输/导入命令找不到该文件。 | 统一压缩导出命令；去掉未实测的固定镜像大小承诺。 |
| P2 | e33fe7d3 脚本及文档 | “预置向量后完全断网可用”表述不正确，查询仍需 Embedding API，对话仍需 LLM API。 | 明确支持无公网但模型服务内网可达的部署。 |
| P2 | 原分词模板，在离线部署中暴露 | 默认 Hugging Face 分词来源没有在线模型对应的本地 tokenizer，尝试加载后异常回退，切块参数也随之改变。 | 示例默认使用字符切分；tiktoken 缓存置于镜像内。 |
| P2 | e33fe7d3 导入/导出脚本 | 带 registry/namespace 的镜像名仅替换冒号，文件名中的斜杠被解释成目录，导出可能失败。 | 导入、导出一致替换冒号和斜杠。 |

## 裁剪边界

移除 CUDA / nvidia-*、vLLM、xformers、triton、torchaudio、torchvision、
sentence-transformers、llama-index、unstructured-inference、spacy 及关联的显式冻结项。
保留 CPU torch、transformers、accelerate，作为 FastChat 默认模型适配器的兼容余量；
FastChat API worker 的自定义会话模板路径不一定需要该适配器，故不声称这些包都不可移除。
[FastChat 0.2.34 上游依赖声明](https://github.com/lm-sys/FastChat/blob/v0.2.34/pyproject.toml)
区分基础依赖和模型 worker 可选依赖。进一步移除 torch 应在实际容器中验证全部启动路径后进行。

原 PDF/图片流程使用 RapidOCR，保留 CPU ONNX 和 OpenCV；未安装 LibreOffice，传统
`.doc` / `.ppt` 仍需自行添加转换工具。当前仓库没有远程 rerank 适配器，按提供的配置
保持关闭；本次没有新增远程 rerank 协议实现。

## 验证与限制

已执行：

- 5 项标准库 unittest：逐项补全配置不覆盖、默认无密钥/本地权重、独立 Embedding 服务、
  Gitee 环境变量兼容、通用变量优先级。
- 修改的 Python/配置模板语法检查、shell 文件 LF 检查、`git diff --check`。
- 从 PyPI 核对直接依赖版本和直接约束，修正 arxiv 2.1.0 / requests 2.32.3 冲突为 arxiv 2.1.3。
  这不是完整的传递依赖解析或安装验证。

已加入、但尚未执行的 Docker 构建检查：`pip check`、确认无 CUDA wheel、API 路由/worker
导入与实例化、分词、NLTK 数据及 CPU OCR 初始化。尚未测试真实模型 API、文档入库和检索。

本机 Docker 客户端存在，但 daemon 管道不存在，无法执行完整镜像构建、容器端到端测试或
镜像体积实测。WSL Bash 同样不可用，尚未执行 shell 运行验证。
部署前请按 `DOCKER_OFFLINE_DEPLOY.md` 构建，并实测对话、文件上传、向量化和知识库检索。
