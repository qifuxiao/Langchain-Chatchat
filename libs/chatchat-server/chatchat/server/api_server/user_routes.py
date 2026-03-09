"""
用户管理 API 路由
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from chatchat.server.db.base import get_db
from chatchat.server.db.models.user_model import (
    UserModel, UserCreate, UserUpdate, UserLogin, UserPasswordChange,
    Token, UserResponse, UserListResponse, UserStats
)
from chatchat.server.db.models.auth import (
    get_password_hash, verify_password,
    create_access_token, create_refresh_token, decode_token,
    authenticate_user, update_last_login
)

# OAuth2 依赖
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/user/login")

# 路由
user_router = APIRouter(prefix="/api/user", tags=["用户管理"])


def get_current_active_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> UserModel:
    """获取当前活跃用户"""
    from chatchat.server.db.models.auth import get_current_user
    user = get_current_user(db, token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭据",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_admin(user: UserModel = Depends(get_current_active_user)) -> UserModel:
    """要求管理员权限"""
    if user.role != "admin" and not user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return user


# ============== 公开接口 ==============

@user_router.post("/register", response_model=UserResponse, summary="用户注册")
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """用户注册"""
    # 检查用户名是否已存在
    existing_user = db.query(UserModel).filter(
        UserModel.username == user_data.username
    ).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 检查邮箱是否已存在
    if user_data.email:
        existing_email = db.query(UserModel).filter(
            UserModel.email == user_data.email
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被使用"
            )
    
    # 创建用户
    hashed_password = get_password_hash(user_data.password)
    new_user = UserModel(
        username=user_data.username,
        email=user_data.email,
        phone=user_data.phone,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=True,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user


@user_router.post("/login", response_model=Token, summary="用户登录")
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """用户登录（用户名密码）"""
    user = authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 生成token
    access_token, expires = create_access_token(
        user_id=user.id,
        username=user.username,
        role=user.role
    )
    refresh_token = create_refresh_token(user.id)
    
    # 更新最后登录时间
    update_last_login(db, user)
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=int((expires - datetime.utcnow()).total_seconds()),
        refresh_token=refresh_token
    )


@user_router.post("/login/oauth", response_model=Token, summary="OAuth登录")
def oauth_login(
    provider: str = Body(..., description="OAuth提供商: github, google"),
    code: str = Body(..., description="OAuth授权码"),
    db: Session = Depends(get_db)
):
    """OAuth第三方登录（需实现具体的OAuth逻辑）"""
    # TODO: 实现具体的OAuth登录逻辑
    # 1. 用code换取access_token
    # 2. 获取用户信息
    # 3. 查找或创建用户
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="OAuth登录尚未实现"
    )


@user_router.post("/refresh", response_model=Token, summary="刷新Token")
def refresh_token(refresh_token: str = Body(..., description="刷新令牌"), db: Session = Depends(get_db)):
    """刷新访问令牌"""
    try:
        from jwt import decode
        from chatchat.server.db.models.auth import JWT_SECRET_KEY, JWT_ALGORITHM
        
        payload = decode(refresh_token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("user_id")
        
        if payload.get("type") != "refresh" or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的刷新令牌"
            )
        
        user = db.query(UserModel).filter(UserModel.id == user_id).first()
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户不存在或已禁用"
            )
        
        # 生成新token
        access_token, expires = create_access_token(
            user_id=user.id,
            username=user.username,
            role=user.role
        )
        new_refresh_token = create_refresh_token(user.id)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=int((expires - datetime.utcnow()).total_seconds()),
            refresh_token=new_refresh_token
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的刷新令牌"
        )


# ============== 需要认证的接口 ==============

@user_router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
def get_current_user_info(current_user: UserModel = Depends(get_current_active_user)):
    """获取当前登录用户信息"""
    return current_user


@user_router.put("/me", response_model=UserResponse, summary="更新当前用户信息")
def update_current_user(
    user_data: UserUpdate,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息（部分字段）"""
    if user_data.email is not None:
        # 检查邮箱是否被其他用户使用
        existing = db.query(UserModel).filter(
            UserModel.email == user_data.email,
            UserModel.id != current_user.id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被其他用户使用"
            )
        current_user.email = user_data.email
    
    if user_data.phone is not None:
        current_user.phone = user_data.phone
    
    if user_data.full_name is not None:
        current_user.full_name = user_data.full_name
    
    if user_data.avatar_url is not None:
        current_user.avatar_url = user_data.avatar_url
    
    db.commit()
    db.refresh(current_user)
    return current_user


@user_router.post("/me/password", summary="修改密码")
def change_password(
    password_data: UserPasswordChange,
    current_user: UserModel = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """修改当前用户密码"""
    if not verify_password(password_data.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="旧密码错误"
        )
    
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "密码修改成功"}


@user_router.post("/logout", summary="登出")
def logout(current_user: UserModel = Depends(get_current_active_user)):
    """用户登出（客户端删除token即可）"""
    return {"message": "登出成功"}


# ============== 管理员接口 ==============

@user_router.get("/list", response_model=UserListResponse, summary="获取用户列表")
def get_user_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    username: Optional[str] = Query(None, description="用户名搜索"),
    role: Optional[str] = Query(None, description="角色筛选"),
    is_active: Optional[bool] = Query(None, description="激活状态筛选"),
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取用户列表（管理员）"""
    query = db.query(UserModel)
    
    if username:
        query = query.filter(UserModel.username.like(f"%{username}%"))
    if role:
        query = query.filter(UserModel.role == role)
    if is_active is not None:
        query = query.filter(UserModel.is_active == is_active)
    
    total = query.count()
    users = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return UserListResponse(total=total, users=users)


@user_router.get("/stats", response_model=UserStats, summary="获取用户统计")
def get_user_stats(current_user: UserModel = Depends(require_admin), db: Session = Depends(get_db)):
    """获取用户统计信息（管理员）"""
    from datetime import datetime, timedelta
    
    total_users = db.query(UserModel).count()
    active_users = db.query(UserModel).filter(UserModel.is_active == True).count()
    
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_logins = db.query(UserModel).filter(
        UserModel.last_login >= today
    ).count()
    
    new_users_today = db.query(UserModel).filter(
        UserModel.create_time >= today
    ).count()
    
    return UserStats(
        total_users=total_users,
        active_users=active_users,
        today_logins=today_logins,
        new_users_today=new_users_today
    )


@user_router.get("/{user_id}", response_model=UserResponse, summary="获取指定用户信息")
def get_user(
    user_id: int,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取指定用户信息（管理员）"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    return user


@user_router.post("/", response_model=UserResponse, summary="创建用户")
def create_user(
    user_data: UserCreate,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """创建用户（管理员）"""
    # 检查用户名
    existing = db.query(UserModel).filter(
        UserModel.username == user_data.username
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    new_user = UserModel(
        username=user_data.username,
        email=user_data.email,
        phone=user_data.phone,
        hashed_password=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@user_router.put("/{user_id}", response_model=UserResponse, summary="更新用户")
def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """更新用户（管理员）"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 不能修改超级管理员（除非自己）
    if user.is_superuser and user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能修改超级管理员"
        )
    
    update_data = user_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user


@user_router.delete("/{user_id}", summary="删除用户")
def delete_user(
    user_id: int,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """删除用户（管理员）"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 不能删除自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )
    
    # 不能删除超级管理员
    if user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能删除超级管理员"
        )
    
    db.delete(user)
    db.commit()
    
    return {"message": "用户删除成功"}


@user_router.post("/{user_id}/reset-password", summary="重置密码")
def reset_password(
    user_id: int,
    new_password: str = Body(..., min_length=6),
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """重置用户密码（管理员）"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    
    return {"message": "密码重置成功"}


@user_router.post("/{user_id}/toggle-active", response_model=UserResponse, summary="启用/禁用用户")
def toggle_user_active(
    user_id: int,
    current_user: UserModel = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """启用/禁用用户（管理员）"""
    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 不能禁用自己
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用自己"
        )
    
    # 不能禁用超级管理员
    if user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="不能禁用超级管理员"
        )
    
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)
    
    return user
