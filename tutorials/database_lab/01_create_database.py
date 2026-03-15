from pathlib import Path
import sys

from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from tutorials.database_lab.config import LAB_DB, admin_database_url


def main() -> None:
    # AUTOCOMMIT 很适合 CREATE DATABASE 这类数据库级操作。
    engine = create_engine(admin_database_url(), isolation_level="AUTOCOMMIT")

    with engine.connect() as connection:
        # 先查询目标数据库是否已存在，避免重复创建报错。
        exists = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
            {"db_name": LAB_DB},
        ).scalar()

        if exists:
            print(f"Database '{LAB_DB}' already exists.")
        else:
            # PostgreSQL 里必须先有数据库，后面才能在这个库里建 schema 和表。
            connection.execute(text(f'CREATE DATABASE "{LAB_DB}"'))
            print(f"Created database '{LAB_DB}'.")

    engine.dispose()


if __name__ == "__main__":
    main()
