import os


# 这组配置专门服务于“数据库学习实验室”，不直接影响项目业务库。
DB_HOST = os.getenv("DB_LAB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_LAB_PORT", "5432"))
DB_USER = os.getenv("DB_LAB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_LAB_PASSWORD", "postgres")
ADMIN_DB = os.getenv("DB_LAB_ADMIN_DB", "postgres")
LAB_DB = os.getenv("DB_LAB_NAME", "db_learning_lab")
# PostgreSQL 里的 schema 类似“库中的命名空间/逻辑分组”。
LAB_SCHEMA = "lab"


def admin_database_url() -> str:
    # 连接管理员数据库，用来执行“创建数据库”这类操作。
    return (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{ADMIN_DB}"
    )


def lab_database_url() -> str:
    # 连接我们自己的学习数据库，后续建表和 CRUD 都在这里做。
    return (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{LAB_DB}"
    )
