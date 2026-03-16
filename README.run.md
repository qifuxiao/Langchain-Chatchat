# Langchain-Chatchat 项目运行指南

本项目使用 **Poetry** 管理虚拟环境和依赖。

## 环境要求

- Python 3.9 - 3.12
- Poetry (参见下方安装)

## 安装步骤

### 1. 安装 Poetry

```bash
# macOS / Linux
curl -sSL https://install.python-poetry.org | python3 -

# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -
```

### 2. 克隆项目

```bash
git clone git@github.com:qifuxiao/Langchain-Chatchat.git
cd Langchain-Chatchat
```

### 3. 安装依赖

```bash
# 进入 server 目录
cd libs/chatchat-server

# 创建虚拟环境并安装依赖
poetry install

# 激活虚拟环境
poetry env activate
```

### 4. 初始化配置

```bash
# 设置数据目录（可选）
export CHATCHAT_ROOT=/path/to/chatchat_data

# 初始化配置和知识库
poetry run chatchat init
```

### 5. 启动服务

```bash
# 创建默认知识库（首次运行）
poetry run chatchat kb -r

# 启动 WebUI 服务
poetry run chatchat start -a
```

## 常用命令

| 命令 | 说明 |
|------|------|
| `poetry env info` | 查看虚拟环境信息 |
| `poetry env activate` | 激活虚拟环境 |
| `poetry run <command>` | 在虚拟环境中运行命令 |
| `poetry install` | 安装所有依赖 |
| `poetry install --only main` | 仅安装主依赖（不含 dev） |

## 配置说明

配置文件位于 `libs/chatchat-server/` 目录：

- `.env` - API 密钥等环境变量
- `*_settings.yaml` - 模型配置文件

首次运行 `chatchat init` 后会在 `CHATCHAT_ROOT` 目录生成配置文件。

## 故障排查

### 依赖安装失败

```bash
# 清除缓存后重试
poetry cache clear --all
poetry lock
poetry install
```

### Python 版本问题

```bash
# 指定 Python 版本
poetry env use 3.12
```

## 项目结构

```
Langchain-Chatchat/
├── libs/
│   └── chatchat-server/    # 主要服务代码
│       ├── chatchat/       # 核心代码
│       ├── pyproject.toml  # 依赖配置
│       └── .venv/          # Poetry 虚拟环境
├── docs/                   # 文档
└── README.md              # 项目说明
```
