from pathlib import Path
import sys

from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from tutorials.database_lab.config import LAB_SCHEMA, lab_database_url
from tutorials.database_lab.models import Base


def main() -> None:
    engine = create_engine(lab_database_url())

    with engine.begin() as connection:
        # 第一步：创建 schema。它相当于数据库内部的逻辑分组。
        connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{LAB_SCHEMA}"'))
        # 第二步：根据 ORM 模型创建表。
        Base.metadata.create_all(bind=connection)
        print(f"Schema '{LAB_SCHEMA}' is ready.")
        print("Tables created or already present:")
        for table in Base.metadata.sorted_tables:
            print(f"- {table.schema}.{table.name}")

    engine.dispose()


if __name__ == "__main__":
    main()
