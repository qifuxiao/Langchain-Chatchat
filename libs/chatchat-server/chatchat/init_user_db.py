"""
创建默认管理员用户的脚本
"""

from datetime import datetime

from chatchat.server.db.base import engine, Base
from chatchat.server.db.models import UserModel
from chatchat.server.db.models.auth import get_password_hash
from chatchat.server.db.session import session_scope


def create_tables():
    """创建所有表"""
    Base.metadata.create_all(bind=engine)
    print("数据库表已创建")


def create_default_admin(username: str = "admin", password: str = "admin123"):
    """创建默认管理员用户"""
    with session_scope() as session:
        # 检查是否已存在
        existing = session.query(UserModel).filter(UserModel.username == username).first()
        if existing:
            print(f"用户 {username} 已存在，跳过创建")
            return
        
        admin = UserModel(
            username=username,
            email="admin@example.com",
            hashed_password=get_password_hash(password),
            full_name="系统管理员",
            is_active=True,
            is_superuser=True,
            role="admin",
            max_knowledge_bases=100,
            max_conversations=1000,
            daily_api_calls=10000,
        )
        session.add(admin)
        session.commit()
        print(f"默认管理员用户已创建: {username}/{password}")


if __name__ == "__main__":
    create_tables()
    create_default_admin()
    print("初始化完成!")
