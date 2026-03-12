# Langchain-Chatchat (Gitee AI 版本)

基于 [Langchain-Chatchat](https://github.com/chatchat-space/Langchain-Chatchat) 的二次开发，支持 **ai.gitee.com** 的大模型和 Embedding 模型。

## 功能特性

- 🤖 支持 ai.gitee.com 提供的所有 LLM 模型
- 📚 支持知识库问答 (RAG)
- 💬 支持多种对话模式
- 🔧 支持 Agent 工具
- 🎨 支持 WebUI 界面

## 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/qifuxiao/Langchain-Chatchat.git
cd Langchain-Chatchat
```

### 2. 配置环境变量

```bash
# 复制配置模板
cp libs/chatchat-server/.env.example libs/chatchat-server/.env

# 编辑 .env 文件，填入你的 Gitee AI API Key
vim libs/chatchat-server/.env
```

`.env` 文件内容：

```bash
# Gitee AI 配置
GITEE_BASE_URL=https://ai.gitee.com/v1
GITEE_API_KEY=你的API密钥
GITEE_LLM_MODELS=Qwen2-72B-Instruct,Qwen2-7B-Instruct,GLM-4-Flash
GITEE_EMBED_MODELS=embedding-2

# 默认模型
DEFAULT_LLM_MODEL=Qwen2-72B-Instruct
DEFAULT_EMBEDDING_MODEL=embedding-2
```

### 3. 获取 API Key

1. 访问 [ai.gitee.com](https://ai.gitee.com/)
2. 注册/登录账号
3. 在个人中心获取 API Key

### 4. 安装依赖

```bash
cd libs/chatchat-server
pip install -r requirements.txt
```

或使用 Poetry：

```bash
cd libs/chatchat-server
poetry install
```

### 5. 初始化项目

```bash
# 初始化配置
chatchat init -x http://127.0.0.1:9997/v1 -l Qwen2-72B-Instruct -e embedding-2

# 或手动初始化知识库
chatchat kb -r
```

### 6. 启动服务

```bash
# 启动所有服务 (API + WebUI)
chatchat start -a

# 或只启动 API 服务
chatchat start
```

服务启动后：
- API: http://localhost:7861
- WebUI: http://localhost:8501

## 配置说明

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `GITEE_BASE_URL` | Gitee AI API 地址 | https://ai.gitee.com/v1 |
| `GITEE_API_KEY` | Gitee AI API Key | (必填) |
| `GITEE_LLM_MODELS` | 可用的 LLM 模型列表 | Qwen2-72B-Instruct,... |
| `GITEE_EMBED_MODELS` | 可用的 Embedding 模型列表 | embedding-2 |
| `DEFAULT_LLM_MODEL` | 默认使用的 LLM 模型 | Qwen2-72B-Instruct |
| `DEFAULT_EMBEDDING_MODEL` | 默认使用的 Embedding 模型 | embedding-2 |

## 可用模型 (参考)

### LLM 模型
- Qwen2-72B-Instruct
- Qwen2-7B-Instruct
- GLM-4-Flash
- GLM-4V-Flash

### Embedding 模型
- embedding-2

## 目录结构

```
Langchain-Chatchat/
├── libs/
│   └── chatchat-server/     # 主服务代码
│       ├── chatchat/        # 核心代码
│       ├── .env             # 环境配置
│       └── requirements.txt # Python 依赖
├── frontend/                # WebUI 前端
├── docker/                  # Docker 配置
└── docs/                    # 文档
```

## 常见问题

### 1. 模型无法加载
确保 `GITEE_API_KEY` 正确配置，并且模型名称在支持列表中。

### 2. 知识库无法创建
确保 `DEFAULT_EMBEDDING_MODEL` 可用，并且已运行 `chatchat kb -r` 初始化知识库。

### 3. API 调用超时
可以修改 `.env` 中的 `HTTPX_DEFAULT_TIMEOUT` 参数增大超时时间。

## 原始项目

本项目基于 [Langchain-Chatchat](https://github.com/chatchat-space/Langchain-Chatchat) 开发，保留了所有原版功能。

## License

MIT
