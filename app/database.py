from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 定义 SQLite 数据库文件的 URL
# "sqlite:///./novel_settings.db" 表示在项目根目录下创建一个名为 novel_settings.db 的文件
SQLALCHEMY_DATABASE_URL = "sqlite:///./novel_settings.db"

# 创建 SQLAlchemy 引擎
# connect_args 是 SQLite 特有的配置，用于允许多线程访问，这在 FastAPI 中是必需的
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 创建一个数据库会话工厂 (SessionLocal)
# autocommit=False 和 autoflush=False 确保数据只有在显式调用 commit() 时才被写入
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建一个 Declarative Base
# 之后我们的数据库模型类将继承这个 Base 类
Base = declarative_base()

# 数据库依赖函数
def get_db():
    """
    一个 FastAPI 依赖项，用于在每个请求中获取数据库会-话。
    它确保数据库连接在请求处理完毕后被正确关闭。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
