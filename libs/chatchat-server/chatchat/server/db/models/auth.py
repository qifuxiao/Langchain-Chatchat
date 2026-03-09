"""
用户认证模块
提供JWT token生成、验证和密码哈希功能
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from chatchat.server.db.models.user_model import UserModel, TokenData

# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT配置
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24小时
REFRESH_TOKEN_EXPIRE_DAYS = 30


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


def create_access_token(user_id: int, username: str, role: str, expires_delta: Optional[timedelta] = None) -> tuple[str, datetime]:
    """创建访问令牌"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = TokenData(
        user_id=user_id,
        username=username,
        role=role,
        exp=expire
    )
    
    encoded_jwt = jwt.encode(
        to_encode.model_dump(), 
        JWT_SECRET_KEY, 
        algorithm=JWT_ALGORITHM
    )
    return encoded_jwt, expire


def create_refresh_token(user_id: int) -> str:
    """创建刷新令牌"""
    to_encode = {
        "user_id": user_id,
        "type": "refresh",
        "rand": secrets.token_hex(16)
    }
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode["exp"] = expire
    
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[TokenData]:
    """解码令牌"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return TokenData(**payload)
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user(db: Session, token: str) -> Optional[UserModel]:
    """从令牌获取当前用户"""
    token_data = decode_token(token)
    if not token_data:
        return None
    
    user = db.query(UserModel).filter(UserModel.id == token_data.user_id).first()
    if not user or not user.is_active:
        return None
    
    # 检查账户是否过期
    if user.expires_at and user.expires_at < datetime.utcnow():
        return None
    
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[UserModel]:
    """验证用户登录"""
    # 支持用户名或邮箱登录
    user = db.query(UserModel).filter(
        (UserModel.username == username) | (UserModel.email == username)
    ).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    # 检查账户是否过期
    if user.expires_at and user.expires_at < datetime.utcnow():
        return None
    
    if not user.is_active:
        return None
    
    return user


def update_last_login(db: Session, user: UserModel):
    """更新最后登录时间"""
    user.last_login = datetime.utcnow()
    db.commit()


def generate_api_key() -> str:
    """生成API密钥"""
    return f"sk-{secrets.token_urlsafe(32)}"


def verify_api_key(db: Session, api_key: str) -> Optional[UserModel]:
    """验证API密钥"""
    # 简单实现：API key 存储在用户表的特定字段
    # 可以扩展为单独的 API key 表
    if not api_key.startswith("sk-"):
        return None
    
    # 这里可以查询 API key 表，目前简化处理
    return None
