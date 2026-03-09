# 用户管理功能

本模块为 Langchain-Chatchat 项目添加了完整的用户管理功能，包括用户注册、登录、权限管理等。

## 功能列表

### 公开接口
- **用户注册** `POST /api/user/register` - 新用户注册
- **用户登录** `POST /api/user/login` - 用户登录获取 Token
- **刷新 Token** `POST /api/user/refresh` - 刷新访问令牌
- **OAuth 登录** `POST /api/user/login/oauth` - 第三方 OAuth 登录（开发中）

### 需要认证的接口
- **获取当前用户** `GET /api/user/me` - 获取当前登录用户信息
- **更新当前用户** `PUT /api/user/me` - 更新当前用户信息
- **修改密码** `POST /api/user/me/password` - 修改当前用户密码
- **登出** `POST /api/user/logout` - 用户登出

### 管理员接口
- **获取用户列表** `GET /api/user/list` - 获取所有用户列表
- **获取用户统计** `GET /api/user/stats` - 获取用户统计信息
- **获取指定用户** `GET /api/user/{user_id}` - 获取指定用户信息
- **创建用户** `POST /api/user/` - 管理员创建用户
- **更新用户** `PUT /api/user/{user_id}` - 管理员更新用户
- **删除用户** `DELETE /api/user/{user_id}` - 管理员删除用户
- **重置密码** `POST /api/user/{user_id}/reset-password` - 管理员重置用户密码
- **启用/禁用用户** `POST /api/user/{user_id}/toggle-active` - 管理员启用或禁用用户

## 使用方法

### 1. 安装依赖

确保已安装 `passlib` 依赖：

```bash
pip install passlib[bcrypt]
```

### 2. 初始化数据库

运行初始化脚本创建用户表和默认管理员：

```bash
cd libs/chatchat-server
python -c "from chatchat.init_user_db import create_tables, create_default_admin; create_tables(); create_default_admin()"
```

默认管理员账户：
- 用户名：`admin`
- 密码：`admin123`

### 3. 启动服务

```bash
chatchat start -a
```

### 4. API 使用示例

#### 注册新用户

```bash
curl -X POST "http://localhost:7861/api/user/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "test123456",
    "full_name": "测试用户"
  }'
```

#### 登录

```bash
curl -X POST "http://localhost:7861/api/user/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test123456"
  }'
```

响应：
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400,
  "refresh_token": "eyJ..."
}
```

#### 获取当前用户信息

```bash
curl -X GET "http://localhost:7861/api/user/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 用户权限

系统支持以下角色：

| 角色 | 说明 |
|------|------|
| `user` | 普通用户，默认角色 |
| `admin` | 管理员，可以管理其他用户 |
| `guest` | 访客，受限功能 |

用户属性说明：
- `max_knowledge_bases`: 最大知识库数量
- `max_conversations`: 最大对话数量
- `daily_api_calls`: 每日 API 调用次数限制
- `expires_at`: 账户过期时间

## JWT 配置

可以通过环境变量配置 JWT：

```bash
export JWT_SECRET_KEY="your-secret-key-change-in-production"
```

- `JWT_SECRET_KEY`: JWT 密钥，默认值为 "your-secret-key-change-in-production"，**生产环境请修改**
- Token 有效期：24 小时
- 刷新 Token 有效期：30 天

## 数据库表

用户表 `users` 包含以下字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| username | String | 用户名（唯一） |
| email | String | 邮箱（唯一，可选） |
| phone | String | 手机号（唯一，可选） |
| hashed_password | String | 加密后的密码 |
| full_name | String | 真实姓名 |
| is_active | Boolean | 是否激活 |
| is_superuser | Boolean | 是否超级管理员 |
| role | String | 角色 |
| max_knowledge_bases | Integer | 最大知识库数量 |
| max_conversations | Integer | 最大对话数量 |
| daily_api_calls | Integer | 每日 API 调用次数限制 |
| oauth_provider | String | OAuth 提供商 |
| oauth_id | String | OAuth 用户 ID |
| avatar_url | String | 头像 URL |
| last_login | DateTime | 最后登录时间 |
| expires_at | DateTime | 账户过期时间 |
| create_time | DateTime | 创建时间 |
| update_time | DateTime | 更新时间 |

## 扩展知识库权限控制

用户登录后，知识库操作可以根据用户权限进行限制。在后续扩展中，可以：

1. 将知识库与用户关联（添加 `user_id` 字段）
2. 在查询知识库时过滤当前用户的数据
3. 实现用户级别的 API 调用限制

## 文件结构

```
chatchat/server/
├── db/
│   └── models/
│       ├── user_model.py    # 用户模型和 Schema
│       └── auth.py          # 认证相关功能
├── api_server/
│   └── user_routes.py       # 用户管理 API 路由
└── init_user_db.py          # 数据库初始化脚本
```

## 安全建议

1. **修改默认 JWT 密钥**：在生产环境中务必修改 `JWT_SECRET_KEY`
2. **使用 HTTPS**：生产环境应使用 HTTPS
3. **密码强度**：建议强制要求密码强度
4. **定期更新依赖**：保持 passlib 等安全相关依赖更新
5. **日志审计**：建议添加登录日志审计
