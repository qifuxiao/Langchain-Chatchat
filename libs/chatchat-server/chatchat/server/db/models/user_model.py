"""
用户管理模块
包括用户模型、认证和API路由
"""

from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import Column, DateTime, Integer, String, Boolean, Text

from chatchat.server.db.base import Base


class UserModel(Base):
    """
    用户模型
    """
    __tablename__ = "users"

    username = Column(String(50), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(100), unique=True, nullable=True, index=True, comment="邮箱")
    phone = Column(String(20), unique=True, nullable=True, index=True, comment="手机号")
    hashed_password = Column(String(255), nullable=False, comment="加密后的密码")
    full_name = Column(String(100), nullable=True, comment="真实姓名")
    
    # 状态
    is_active = Column(Boolean, default=True, comment="是否激活")
    is_superuser = Column(Boolean, default=False, comment="是否超级管理员")
    
    # 权限相关
    role = Column(String(20), default="user", comment="角色: user, admin, guest")
    
    # 限制
    max_knowledge_bases = Column(Integer, default=5, comment="最大知识库数量")
    max_conversations = Column(Integer, default=50, comment="最大对话数量")
    daily_api_calls = Column(Integer, default=1000, comment="每日API调用次数限制")
    
    # OAuth
    oauth_provider = Column(String(20), nullable=True, comment="OAuth提供商: github, google, etc.")
    oauth_id = Column(String(100), nullable=True, comment="OAuth用户ID")
    
    # 头像
    avatar_url = Column(Text, nullable=True, comment="头像URL")
    
    # 最后登录
    last_login = Column(DateTime, nullable=True, comment="最后登录时间")
    
    # 过期时间
    expires_at = Column(DateTime, nullable=True, comment="账户过期时间")

    def __repr__(self):
        return f"<User(id='{self.id}', username='{self.username}', email='{self.email}')>"


# ============== Pydantic Schemas ==============

class UserCreate(BaseModel):
    """创建用户请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    full_name: Optional[str] = None
    role: str = "user"


class UserUpdate(BaseModel):
    """更新用户请求"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    full_name: Optional[str] = None
    max_knowledge_bases: Optional[int] = None
    max_conversations: Optional[int] = None
    daily_api_calls: Optional[int] = None
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None
    role: Optional[str] = None


class UserPasswordChange(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class UserLogin(BaseModel):
    """登录请求"""
    username: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class Token(BaseModel):
    """Token响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒
    refresh_token: Optional[str] = None


class TokenData(BaseModel):
    """Token载荷数据"""
    user_id: int
    username: str
    role: str
    exp: datetime


class UserResponse(BaseModel):
    """用户信息响应"""
    id: int
    username: str
    email: Optional[str]
    phone: Optional[str]
    full_name: Optional[str]
    is_active: bool
    is_superuser: bool
    role: str
    max_knowledge_bases: int
    max_conversations: int
    daily_api_calls: int
    avatar_url: Optional[str]
    last_login: Optional[datetime]
    expires_at: Optional[datetime]
    create_time: datetime

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """用户列表响应"""
    total: int
    users: list[UserResponse]


class UserStats(BaseModel):
    """用户统计信息"""
    total_users: int
    active_users: int
    today_logins: int
    new_users_today: int
